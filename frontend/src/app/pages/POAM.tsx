import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router';
import { Download, Loader2, AlertTriangle, ChevronRight, ArrowRight, Shield, Clock, TrendingDown, CheckCircle2 } from 'lucide-react';
import { getPoamSummary, exportPoamPdf, exportPoamDocx } from '../api/client';

const RISK_COLORS: Record<string, { border: string; bg: string; text: string; dot: string }> = {
  CRITICAL: { border: 'border-l-red-500', bg: 'bg-red-500/10', text: 'text-red-400', dot: 'bg-red-500' },
  HIGH:     { border: 'border-l-orange-500', bg: 'bg-orange-500/10', text: 'text-orange-400', dot: 'bg-orange-500' },
  MEDIUM:   { border: 'border-l-amber-500', bg: 'bg-amber-500/10', text: 'text-amber-400', dot: 'bg-amber-500' },
};

const STATUS_STYLES: Record<string, string> = {
  OPEN: 'bg-zinc-800 text-zinc-400',
  IN_PROGRESS: 'bg-blue-500/15 text-blue-400 border border-blue-500/20',
  CLOSED: 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/20',
  OVERDUE: 'bg-red-500/15 text-red-400 border border-red-500/20',
};

function daysUntil(dateStr: string): number {
  if (!dateStr) return 999;
  const due = new Date(dateStr);
  const now = new Date();
  return Math.ceil((due.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));
}

function formatDeadline(dateStr: string) {
  const days = daysUntil(dateStr);
  if (days < 0) return { text: `${Math.abs(days)} days overdue`, className: 'text-red-400 font-medium' };
  if (days === 0) return { text: 'Due today', className: 'text-red-400 font-medium' };
  if (days <= 7) return { text: `${days} days left`, className: 'text-orange-400 font-medium' };
  if (days <= 30) return { text: `${days} days left`, className: 'text-amber-400' };
  return { text: `${days} days left`, className: 'text-zinc-500' };
}

function getEffectiveStatus(item: any): string {
  if (item.status === 'OPEN' && item.scheduled_completion && daysUntil(item.scheduled_completion) < 0) return 'OVERDUE';
  return item.status;
}

export function POAM() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [items, setItems] = useState<any[]>([]);
  const [statusCounts, setStatusCounts] = useState<any>({});
  const [riskFilter, setRiskFilter] = useState('All');
  const [statusFilter, setStatusFilter] = useState('All');
  const [sortBy, setSortBy] = useState<'urgency' | 'risk' | 'deadline'>('urgency');
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [exporting, setExporting] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const data = await getPoamSummary();
        setItems(data.items || []);
        setStatusCounts(data.status_counts || {});
      } catch {} finally { setLoading(false); }
    }
    load();
  }, []);

  const handleExport = async (type: 'pdf' | 'docx') => {
    setExporting(type);
    try { type === 'pdf' ? await exportPoamPdf() : await exportPoamDocx(); }
    catch (e: any) { alert(e.message); } finally { setExporting(null); }
  };

  // Compute derived data
  const overdueCount = items.filter(i => getEffectiveStatus(i) === 'OVERDUE').length;
  const dueSoonCount = items.filter(i => {
    const d = daysUntil(i.scheduled_completion);
    return d >= 0 && d <= 30 && getEffectiveStatus(i) !== 'CLOSED';
  }).length;
  const closedCount = statusCounts.CLOSED || 0;
  const inProgressCount = statusCounts.IN_PROGRESS || 0;
  const pointsAtRisk = items
    .filter(i => getEffectiveStatus(i) !== 'CLOSED')
    .reduce((sum, i) => sum + (i.points || 0), 0);

  // Filter
  const filtered = items.filter(i => {
    if (riskFilter !== 'All' && i.risk_level !== riskFilter) return false;
    const eff = getEffectiveStatus(i);
    if (statusFilter !== 'All' && eff !== statusFilter) return false;
    return true;
  });

  // Sort
  const sorted = [...filtered].sort((a, b) => {
    if (sortBy === 'urgency') {
      const aOverdue = getEffectiveStatus(a) === 'OVERDUE' ? 0 : 1;
      const bOverdue = getEffectiveStatus(b) === 'OVERDUE' ? 0 : 1;
      if (aOverdue !== bOverdue) return aOverdue - bOverdue;
      const riskW: Record<string, number> = { CRITICAL: 3, HIGH: 2, MEDIUM: 1 };
      const aScore = (riskW[a.risk_level] || 0) * (1 / Math.max(daysUntil(a.scheduled_completion), 1));
      const bScore = (riskW[b.risk_level] || 0) * (1 / Math.max(daysUntil(b.scheduled_completion), 1));
      return bScore - aScore;
    }
    if (sortBy === 'risk') {
      const riskW: Record<string, number> = { CRITICAL: 3, HIGH: 2, MEDIUM: 1 };
      return (riskW[b.risk_level] || 0) - (riskW[a.risk_level] || 0);
    }
    return daysUntil(a.scheduled_completion) - daysUntil(b.scheduled_completion);
  });

  if (loading) return <div className="flex items-center justify-center h-[60vh]"><Loader2 className="w-6 h-6 text-zinc-500 animate-spin" /></div>;

  return (
    <div className="p-6 w-full">

      {/* Alert Banner */}
      {overdueCount > 0 && (
        <div className="mb-6 flex items-center gap-3 px-5 py-4 bg-red-500/10 border border-red-500/20 rounded-xl">
          <AlertTriangle className="w-5 h-5 text-red-400 flex-shrink-0" />
          <div className="flex-1">
            <span className="text-sm font-medium text-red-400">{overdueCount} item{overdueCount > 1 ? 's' : ''} past deadline</span>
            <span className="text-sm text-red-400/70 ml-2">— these block CMMC certification</span>
          </div>
          <button onClick={() => { setStatusFilter('OVERDUE'); setRiskFilter('All'); }}
            className="px-3 py-1.5 bg-red-500/20 hover:bg-red-500/30 rounded-lg text-xs font-medium text-red-400 transition-colors">
            View overdue
          </button>
        </div>
      )}

      {/* Header */}
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-xl font-medium text-zinc-100 mb-1">Plan of Action & Milestones</h1>
          <p className="text-sm text-zinc-500">Track and remediate compliance gaps</p>
        </div>
        <div className="flex items-center gap-3">
          <button onClick={() => handleExport('pdf')} disabled={!!exporting}
            className="px-4 py-2 bg-zinc-800 hover:bg-zinc-700 border border-zinc-700 rounded-lg text-sm text-zinc-300 transition-colors flex items-center gap-2">
            {exporting === 'pdf' ? <Loader2 className="w-4 h-4 animate-spin" /> : <Download className="w-4 h-4" />} PDF
          </button>
          <button onClick={() => handleExport('docx')} disabled={!!exporting}
            className="px-4 py-2 bg-blue-400/80 hover:bg-blue-400 rounded-lg text-sm font-medium text-white transition-colors flex items-center gap-2">
            {exporting === 'docx' ? <Loader2 className="w-4 h-4 animate-spin" /> : <Download className="w-4 h-4" />} DOCX
          </button>
        </div>
      </div>

      {/* KPI Strip */}
      <div className="mb-6 grid grid-cols-5 gap-4">
        <div className="bg-zinc-900/50 border border-zinc-800 rounded-xl p-4">
          <div className="flex items-center gap-2 mb-2">
            <TrendingDown className="w-3.5 h-3.5 text-zinc-600" />
            <span className="text-xs text-zinc-600 uppercase tracking-wider">Points at Risk</span>
          </div>
          <div className="text-3xl font-medium text-zinc-100">{pointsAtRisk}</div>
          <div className="text-xs text-zinc-600 mt-1">SPRS impact</div>
        </div>
        <div className={`bg-zinc-900/50 border rounded-xl p-4 ${overdueCount > 0 ? 'border-red-500/30' : 'border-zinc-800'}`}>
          <div className="flex items-center gap-2 mb-2">
            <AlertTriangle className={`w-3.5 h-3.5 ${overdueCount > 0 ? 'text-red-400' : 'text-zinc-600'}`} />
            <span className="text-xs text-zinc-600 uppercase tracking-wider">Overdue</span>
          </div>
          <div className={`text-3xl font-medium ${overdueCount > 0 ? 'text-red-400' : 'text-zinc-100'}`}>{overdueCount}</div>
          <div className="text-xs text-zinc-600 mt-1">past deadline</div>
        </div>
        <div className="bg-zinc-900/50 border border-zinc-800 rounded-xl p-4">
          <div className="flex items-center gap-2 mb-2">
            <Clock className="w-3.5 h-3.5 text-amber-400/70" />
            <span className="text-xs text-zinc-600 uppercase tracking-wider">Due Soon</span>
          </div>
          <div className="text-3xl font-medium text-amber-400">{dueSoonCount}</div>
          <div className="text-xs text-zinc-600 mt-1">within 30 days</div>
        </div>
        <div className="bg-zinc-900/50 border border-zinc-800 rounded-xl p-4">
          <div className="flex items-center gap-2 mb-2">
            <Shield className="w-3.5 h-3.5 text-blue-400/70" />
            <span className="text-xs text-zinc-600 uppercase tracking-wider">In Progress</span>
          </div>
          <div className="text-3xl font-medium text-blue-400">{inProgressCount}</div>
          <div className="text-xs text-zinc-600 mt-1">being remediated</div>
        </div>
        <div className="bg-zinc-900/50 border border-zinc-800 rounded-xl p-4">
          <div className="flex items-center gap-2 mb-2">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400/70" />
            <span className="text-xs text-zinc-600 uppercase tracking-wider">Closed</span>
          </div>
          <div className="text-3xl font-medium text-emerald-400">{closedCount}</div>
          <div className="text-xs text-zinc-600 mt-1">remediated</div>
        </div>
      </div>

      {/* Filters + Sort */}
      <div className="mb-5 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-xs text-zinc-600 mr-1">Risk:</span>
          {['All', 'CRITICAL', 'HIGH', 'MEDIUM'].map(f => (
            <button key={f} onClick={() => setRiskFilter(f)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${riskFilter === f ? 'bg-zinc-700 text-zinc-200' : 'bg-zinc-900 text-zinc-500 hover:text-zinc-400'}`}>{f}</button>
          ))}
          <div className="w-px h-5 bg-zinc-800 mx-2" />
          <span className="text-xs text-zinc-600 mr-1">Status:</span>
          {['All', 'OVERDUE', 'OPEN', 'IN_PROGRESS', 'CLOSED'].map(f => (
            <button key={f} onClick={() => setStatusFilter(f)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${statusFilter === f ? 'bg-zinc-700 text-zinc-200' : 'bg-zinc-900 text-zinc-500 hover:text-zinc-400'}`}>
              {f.replace('_', ' ')}
            </button>
          ))}
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs text-zinc-600">Sort:</span>
          {([['urgency', 'Urgency'], ['risk', 'Risk'], ['deadline', 'Deadline']] as const).map(([val, label]) => (
            <button key={val} onClick={() => setSortBy(val)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${sortBy === val ? 'bg-zinc-700 text-zinc-200' : 'bg-zinc-900 text-zinc-500 hover:text-zinc-400'}`}>{label}</button>
          ))}
        </div>
      </div>

      {/* Card List */}
      {sorted.length === 0 ? (
        <div className="text-center py-16">
          <CheckCircle2 className="w-12 h-12 text-emerald-400/30 mx-auto mb-4" />
          <div className="text-zinc-400 mb-1">No items match your filters</div>
          <div className="text-sm text-zinc-600">Try adjusting the risk or status filters</div>
        </div>
      ) : (
        <div className="space-y-2">
          {sorted.map((item, idx) => {
            const effStatus = getEffectiveStatus(item);
            const risk = RISK_COLORS[item.risk_level] || RISK_COLORS.MEDIUM;
            const deadline = formatDeadline(item.scheduled_completion);
            const isExpanded = expandedId === item.id;

            return (
              <div key={item.id || idx}>
                {/* Card row */}
                <button
                  onClick={() => setExpandedId(isExpanded ? null : item.id)}
                  className={`w-full text-left border-l-[3px] ${risk.border} bg-zinc-900/50 border border-zinc-800 hover:border-zinc-700 rounded-lg rounded-l-none transition-all ${isExpanded ? 'border-zinc-700' : ''}`}
                >
                  <div className="flex items-center gap-4 px-5 py-4">
                    <ChevronRight className={`w-4 h-4 text-zinc-600 transition-transform flex-shrink-0 ${isExpanded ? 'rotate-90' : ''}`} />

                    {/* Risk dot */}
                    <div className={`w-2.5 h-2.5 rounded-full flex-shrink-0 ${risk.dot}`} />

                    {/* Control ID */}
                    <span className="text-xs font-mono text-zinc-500 bg-zinc-800 px-2 py-1 rounded flex-shrink-0 w-[130px]">{item.control_id}</span>

                    {/* Weakness */}
                    <div className="flex-1 min-w-0">
                      <div className="text-sm text-zinc-300 truncate">{item.weakness_description || 'N/A'}</div>
                    </div>

                    {/* Risk badge */}
                    <span className={`px-2 py-0.5 rounded text-xs font-medium border flex-shrink-0 ${risk.bg} ${risk.text} border-current/20`}>
                      {item.risk_level}
                    </span>

                    {/* Status badge */}
                    <span className={`px-2 py-0.5 rounded text-xs font-medium flex-shrink-0 ${STATUS_STYLES[effStatus] || STATUS_STYLES.OPEN}`}>
                      {effStatus.replace('_', ' ')}
                    </span>

                    {/* Deadline */}
                    <span className={`text-xs flex-shrink-0 w-[110px] text-right ${deadline.className}`}>
                      {deadline.text}
                    </span>
                  </div>
                </button>

                {/* Expanded detail */}
                {isExpanded && (
                  <div className={`border-l-[3px] ${risk.border} bg-black/40 border border-t-0 border-zinc-800 rounded-b-lg rounded-l-none px-6 py-5`}>
                    <div className="grid grid-cols-2 gap-6">
                      <div>
                        <div className="text-xs text-zinc-600 uppercase tracking-wider font-medium mb-2">Weakness</div>
                        <p className="text-sm text-zinc-300 leading-relaxed">{item.weakness_description || 'N/A'}</p>
                      </div>
                      <div>
                        <div className="text-xs text-zinc-600 uppercase tracking-wider font-medium mb-2">Remediation Plan</div>
                        <p className="text-sm text-zinc-300 leading-relaxed">{item.remediation_plan || 'No remediation plan documented.'}</p>
                      </div>
                    </div>

                    <div className="grid grid-cols-3 gap-6 mt-5 pt-5 border-t border-zinc-800">
                      <div>
                        <div className="text-xs text-zinc-600 uppercase tracking-wider font-medium mb-1.5">Status</div>
                        <span className={`px-2.5 py-1 rounded text-xs font-medium ${STATUS_STYLES[effStatus] || STATUS_STYLES.OPEN}`}>
                          {effStatus.replace('_', ' ')}
                        </span>
                      </div>
                      <div>
                        <div className="text-xs text-zinc-600 uppercase tracking-wider font-medium mb-1.5">Due Date</div>
                        <div className="text-sm text-zinc-300">
                          {item.scheduled_completion ? new Date(item.scheduled_completion).toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' }) : 'N/A'}
                        </div>
                        <div className={`text-xs mt-0.5 ${deadline.className}`}>{deadline.text}</div>
                      </div>
                      <div>
                        <div className="text-xs text-zinc-600 uppercase tracking-wider font-medium mb-1.5">Risk / Points</div>
                        <div className="flex items-center gap-2">
                          <span className={`px-2 py-0.5 rounded text-xs font-medium ${risk.bg} ${risk.text}`}>{item.risk_level}</span>
                          {item.points && <span className="text-sm text-zinc-400">{item.points} pts</span>}
                        </div>
                      </div>
                    </div>

                    {/* Milestones */}
                    {item.milestone_changes && (
                      <div className="mt-5 pt-5 border-t border-zinc-800">
                        <div className="text-xs text-zinc-600 uppercase tracking-wider font-medium mb-2">Milestones</div>
                        <div className="text-sm text-zinc-400">
                          {typeof item.milestone_changes === 'string' ? item.milestone_changes : JSON.stringify(item.milestone_changes, null, 2)}
                        </div>
                      </div>
                    )}

                    {/* Action */}
                    <div className="mt-5 pt-5 border-t border-zinc-800 flex justify-end">
                      <button onClick={() => navigate(`/ssp?control=${item.control_id}`)}
                        className="px-4 py-2 bg-zinc-800 hover:bg-zinc-700 rounded-lg text-sm text-zinc-300 transition-colors flex items-center gap-2">
                        View in SSP <ArrowRight className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      <div className="mt-4 text-xs text-zinc-600">Showing {sorted.length} of {items.length} items</div>
    </div>
  );
}
