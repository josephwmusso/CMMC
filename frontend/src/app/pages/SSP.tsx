import { Search, Download, Sparkles, Loader2, FileText } from 'lucide-react';
import { useState, useEffect, useRef, useCallback } from 'react';
import { useSearchParams } from 'react-router';
import { getComplianceOverview, getGaps, getEvidenceByControl, getSSPNarrative, exportSSPAsPdf, exportSSPAsDocx, generateFullSSP, getSSPJobStatus } from '../api/client';
import { controlFamilies } from '../data/nist-controls';
import { toast } from 'sonner';

type ControlData = {
  control_id: string;
  title: string;
  family: string;
  implementation_status: string;
  points?: number;
};

export function SSP() {
  const [searchParams] = useSearchParams();
  const [loading, setLoading] = useState(true);
  const [controls, setControls] = useState<ControlData[]>([]);
  const [gapDetails, setGapDetails] = useState<any[]>([]);
  const [selectedFamily, setSelectedFamily] = useState('AC');
  const [selectedControl, setSelectedControl] = useState<ControlData | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [narrative, setNarrative] = useState('');
  const [narrativeLoading, setNarrativeLoading] = useState(false);
  const [evidence, setEvidence] = useState<any[]>([]);
  const [evidenceLoading, setEvidenceLoading] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [exportingDocx, setExportingDocx] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [jobId, setJobId] = useState<string | null>(null);
  const [jobProgress, setJobProgress] = useState('');
  const [jobDone, setJobDone] = useState(0);
  const [jobTotal, setJobTotal] = useState(0);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const stopPolling = useCallback(() => {
    if (pollRef.current) { clearInterval(pollRef.current); pollRef.current = null; }
  }, []);

  useEffect(() => () => stopPolling(), [stopPolling]);

  const startPolling = useCallback((jid: string) => {
    stopPolling();
    pollRef.current = setInterval(async () => {
      try {
        const s = await getSSPJobStatus(jid);
        setJobProgress(s.progress || '');
        setJobDone(s.controls_done || 0);
        setJobTotal(s.controls_total || 110);
        if (s.status === 'completed') {
          stopPolling();
          setGenerating(false);
          setJobId(null);
          toast.success('SSP generation complete! Reloading...');
          const [ov, gaps] = await Promise.all([getComplianceOverview(), getGaps()]);
          setControls(ov.sprs?.details || []);
          setGapDetails(gaps.gap_details || []);
        } else if (s.status === 'failed') {
          stopPolling();
          setGenerating(false);
          setJobId(null);
          toast.error(`SSP generation failed: ${s.error || 'Unknown error'}`);
        }
      } catch {}
    }, 5000);
  }, [stopPolling]);

  useEffect(() => {
    async function load() {
      try {
        const [ov, gaps] = await Promise.all([getComplianceOverview(), getGaps()]);
        const details = ov.sprs?.details || [];
        setControls(details);
        setGapDetails(gaps.gap_details || []);
        const deepLink = searchParams.get('control');
        if (deepLink) {
          const ctrl = details.find((c: any) => c.control_id === deepLink);
          if (ctrl) { setSelectedFamily(ctrl.family || 'AC'); setSelectedControl(ctrl); }
        } else if (details.length > 0) { setSelectedControl(details[0]); }
      } catch (e) { console.error('SSP load failed:', e); }
      finally { setLoading(false); }
    }
    load();
  }, []);

  useEffect(() => {
    if (!selectedControl) return;
    setNarrativeLoading(true); setEvidenceLoading(true);
    setNarrative(''); setEvidence([]);
    getSSPNarrative(selectedControl.control_id).then(d => setNarrative(d.narrative || '')).catch(() => setNarrative('')).finally(() => setNarrativeLoading(false));
    getEvidenceByControl(selectedControl.control_id).then(d => setEvidence(d.artifacts || [])).catch(() => setEvidence([])).finally(() => setEvidenceLoading(false));
  }, [selectedControl?.control_id]);

  const handleExportPdf = async () => {
    setExporting(true);
    try { await exportSSPAsPdf(); toast.success('SSP exported as PDF'); }
    catch (e: any) { toast.error(e.message); } finally { setExporting(false); }
  };

  const handleExportDocx = async () => {
    setExportingDocx(true);
    try { await exportSSPAsDocx(); toast.success('SSP exported as DOCX'); }
    catch (e: any) { toast.error(e.message); } finally { setExportingDocx(false); }
  };

  const handleGenerate = async () => {
    setGenerating(true);
    try {
      const job = await generateFullSSP();
      setJobId(job.job_id);
      setJobDone(0);
      setJobTotal(job.controls_total || 110);
      toast.success(`SSP generation started (job ${job.job_id})`);
      startPolling(job.job_id);
    } catch (e: any) { toast.error(e.message); setGenerating(false); }
  };

  const getControlsByFamily = (familyId: string) => controls.filter(c => (c.family || c.control_id.split('.')[0]) === familyId);

  const filteredControls = controls.filter(c => {
    const f = c.family || c.control_id.split('.')[0];
    if (selectedFamily && f !== selectedFamily) return false;
    if (searchQuery) { const q = searchQuery.toLowerCase(); return c.control_id.toLowerCase().includes(q) || c.title.toLowerCase().includes(q); }
    return true;
  });

  const controlGaps = selectedControl ? gapDetails.filter(g => g.control_id === selectedControl.control_id) : [];
  if (loading) return <div className="flex items-center justify-center h-[60vh]"><Loader2 className="w-6 h-6 text-zinc-500 animate-spin" /></div>;

  const implemented = controls.filter(c => c.implementation_status === 'Implemented').length;
  const selectedFamilyData = controlFamilies.find(f => f.id === selectedFamily);

  return (
    <div className="flex h-[calc(100vh-56px)] bg-black">
      <aside className="w-64 border-r border-zinc-800 flex flex-col bg-zinc-900/20">
        <div className="p-6">
          <h2 className="text-sm font-medium text-zinc-400 uppercase tracking-wider mb-6">System Security Plan</h2>
          <div className="mb-6 p-4 bg-zinc-900/50 border border-zinc-800 rounded-lg">
            <div className="text-xs text-zinc-500 uppercase tracking-wider mb-3">Overall Compliance</div>
            <div className="text-2xl font-medium text-zinc-100">{implemented}<span className="text-sm text-zinc-600 ml-1">/ {controls.length || 110}</span></div>
            <div className="h-1.5 bg-zinc-800 rounded-full overflow-hidden">
              <div className="h-full bg-blue-400/80 rounded-full" style={{ width: `${controls.length > 0 ? (implemented / controls.length) * 100 : 0}%` }} />
            </div>
          </div>
          <button onClick={handleExportPdf} disabled={exporting} className="w-full px-4 py-2.5 bg-blue-400/80 hover:bg-blue-400 disabled:opacity-50 rounded-lg text-sm font-medium text-white flex items-center justify-center gap-2 mb-2">
            {exporting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Download className="w-4 h-4" />} Export PDF
          </button>
          <button onClick={handleExportDocx} disabled={exportingDocx} className="w-full px-4 py-2.5 bg-zinc-800 hover:bg-zinc-700 border border-zinc-700 disabled:opacity-50 rounded-lg text-sm font-medium text-zinc-300 flex items-center justify-center gap-2 mb-2">
            {exportingDocx ? <Loader2 className="w-4 h-4 animate-spin" /> : <Download className="w-4 h-4" />} Export DOCX
          </button>
          <button
            onClick={handleGenerate}
            disabled={generating}
            className="w-full rounded-xl px-4 py-2.5 text-sm font-medium transition-all hover:scale-[1.01] active:scale-[0.99] flex items-center justify-center gap-2 border disabled:opacity-50"
            style={{
              background: 'rgba(255,255,255,0.06)',
              backdropFilter: 'blur(12px)',
              WebkitBackdropFilter: 'blur(12px)',
              borderColor: 'rgba(255,255,255,0.12)',
              color: 'rgba(255,255,255,0.9)',
              boxShadow: '0 1px 3px rgba(0,0,0,0.2), inset 0 1px 0 rgba(255,255,255,0.08)',
            }}
          >
            {generating ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4 opacity-70" />}
            {generating ? 'Generating...' : 'AI Generate All'}
            <span className="px-1.5 py-0.5 bg-white/10 border border-white/10 rounded text-[9px] font-bold uppercase tracking-wider ml-1 opacity-70">AI</span>
          </button>
          {generating && jobId && (
            <div className="mt-3">
              <div className="h-1.5 bg-zinc-800 rounded-full overflow-hidden">
                <div className="h-full bg-blue-500 rounded-full transition-all" style={{ width: `${jobTotal > 0 ? (jobDone / jobTotal) * 100 : 0}%` }} />
              </div>
              <div className="text-xs text-zinc-500 mt-1">{jobProgress || `${jobDone}/${jobTotal}`}</div>
            </div>
          )}
        </div>
        <div className="h-px bg-zinc-800 mx-6 mb-4" />
        <div className="flex-1 overflow-y-auto px-6 pb-6">
          <div className="text-xs text-zinc-500 uppercase tracking-wider mb-3">Control Families</div>
          <div className="space-y-1">{controlFamilies.map(family => {
            const fc = getControlsByFamily(family.id);
            const implCount = fc.filter(c => c.implementation_status === 'Implemented').length;
            return (
              <button key={family.id} onClick={() => { setSelectedFamily(family.id); const first = getControlsByFamily(family.id)[0]; if (first) setSelectedControl(first); }}
                className={`w-full text-left px-3 py-2.5 rounded-lg transition-colors ${selectedFamily === family.id ? 'bg-zinc-800 text-zinc-100 border border-zinc-700' : 'text-zinc-500 hover:text-zinc-400 hover:bg-zinc-900/50'}`}>
                <div className="flex items-center gap-2 mb-1.5">
                  <span className="text-xs font-mono text-zinc-500">{family.id}</span>
                  <span className="text-xs text-zinc-700">{implCount}/{fc.length || family.controlCount}</span>
                </div>
                <div className="text-sm">{family.name}</div>
                <div className="h-1 bg-zinc-800 rounded-full overflow-hidden mt-1">
                  <div className="h-full bg-blue-400/80 rounded-full" style={{ width: `${fc.length > 0 ? (implCount / fc.length) * 100 : 0}%` }} />
                </div>
              </button>
            );
          })}</div>
        </div>
      </aside>

      <div className="w-80 border-r border-zinc-800 flex flex-col bg-zinc-950">
        <div className="p-4 border-b border-zinc-800">
          <div className="mb-3">
            <div className="text-xs font-medium text-zinc-500 mb-1">{selectedFamilyData?.name}</div>
            <div className="text-xs text-zinc-600">{selectedFamilyData?.description}</div>
          </div>
          <div className="relative">
            <Search className="w-4 h-4 absolute left-3 top-2.5 text-zinc-600" />
            <input type="text" placeholder="Search controls..." value={searchQuery} onChange={e => setSearchQuery(e.target.value)}
              className="w-full pl-9 pr-3 py-2 bg-black border border-zinc-800 rounded text-sm text-zinc-300 placeholder:text-zinc-700 focus:outline-none focus:border-zinc-700" />
          </div>
        </div>
        <div className="flex-1 overflow-y-auto p-2">
          {filteredControls.map(control => (
            <button key={control.control_id} onClick={() => setSelectedControl(control)}
              className={`w-full text-left px-3 py-2.5 rounded mb-1 transition-colors ${selectedControl?.control_id === control.control_id ? 'bg-zinc-900 text-zinc-100' : 'text-zinc-500 hover:bg-zinc-900/50 hover:text-zinc-300'}`}>
              <div className="text-xs font-mono text-zinc-600 mb-1">{control.control_id}</div>
              <div className="text-sm">{control.title}</div>
              <span className={`text-xs px-1.5 py-0.5 rounded mt-1 inline-block ${
                control.implementation_status === 'Implemented' ? 'bg-emerald-500/10 text-emerald-400/80' :
                control.implementation_status === 'Partially Implemented' ? 'bg-blue-500/10 text-blue-400/80' :
                'bg-red-500/10 text-red-400/80'
              }`}>{control.implementation_status}</span>
            </button>
          ))}
        </div>
      </div>

      <div className="flex-1 overflow-y-auto">
        {selectedControl ? (
          <div className="w-full p-8">
            <div className="mb-8">
              <div className="text-xs font-mono text-zinc-600 mb-2">{selectedControl.control_id}</div>
              <h1 className="text-2xl font-medium text-zinc-100 mb-2">{selectedControl.title}</h1>
              <div className="flex items-center gap-4 text-sm text-zinc-500">
                <span>{selectedControl.family}</span><span>-</span><span>{selectedControl.points ?? '?'} points</span>
              </div>
            </div>

            <div className="flex items-center justify-between mb-8 pb-6 border-b border-zinc-800">
              <div><div className="text-xs text-zinc-600 mb-2">Status</div><div className="text-sm text-zinc-300">{selectedControl.implementation_status}</div></div>
            </div>

            <div className="mb-8">
              <h3 className="text-sm text-zinc-500 mb-3">Implementation Narrative</h3>
              {narrativeLoading ? <div className="flex items-center gap-2 text-zinc-500"><Loader2 className="w-4 h-4 animate-spin" /> Loading...</div>
                : narrative ? <p className="text-zinc-300 leading-relaxed whitespace-pre-wrap">{narrative}</p>
                : <p className="text-zinc-600 text-sm italic">No narrative generated yet.</p>}
            </div>

            <div className="mb-8">
              <h3 className="text-sm text-zinc-500 mb-3">Supporting Evidence ({evidence.length})</h3>
              {evidenceLoading ? <div className="flex items-center gap-2 text-zinc-500"><Loader2 className="w-4 h-4 animate-spin" /> Loading...</div>
                : evidence.length === 0 ? <p className="text-zinc-600 text-sm">No evidence linked</p>
                : <div className="space-y-2">{evidence.map((ev: any) => (
                  <div key={ev.id} className="flex items-center gap-3 text-sm text-zinc-400 p-2 rounded bg-zinc-900/30">
                    <FileText className="w-4 h-4 flex-shrink-0" /><span className="flex-1">{ev.filename}</span>
                    <span className={`px-2 py-0.5 rounded text-xs border ${ev.state === 'PUBLISHED' ? 'bg-emerald-500/10 text-emerald-400/80 border-emerald-500/20' : 'bg-zinc-800 text-zinc-400 border-zinc-700'}`}>{ev.state}</span>
                  </div>
                ))}</div>}
            </div>

            {controlGaps.length > 0 && (
              <div>
                <h3 className="text-sm text-zinc-500 mb-3">Gaps ({controlGaps.length})</h3>
                <div className="space-y-2">{controlGaps.map((gap: any, idx: number) => (
                  <div key={idx} className="p-3 bg-zinc-900/50 border border-zinc-800 rounded-lg">
                    <div className="flex items-center gap-2 mb-1">
                      <span className={`px-1.5 py-0.5 rounded text-xs font-medium ${gap.severity === 'CRITICAL' ? 'bg-red-500/10 text-red-400' : gap.severity === 'HIGH' ? 'bg-orange-500/10 text-orange-400' : 'bg-amber-500/10 text-amber-400'}`}>{gap.severity || 'MEDIUM'}</span>
                      <span className="text-xs text-zinc-500">{gap.gap_type}</span>
                    </div>
                    <p className="text-sm text-zinc-400">{gap.remediation || gap.description || 'Remediation needed'}</p>
                  </div>
                ))}</div>
              </div>
            )}
          </div>
        ) : (
          <div className="flex items-center justify-center h-full"><p className="text-zinc-600">Select a control to view details</p></div>
        )}
      </div>
    </div>
  );
}
