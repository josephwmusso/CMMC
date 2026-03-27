import { useState, useEffect, useRef } from 'react';
import { Upload, Download, Check, Lock, Loader2 } from 'lucide-react';
import { listArtifacts, uploadEvidence, transitionArtifact, downloadArtifact } from '../api/client';

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

  const stateCounts = ['All States', 'PUBLISHED', 'APPROVED', 'REVIEWED', 'DRAFT'].map(s => ({
    state: s, count: s === 'All States' ? artifacts.length : artifacts.filter(a => a.state === s).length,
  }));

  const filtered = artifacts.filter(a => {
    if (stateFilter !== 'All States' && a.state !== stateFilter) return false;
    if (search && !a.filename?.toLowerCase().includes(search.toLowerCase())) return false;
    return true;
  });

  if (loading) return <div className="flex items-center justify-center h-[60vh]"><Loader2 className="w-6 h-6 text-zinc-500 animate-spin" /></div>;

  return (
    <div className="p-6">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-xl font-medium text-zinc-100 mb-1">Evidence</h1>
          <p className="text-sm text-zinc-500">Manage compliance artifacts and documentation</p>
        </div>
        <button onClick={() => fileInputRef.current?.click()} disabled={uploading}
          className="px-4 py-2 bg-zinc-800 hover:bg-zinc-700 rounded-lg text-sm font-medium text-zinc-300 transition-colors flex items-center gap-2">
          {uploading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Upload className="w-4 h-4" />}
          {uploading ? 'Uploading...' : 'Upload Evidence'}
        </button>
        <input ref={fileInputRef} type="file" multiple className="hidden" onChange={e => e.target.files && handleUpload(e.target.files)} />
      </div>

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

      <div onDragOver={e => { e.preventDefault(); setDragActive(true); }} onDragLeave={() => setDragActive(false)}
        onDrop={e => { e.preventDefault(); setDragActive(false); if (e.dataTransfer.files?.length) handleUpload(e.dataTransfer.files); }}
        onClick={() => fileInputRef.current?.click()}
        className={`mb-6 border-2 border-dashed rounded-xl p-12 text-center transition-all cursor-pointer ${dragActive ? 'border-blue-500 bg-blue-500/5' : 'border-zinc-800 bg-zinc-900/30 hover:border-zinc-700 hover:bg-zinc-900/50'}`}>
        <Upload className="w-12 h-12 text-zinc-600 mx-auto mb-4" />
        <div className="text-sm text-zinc-400 mb-2">Drag & drop evidence files here</div>
        <div className="text-xs text-zinc-600">or click to browse</div>
        <div className="text-xs text-zinc-700 mt-2">PDF, DOCX, CSV, PNG, JPG, TXT, MD, JSON</div>
      </div>

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
            {filtered.map(item => (
              <tr key={item.id} className="hover:bg-zinc-800/30 transition-colors">
                <td className="px-6 py-4"><div className="flex items-center gap-2"><Lock className="w-3.5 h-3.5 text-emerald-400/80" /><span className="text-sm text-zinc-300">{item.filename}</span></div></td>
                <td className="px-6 py-4"><span className="px-2 py-0.5 bg-zinc-800 rounded text-xs text-zinc-400">{item.evidence_type || 'N/A'}</span></td>
                <td className="px-6 py-4 text-sm text-zinc-500">{item.source_system || 'manual'}</td>
                <td className="px-6 py-4"><span className={`px-2 py-0.5 border rounded text-xs font-medium ${STATE_COLORS[item.state] || STATE_COLORS.DRAFT}`}>{item.state}</span></td>
                <td className="px-6 py-4"><span className="text-xs font-mono text-zinc-600">{(item.sha256_hash || '').slice(0, 20)}...</span></td>
                <td className="px-6 py-4 text-sm text-zinc-500">{formatBytes(item.file_size_bytes)}</td>
                <td className="px-6 py-4">
                  <div className="flex items-center justify-end gap-2">
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
            ))}
          </tbody>
        </table>
      </div>
      <div className="mt-4 text-xs text-zinc-600">Showing {filtered.length} of {artifacts.length} artifacts</div>
    </div>
  );
}
