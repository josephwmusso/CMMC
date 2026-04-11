import React, { useState, useEffect, useRef } from 'react';
import { Upload, Download, Check, Lock, Loader2, Shield, FileText, X, Eye, Link2 } from 'lucide-react';
import { listArtifacts, uploadEvidence, transitionArtifact, downloadArtifact, generateManifest, downloadManifest, verifyAuditChain, previewArtifact, linkEvidenceToControls } from '../api/client';

const STATE_COLORS: Record<string, string> = {
  PUBLISHED: 'bg-emerald-500/10 text-emerald-400/80 border-emerald-500/20',
  APPROVED: 'bg-blue-500/10 text-blue-400/80 border-blue-500/20',
  REVIEWED: 'bg-amber-500/10 text-amber-400/80 border-amber-500/20',
  DRAFT: 'bg-zinc-800 text-zinc-400 border-zinc-700',
};
const NEXT_STATE: Record<string, string> = { DRAFT: 'REVIEWED', REVIEWED: 'APPROVED', APPROVED: 'PUBLISHED' };

function formatBytes(bytes: number) {
  if (!bytes) return '0 B';
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}

export function Evidence() {
  const [loading, setLoading] = useState(true);
  const [artifacts, setArtifacts] = useState<any[]>([]);
  const [search, setSearch] = useState('');
  const [stateFilter, setStateFilter] = useState('All States');
  const [uploading, setUploading] = useState(false);
  const [dragActive, setDragActive] = useState(false);
  const [manifestLoading, setManifestLoading] = useState(false);
  const [auditResult, setAuditResult] = useState<any>(null);
  const [auditLoading, setAuditLoading] = useState(false);
  const [previewData, setPreviewData] = useState<any>(null);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [linkingId, setLinkingId] = useState<string | null>(null);
  const [linkInput, setLinkInput] = useState('');
  const fileInputRef = useRef<HTMLInputElement>(null);

  const loadData = async () => {
    try { const d = await listArtifacts(null, 500); setArtifacts(d.artifacts || []); }
    catch {} finally { setLoading(false); }
  };
  useEffect(() => { loadData(); }, []);

  const handleUpload = async (files: FileList | File[]) => {
    setUploading(true);
    try {
      for (const file of Array.from(files)) await uploadEvidence(file, { evidence_type: 'Documentation', source_system: 'manual' });
      await loadData();
    } catch (e: any) { alert(e.message); }
    finally { setUploading(false); }
  };

  const handleTransition = async (id: string, newState: string) => {
    try { await transitionArtifact(id, newState); await loadData(); } catch (e: any) { alert(e.message); }
  };

  const handleGenerateManifest = async () => {
    setManifestLoading(true);
    try {
      const result = await generateManifest();
      alert(`Manifest generated: ${result.artifact_count} artifacts`);
    } catch (e: any) { alert(e.message); } finally { setManifestLoading(false); }
  };

  const handleVerifyAudit = async () => {
    setAuditLoading(true);
    try { const result = await verifyAuditChain(); setAuditResult(result); }
    catch (e: any) { alert(e.message); } finally { setAuditLoading(false); }
  };

  const handlePreview = async (id: string) => {
    setPreviewLoading(true);
    try { const data = await previewArtifact(id); setPreviewData(data); }
    catch (e: any) { alert(e.message); setPreviewData(null); } finally { setPreviewLoading(false); }
  };

  const handleLinkControls = async (artifactId: string) => {
    const ids = linkInput.split(',').map(s => s.trim()).filter(Boolean);
    if (ids.length === 0) return;
    try {
      const result = await linkEvidenceToControls(artifactId, ids);
      alert(`Linked ${result.links_created} control(s)`);
      setLinkingId(null);
      setLinkInput('');
    } catch (e: any) { alert(e.message); }
  };

  const stateCounts = ['All States', 'PUBLISHED', 'APPROVED', 'REVIEWED', 'DRAFT'].map(s => ({
    state: s, count: s === 'All States' ? artifacts.length : artifacts.filter(a => a.state === s).length,
  }));

  const filtered = artifacts.filter(a => {
    if (stateFilter !== 'All States' && a.state !== stateFilter) return false;
    if (search && !a.filename?.toLowerCase().includes(search.toLowerCase())) return false;
    return true;
  });

  if (loading) return <div className="flex items-center justify-center h-[60vh]"><Loader2 className="w-6 h-6 text-zinc-500 animate-spin" /></div>;

  // Empty state when no evidence has been collected yet.
  // Upload zone and toolbar stay visible — only the table area changes.
  const hasEvidence = artifacts && artifacts.length > 0;

  return (
    <div className="p-6">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-xl font-medium text-zinc-100 mb-1">Evidence</h1>
          <p className="text-sm text-zinc-500">Manage compliance artifacts and documentation</p>
        </div>
        <div className="flex items-center gap-2">
          <button onClick={handleVerifyAudit} disabled={auditLoading}
            className="px-3 py-2 bg-zinc-800 hover:bg-zinc-700 border border-zinc-700 rounded-lg text-sm text-zinc-300 transition-colors flex items-center gap-2">
            {auditLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Shield className="w-4 h-4" />} Verify Chain
          </button>
          <button onClick={handleGenerateManifest} disabled={manifestLoading}
            className="px-3 py-2 bg-zinc-800 hover:bg-zinc-700 border border-zinc-700 rounded-lg text-sm text-zinc-300 transition-colors flex items-center gap-2">
            {manifestLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <FileText className="w-4 h-4" />} Manifest
          </button>
          <button onClick={() => downloadManifest()}
            className="px-3 py-2 bg-zinc-800 hover:bg-zinc-700 border border-zinc-700 rounded-lg text-sm text-zinc-300 transition-colors flex items-center gap-2">
            <Download className="w-4 h-4" /> Download
          </button>
          <div className="w-px h-6 bg-zinc-700" />
          <button onClick={() => fileInputRef.current?.click()} disabled={uploading}
            className="px-4 py-2 bg-blue-500/80 hover:bg-blue-500 disabled:opacity-50 rounded-lg text-sm font-medium text-white transition-colors flex items-center gap-2">
            {uploading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Upload className="w-4 h-4" />}
            {uploading ? 'Uploading...' : 'Upload'}
          </button>
        </div>
        <input ref={fileInputRef} type="file" multiple className="hidden" onChange={e => e.target.files && handleUpload(e.target.files)} />
      </div>

      {auditResult && (
        <div className={`mb-4 flex items-center justify-between px-4 py-3 rounded-lg border ${auditResult.valid ? 'bg-emerald-500/10 border-emerald-500/20' : 'bg-red-500/10 border-red-500/20'}`}>
          <div className="flex items-center gap-2">
            <Shield className={`w-4 h-4 ${auditResult.valid ? 'text-emerald-400' : 'text-red-400'}`} />
            <span className={`text-sm font-medium ${auditResult.valid ? 'text-emerald-400' : 'text-red-400'}`}>
              {auditResult.valid ? 'Audit chain verified — all hashes valid' : `Chain integrity issue: ${auditResult.status}`}
            </span>
          </div>
          <button onClick={() => setAuditResult(null)} className="text-zinc-500 hover:text-zinc-300"><X className="w-4 h-4" /></button>
        </div>
      )}

      {hasEvidence && (
        <div className="mb-6 flex items-center justify-between">
          <div className="flex items-center gap-6">
            <div className="text-sm text-zinc-500"><span className="text-zinc-300 font-medium">{artifacts.length}</span> total artifacts</div>
            <div className="flex items-center gap-2">
              {stateCounts.map(item => (
                <button key={item.state} onClick={() => setStateFilter(item.state)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${stateFilter === item.state ? 'bg-zinc-800 text-zinc-300' : 'bg-zinc-900 text-zinc-500 hover:text-zinc-400'}`}>
                  {item.state} <span className="ml-1.5 opacity-70">{item.count}</span>
                </button>
              ))}
            </div>
          </div>
          <input type="text" placeholder="Search artifacts..." value={search} onChange={e => setSearch(e.target.value)}
            className="px-4 py-2 bg-zinc-900 border border-zinc-800 rounded-lg text-sm text-zinc-300 placeholder:text-zinc-600 focus:outline-none focus:border-zinc-700 w-64" />
        </div>
      )}

      <div onDragOver={e => { e.preventDefault(); setDragActive(true); }} onDragLeave={() => setDragActive(false)}
        onDrop={e => { e.preventDefault(); setDragActive(false); if (e.dataTransfer.files?.length) handleUpload(e.dataTransfer.files); }}
        onClick={() => fileInputRef.current?.click()}
        className={`mb-6 border-2 border-dashed rounded-xl p-12 text-center transition-all cursor-pointer ${dragActive ? 'border-blue-500 bg-blue-500/5' : 'border-zinc-800 bg-zinc-900/30 hover:border-zinc-700 hover:bg-zinc-900/50'}`}>
        <Upload className="w-12 h-12 text-zinc-600 mx-auto mb-4" />
        <div className="text-sm text-zinc-400 mb-2">Drag & drop evidence files here</div>
        <div className="text-xs text-zinc-600">or click to browse</div>
        <div className="text-xs text-zinc-700 mt-2">PDF, DOCX, CSV, PNG, JPG, TXT, MD, JSON</div>
      </div>

      {!hasEvidence ? (
        <EvidenceEmptyState />
      ) : (
      <>
      <div className="bg-zinc-900/50 border border-zinc-800 rounded-xl overflow-hidden">
        <table className="w-full">
          <thead className="bg-black border-b border-zinc-800">
            <tr className="text-xs text-zinc-500 uppercase tracking-wider">
              <th className="text-left px-6 py-3 font-medium">Filename</th>
              <th className="text-left px-6 py-3 font-medium">Type</th>
              <th className="text-left px-6 py-3 font-medium">Source</th>
              <th className="text-left px-6 py-3 font-medium">State</th>
              <th className="text-left px-6 py-3 font-medium">SHA-256</th>
              <th className="text-left px-6 py-3 font-medium">Size</th>
              <th className="text-right px-6 py-3 font-medium">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-zinc-800">
            {filtered.map(item => (<React.Fragment key={item.id}>
              <tr className="hover:bg-zinc-800/30 transition-colors">
                <td className="px-6 py-4"><div className="flex items-center gap-2"><Lock className="w-3.5 h-3.5 text-emerald-400/80" /><span className="text-sm text-zinc-300">{item.filename}</span></div></td>
                <td className="px-6 py-4"><span className="px-2 py-0.5 bg-zinc-800 rounded text-xs text-zinc-400">{item.evidence_type || 'N/A'}</span></td>
                <td className="px-6 py-4 text-sm text-zinc-500">{item.source_system || 'manual'}</td>
                <td className="px-6 py-4"><span className={`px-2 py-0.5 border rounded text-xs font-medium ${STATE_COLORS[item.state] || STATE_COLORS.DRAFT}`}>{item.state}</span></td>
                <td className="px-6 py-4"><span className="text-xs font-mono text-zinc-600">{(item.sha256_hash || '').slice(0, 20)}...</span></td>
                <td className="px-6 py-4 text-sm text-zinc-500">{formatBytes(item.file_size_bytes)}</td>
                <td className="px-6 py-4">
                  <div className="flex items-center justify-end gap-2">
                    <button onClick={() => handlePreview(item.id)} className="p-1.5 hover:bg-zinc-800 rounded transition-colors" title="Preview">
                      <Eye className="w-4 h-4 text-zinc-500" />
                    </button>
                    <button onClick={() => { setLinkingId(linkingId === item.id ? null : item.id); setLinkInput(''); }} className="p-1.5 hover:bg-zinc-800 rounded transition-colors" title="Link Controls">
                      <Link2 className="w-4 h-4 text-zinc-500" />
                    </button>
                    {NEXT_STATE[item.state] && (
                      <button onClick={() => handleTransition(item.id, NEXT_STATE[item.state])} className="p-1.5 hover:bg-zinc-800 rounded transition-colors" title={`Advance to ${NEXT_STATE[item.state]}`}>
                        <Check className="w-4 h-4 text-zinc-500" />
                      </button>
                    )}
                    <button onClick={() => downloadArtifact(item.id, item.filename)} className="p-1.5 hover:bg-zinc-800 rounded transition-colors" title="Download">
                      <Download className="w-4 h-4 text-zinc-500" />
                    </button>
                  </div>
                </td>
              </tr>
              {linkingId === item.id && (
                <tr className="bg-zinc-900/80">
                  <td colSpan={7} className="px-6 py-3">
                    <div className="flex items-center gap-3">
                      <span className="text-xs text-zinc-500">Link to controls:</span>
                      <input type="text" value={linkInput} onChange={e => setLinkInput(e.target.value)}
                        placeholder="AC.L2-3.1.1, SC.L2-3.13.11, ..." className="flex-1 px-3 py-1.5 bg-black border border-zinc-700 rounded text-sm text-zinc-300 placeholder:text-zinc-600 focus:outline-none focus:border-zinc-600" />
                      <button onClick={() => handleLinkControls(item.id)} className="px-3 py-1.5 bg-blue-500/80 hover:bg-blue-500 rounded text-sm text-white">Link</button>
                      <button onClick={() => setLinkingId(null)} className="px-3 py-1.5 bg-zinc-800 hover:bg-zinc-700 rounded text-sm text-zinc-400">Cancel</button>
                    </div>
                  </td>
                </tr>
              )}
            </React.Fragment>))}
          </tbody>
        </table>
      </div>
      <div className="mt-4 text-xs text-zinc-600">Showing {filtered.length} of {artifacts.length} artifacts</div>
      </>
      )}

      {/* Preview Modal */}
      {(previewData || previewLoading) && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm" onClick={() => { setPreviewData(null); setPreviewLoading(false); }}>
          <div className="bg-zinc-900 border border-zinc-700 rounded-xl w-[700px] max-h-[80vh] flex flex-col" onClick={e => e.stopPropagation()}>
            <div className="flex items-center justify-between px-5 py-4 border-b border-zinc-800">
              <div className="text-sm font-medium text-zinc-200">{previewData?.filename || 'Loading...'}</div>
              <button onClick={() => { setPreviewData(null); setPreviewLoading(false); }} className="text-zinc-500 hover:text-zinc-300"><X className="w-4 h-4" /></button>
            </div>
            <div className="flex-1 overflow-auto p-5">
              {previewLoading ? (
                <div className="flex items-center justify-center py-12"><Loader2 className="w-6 h-6 text-zinc-500 animate-spin" /></div>
              ) : previewData?.content_type === 'image' ? (
                <img src={`data:${previewData.mime};base64,${previewData.content}`} alt={previewData.filename} className="max-w-full rounded" />
              ) : previewData?.content_type === 'text' ? (
                <pre className="text-sm text-zinc-300 font-mono whitespace-pre-wrap leading-relaxed">{previewData.content}</pre>
              ) : (
                <div className="text-center py-12 text-zinc-500">
                  <FileText className="w-10 h-10 mx-auto mb-3 text-zinc-700" />
                  <div className="text-sm">Binary file — download to view</div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// ── Empty state ────────────────────────────────────────────────────────────
// Lifecycle stages match STATE_COLORS used in the populated table:
// DRAFT (zinc) → REVIEWED (amber) → APPROVED (blue) → PUBLISHED (emerald)

const LIFECYCLE_STAGES = [
  {
    state: 'DRAFT',
    label: 'Draft',
    color: 'text-zinc-400',
    border: 'border-zinc-700',
    bg: 'bg-zinc-800/40',
    desc: 'New artifacts enter as drafts. Uploaded files and AI-generated documents start here.',
  },
  {
    state: 'REVIEWED',
    label: 'Reviewed',
    color: 'text-amber-400/90',
    border: 'border-amber-500/30',
    bg: 'bg-amber-500/5',
    desc: 'A reviewer confirms the artifact is relevant and accurate.',
  },
  {
    state: 'APPROVED',
    label: 'Approved',
    color: 'text-blue-400/90',
    border: 'border-blue-500/30',
    bg: 'bg-blue-500/5',
    desc: 'An approver signs off. The artifact is ready for publication.',
  },
  {
    state: 'PUBLISHED',
    label: 'Published',
    color: 'text-emerald-400/90',
    border: 'border-emerald-500/30',
    bg: 'bg-emerald-500/5',
    desc: 'Immutable. SHA-256 hashed. Final-form evidence for your assessment.',
  },
];

function EvidenceEmptyState() {
  return (
    <div className="bg-zinc-900/50 border border-zinc-800 rounded-xl p-8 md:p-10">
      {/* Welcome explanation */}
      <div className="max-w-3xl mb-10">
        <h2 className="text-xl font-medium text-zinc-100 mb-3">No Evidence Collected Yet</h2>
        <p className="text-sm text-zinc-400 leading-relaxed mb-2">
          Evidence artifacts are the foundation of your CMMC assessment. Each artifact proves
          that a security control is implemented — policies, configuration exports, scan
          reports, training records, and more.
        </p>
        <p className="text-sm text-zinc-500 leading-relaxed">
          Artifacts are created automatically when you complete the intake questionnaire and
          generate compliance documents. You can also upload evidence directly using the area
          above.
        </p>
      </div>

      {/* Lifecycle visual */}
      <div className="mb-10">
        <div className="text-xs text-zinc-500 uppercase tracking-wider mb-4">Evidence Lifecycle</div>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-3 md:gap-2 items-stretch">
          {LIFECYCLE_STAGES.map((stage, i) => (
            <div key={stage.state} className="relative flex">
              <div className={`flex-1 ${stage.bg} border ${stage.border} rounded-lg p-4`}>
                <div className={`text-xs font-mono font-medium ${stage.color} uppercase tracking-wider mb-2`}>
                  {stage.state}
                </div>
                <div className="text-xs text-zinc-500 leading-relaxed">{stage.desc}</div>
              </div>
              {i < LIFECYCLE_STAGES.length - 1 && (
                <div className="hidden md:flex items-center justify-center w-2 flex-shrink-0">
                  <div className="text-zinc-700 text-xs">→</div>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* How evidence gets created */}
      <div>
        <div className="text-xs text-zinc-500 uppercase tracking-wider mb-4">How Evidence Gets Created</div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          <div className="bg-zinc-900/50 border border-zinc-800 rounded-lg p-4">
            <h4 className="text-sm font-medium text-zinc-200 mb-1.5">From Intake</h4>
            <p className="text-xs text-zinc-500 leading-relaxed">
              Completing the questionnaire and generating documents automatically creates draft
              artifacts linked to relevant controls.
            </p>
          </div>
          <div className="bg-zinc-900/50 border border-zinc-800 rounded-lg p-4">
            <h4 className="text-sm font-medium text-zinc-200 mb-1.5">Upload Directly</h4>
            <p className="text-xs text-zinc-500 leading-relaxed">
              Upload policy documents, configuration exports, scan reports, training records,
              or any supporting artifact.
            </p>
          </div>
          <div className="bg-zinc-900/30 border border-zinc-800/60 rounded-lg p-4 opacity-60">
            <div className="flex items-center gap-2 mb-1.5">
              <h4 className="text-sm font-medium text-zinc-300">From Connectors</h4>
              <span className="text-[10px] font-medium text-zinc-500 uppercase tracking-wider px-1.5 py-0.5 bg-zinc-800 border border-zinc-700 rounded">Soon</span>
            </div>
            <p className="text-xs text-zinc-500 leading-relaxed">
              Automated evidence collection from Entra ID, M365, CrowdStrike, and more.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
