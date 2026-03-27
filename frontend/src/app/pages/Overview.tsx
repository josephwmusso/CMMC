import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router';
import { AlertTriangle, Upload, FileCheck, ArrowRight, Shield, FileText, Clock, AlertCircle, Loader2, Download, Sparkles } from 'lucide-react';
import { getComplianceOverview, listArtifacts, generateFullSSP } from '../api/client';
import { toast } from 'sonner';

export function Overview() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [overview, setOverview] = useState<any>(null);
  const [evidenceCount, setEvidenceCount] = useState(0);
  const [generating, setGenerating] = useState(false);

  const handleGenerateSSP = async () => {
    setGenerating(true);
    try {
      const job = await generateFullSSP();
      toast.success(`SSP generation started — job ${job.job_id}. This takes ~30 minutes.`);
    } catch (e: any) {
      toast.error(e.message || 'Failed to start SSP generation');
    } finally {
      setGenerating(false);
    }
  };

  useEffect(() => {
    async function load() {
      try {
        const [ov, ev] = await Promise.all([
          getComplianceOverview(),
          listArtifacts(null, 500),
        ]);
        setOverview(ov);
        const artifacts = ev.artifacts || ev || [];
        setEvidenceCount(Array.isArray(artifacts) ? artifacts.length : ev.count || 0);
      } catch (e: any) {
        setError(e.message);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-[60vh]">
        <Loader2 className="w-6 h-6 text-zinc-500 animate-spin" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <div className="bg-red-500/10 border border-red-500/20 rounded-xl p-6 text-center">
          <p className="text-red-400 mb-2">Failed to load dashboard</p>
          <p className="text-sm text-zinc-500">{error}</p>
          <button onClick={() => window.location.reload()} className="mt-4 px-4 py-2 bg-zinc-800 hover:bg-zinc-700 rounded-lg text-sm text-zinc-300">Retry</button>
        </div>
      </div>
    );
  }

  const sprs = overview?.sprs || {};
  const poam = overview?.poam || {};
  const gaps = overview?.gaps || {};
  const score = sprs.score ?? 0;
  const maxScore = sprs.max_score ?? 110;
  const met = sprs.met ?? 0;
  const partial = sprs.partial ?? 0;
  const notMet = sprs.not_met ?? 0;
  const totalControls = met + partial + notMet;
  const poamTotal = poam.total_items ?? poam.total ?? 0;
  const gapDetails = gaps.gap_details || [];
  const overduePoam = (poam.items || []).filter((i: any) => i.status === 'OVERDUE').length;

  return (
    <div className="p-6 w-full">
      {/* Top Row: Score + Quick Stats */}
      <div className="grid grid-cols-12 gap-4 mb-6">
        <div className="col-span-4">
          <div className="bg-zinc-900/50 border border-zinc-800 rounded-xl p-5">
            <div className="text-xs text-zinc-600 uppercase tracking-wider mb-3">Compliance Score</div>
            <div className="flex items-end gap-3 mb-3">
              <div className="text-5xl font-medium text-zinc-100">{score}</div>
              <div className="pb-2 text-zinc-500 text-sm">/ {maxScore}</div>
            </div>
            <div className="h-1.5 bg-zinc-800 rounded-full overflow-hidden mb-2">
              <div className="h-full bg-orange-400/80 rounded-full" style={{ width: `${maxScore > 0 ? (score / maxScore) * 100 : 0}%` }} />
            </div>
            <div className="text-xs text-zinc-500">Target: 95+ for certification</div>
          </div>
        </div>

        <div className="col-span-8 grid grid-cols-4 gap-4">
          <div className="bg-zinc-900/50 border border-zinc-800 rounded-xl p-4">
            <div className="flex items-center gap-2 mb-2">
              <Shield className="w-3.5 h-3.5 text-zinc-600" />
              <div className="text-xs text-zinc-600">Controls Met</div>
            </div>
            <div className="text-2xl font-medium text-zinc-100">{met}</div>
            <div className="text-xs text-zinc-600 mt-0.5">of {totalControls} ({partial} partial)</div>
          </div>

          <div className="bg-zinc-900/50 border border-zinc-800 rounded-xl p-4">
            <div className="flex items-center gap-2 mb-2">
              <FileText className="w-3.5 h-3.5 text-zinc-600" />
              <div className="text-xs text-zinc-600">Evidence</div>
            </div>
            <div className="text-2xl font-medium text-zinc-100">{evidenceCount}</div>
            <div className="text-xs text-zinc-600 mt-0.5">artifacts</div>
          </div>

          <div className="bg-zinc-900/50 border border-zinc-800 rounded-xl p-4">
            <div className="flex items-center gap-2 mb-2">
              <AlertCircle className="w-3.5 h-3.5 text-zinc-600" />
              <div className="text-xs text-zinc-600">POA&M</div>
            </div>
            <div className="text-2xl font-medium text-zinc-100">{poamTotal}</div>
            <div className="text-xs text-zinc-600 mt-0.5">{overduePoam > 0 ? <span className="text-red-400/90">{overduePoam} overdue</span> : 'items'}</div>
          </div>

          <div className="bg-zinc-900/50 border border-zinc-800 rounded-xl p-4">
            <div className="flex items-center gap-2 mb-2">
              <Clock className="w-3.5 h-3.5 text-zinc-600" />
              <div className="text-xs text-zinc-600">Gaps</div>
            </div>
            <div className="text-2xl font-medium text-zinc-100">{gapDetails.length}</div>
            <div className="text-xs text-zinc-600 mt-0.5">findings</div>
          </div>
        </div>
      </div>

      {/* Main Content: Actions + Summary */}
      <div className="grid grid-cols-12 gap-6">
        <div className="col-span-8">
          <h2 className="text-base font-medium text-zinc-200 mb-4">What needs your attention</h2>
          <div className="space-y-2">
            {/* Generate SSP - Primary Action */}
            <button
              onClick={handleGenerateSSP}
              disabled={generating}
              className="w-full bg-zinc-900/50 border border-zinc-800 hover:border-zinc-700 rounded-lg p-5 text-left transition-all group disabled:opacity-60"
            >
              <div className="flex items-center gap-4">
                <div className="w-10 h-10 rounded-lg bg-zinc-800 border border-zinc-700 flex items-center justify-center flex-shrink-0">
                  {generating ? <Loader2 className="w-5 h-5 text-zinc-400 animate-spin" /> : <Download className="w-5 h-5 text-zinc-400" />}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <h3 className="text-base font-medium text-zinc-100">{generating ? 'Generating System Security Plan...' : 'Generate System Security Plan'}</h3>
                  </div>
                  <div className="text-sm text-zinc-500">{generating ? 'Processing all 110 NIST controls — this takes ~30 minutes' : `Export your complete SSP with all ${totalControls} NIST controls as a DOCX document`}</div>
                </div>
                <ArrowRight className="w-5 h-5 text-zinc-600 group-hover:text-zinc-400 transition-colors" />
              </div>
            </button>

            {gapDetails.length > 0 && (
              <button onClick={() => navigate('/ssp')} className="w-full bg-zinc-900/50 border border-zinc-800 hover:border-zinc-700/50 rounded-lg p-4 text-left transition-all group">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-lg bg-red-500/10 border border-red-500/20 flex items-center justify-center flex-shrink-0">
                    <AlertTriangle className="w-4 h-4 text-red-400/80" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <h3 className="text-sm font-medium text-zinc-200">{gapDetails.length} compliance gaps found</h3>
                      <span className="px-1.5 py-0.5 bg-red-500/10 border border-red-500/20 rounded text-xs font-medium text-red-400/80">REVIEW</span>
                    </div>
                    <div className="text-xs text-zinc-600">
                      {gapDetails.filter((g: any) => (g.severity || g.risk_level) === 'CRITICAL').length} critical,{' '}
                      {gapDetails.filter((g: any) => (g.severity || g.risk_level) === 'HIGH').length} high severity
                    </div>
                  </div>
                  <ArrowRight className="w-4 h-4 text-zinc-600 group-hover:text-zinc-400 transition-colors" />
                </div>
              </button>
            )}

            <button onClick={() => navigate('/evidence')} className="w-full bg-zinc-900/50 border border-zinc-800 hover:border-zinc-700/50 rounded-lg p-4 text-left transition-all group">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg bg-orange-500/10 border border-orange-500/20 flex items-center justify-center flex-shrink-0">
                  <Upload className="w-4 h-4 text-orange-400/80" />
                </div>
                <div className="flex-1 min-w-0">
                  <h3 className="text-sm font-medium text-zinc-200">Upload evidence artifacts</h3>
                  <div className="text-xs text-zinc-600">{evidenceCount} artifacts on file</div>
                </div>
                <ArrowRight className="w-4 h-4 text-zinc-600 group-hover:text-zinc-400 transition-colors" />
              </div>
            </button>

            <button onClick={() => navigate('/intake')} className="w-full bg-zinc-900/50 border border-zinc-800 hover:border-zinc-700/50 rounded-lg p-4 text-left transition-all group">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg bg-blue-500/10 border border-blue-500/20 flex items-center justify-center flex-shrink-0">
                  <FileCheck className="w-4 h-4 text-blue-400/80" />
                </div>
                <div className="flex-1 min-w-0">
                  <h3 className="text-sm font-medium text-zinc-200">Complete setup wizard</h3>
                  <div className="text-xs text-zinc-600">Answer intake questions to improve assessment accuracy</div>
                </div>
                <ArrowRight className="w-4 h-4 text-zinc-600 group-hover:text-zinc-400 transition-colors" />
              </div>
            </button>

            {poamTotal > 0 && (
              <button onClick={() => navigate('/poam')} className="w-full bg-zinc-900/50 border border-zinc-800 hover:border-zinc-700/50 rounded-lg p-4 text-left transition-all group">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-lg bg-violet-500/10 border border-violet-500/20 flex items-center justify-center flex-shrink-0">
                    <FileCheck className="w-4 h-4 text-violet-400/80" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <h3 className="text-sm font-medium text-zinc-200">{poamTotal} POA&M items to review</h3>
                    <div className="text-xs text-zinc-600">Review remediation plans and update status</div>
                  </div>
                  <ArrowRight className="w-4 h-4 text-zinc-600 group-hover:text-zinc-400 transition-colors" />
                </div>
              </button>
            )}
          </div>
        </div>

        <div className="col-span-4">
          <h3 className="text-sm font-medium text-zinc-400 mb-4">Compliance summary</h3>
          <div className="space-y-3 text-sm">
            <div className="flex items-center justify-between">
              <span className="text-zinc-500">Implemented</span>
              <span className="text-emerald-400 font-medium">{met}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-zinc-500">Partially Implemented</span>
              <span className="text-blue-400 font-medium">{partial}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-zinc-500">Not Implemented</span>
              <span className="text-red-400 font-medium">{notMet}</span>
            </div>
            <div className="border-t border-zinc-800 pt-3 flex items-center justify-between">
              <span className="text-zinc-500">Total Controls</span>
              <span className="text-zinc-300 font-medium">{totalControls}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-zinc-500">Evidence Artifacts</span>
              <span className="text-zinc-300 font-medium">{evidenceCount}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-zinc-500">POA&M Items</span>
              <span className="text-zinc-300 font-medium">{poamTotal}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
