import { Outlet, Link, useLocation, useNavigate, Navigate } from 'react-router';
import { Home, FileText, Shield, AlertTriangle, FileCheck, Settings, ChevronRight, LogOut, Loader2 } from 'lucide-react';
import { useState, useEffect } from 'react';
import { getComplianceOverview, listArtifacts, getPoamSummary } from './api/client';
import { useAuth } from './context/AuthContext';

export function Root() {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, loading, logout } = useAuth();
  const [sprsScore, setSprsScore] = useState<number | null>(null);
  const [sprsTotal, setSprsTotal] = useState(110);
  const [orgName, setOrgName] = useState('');

  // Workflow status — drives the sidebar status dots
  const [hasSsp, setHasSsp] = useState(false);
  const [hasEvidence, setHasEvidence] = useState(false);
  const [hasPoam, setHasPoam] = useState(false);
  const [evidenceCount, setEvidenceCount] = useState(0);
  const [sspMet, setSspMet] = useState(0);
  const [poamCount, setPoamCount] = useState(0);
  const [statusLoaded, setStatusLoaded] = useState(false);

  useEffect(() => {
    if (!user) return;
    let cancelled = false;
    Promise.all([
      getComplianceOverview().catch(() => null),
      listArtifacts(null, 1).catch(() => null),
      getPoamSummary().catch(() => null),
    ]).then(([overview, artifacts, poam]) => {
      if (cancelled) return;
      // Overview / SPRS
      if (overview) {
        setSprsScore(overview.sprs?.score ?? null);
        setSprsTotal(overview.sprs?.total ?? 110);
        setOrgName(overview.sprs?.org_name || 'Apex Defense Solutions');
        const met = overview.sprs?.met ?? 0;
        const partial = overview.sprs?.partial ?? 0;
        setHasSsp((met + partial) > 0);
        setSspMet(met + partial);
      }
      // Evidence
      if (artifacts) {
        const count = (artifacts.artifacts?.length ?? artifacts.count ?? 0);
        setHasEvidence(count > 0);
        setEvidenceCount(count);
      }
      // POA&M
      if (poam) {
        const items = poam.items || [];
        setHasPoam(items.length > 0);
        setPoamCount(items.length);
      }
      setStatusLoaded(true);
    });
    return () => { cancelled = true; };
  }, [user, location.pathname]);

  // Intake is "done" if evidence has been generated/uploaded OR SSP sections exist
  // (both are downstream effects of completing intake)
  const hasIntake = hasEvidence || hasSsp;

  // Workflow next-step: which page should the user visit next?
  const nextStep: string = !hasIntake ? 'intake'
    : !hasEvidence ? 'evidence'
    : !hasSsp ? 'ssp'
    : !hasPoam ? 'poam'
    : 'overview';

  type MenuItem = {
    icon: typeof Home;
    label: string;
    path: string;
    key: string;
    hasData: boolean;
    count: number;
    skipDot?: boolean;
  };

  const menuItems: MenuItem[] = [
    { icon: Home, label: 'Overview', path: '/app', key: 'overview', hasData: hasSsp, count: sspMet },
    { icon: FileText, label: 'SSP', path: '/app/ssp', key: 'ssp', hasData: hasSsp, count: sspMet },
    { icon: Shield, label: 'Evidence', path: '/app/evidence', key: 'evidence', hasData: hasEvidence, count: evidenceCount },
    { icon: AlertTriangle, label: 'POA&M', path: '/app/poam', key: 'poam', hasData: hasPoam, count: poamCount },
    { icon: FileCheck, label: 'Setup Wizard', path: '/app/intake', key: 'intake', hasData: hasIntake, count: 0 },
    { icon: Settings, label: 'Settings', path: '/app/settings', key: 'settings', hasData: false, count: 0, skipDot: true },
  ];

  // Protect /app/* routes — after all hooks
  if (loading) return <div className="min-h-screen bg-black flex items-center justify-center"><Loader2 className="w-6 h-6 text-zinc-500 animate-spin" /></div>;
  if (!user) return <Navigate to="/login" replace />;

  return (
    <div className="min-h-screen bg-black">
        {/* Header */}
        <header className="h-14 border-b border-zinc-800 bg-zinc-900/80 backdrop-blur-sm flex items-center justify-between px-6">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-zinc-800 flex items-center justify-center">
              <Shield className="w-5 h-5 text-zinc-500" />
            </div>
            <h1 className="text-lg font-semibold text-zinc-100 tracking-tight" style={{ fontFamily: 'Space Grotesk, sans-serif' }}>INTRANEST</h1>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={() => navigate('/app/settings')}
              className="flex items-center gap-2 px-3 py-1.5 rounded-lg hover:bg-zinc-800 transition-colors group cursor-pointer"
            >
              <div className="w-7 h-7 rounded-full bg-zinc-800 border border-zinc-700 flex items-center justify-center text-xs font-medium text-zinc-400 group-hover:border-zinc-600">
                {(user?.full_name || user?.email || '?')[0].toUpperCase()}
              </div>
              <span className="text-sm text-zinc-500 group-hover:text-zinc-300 transition-colors">{user?.email || orgName || 'Loading...'}</span>
              <ChevronRight className="w-3.5 h-3.5 text-zinc-600 group-hover:text-zinc-400 transition-colors" />
            </button>
            <button onClick={logout} className="p-1.5 rounded-lg hover:bg-zinc-800 transition-colors" title="Sign out">
              <LogOut className="w-4 h-4 text-zinc-600 hover:text-zinc-400" />
            </button>
          </div>
        </header>

        <div className="flex">
          {/* Sidebar */}
          <aside className="w-[220px] border-r border-zinc-800 bg-zinc-900/50 min-h-[calc(100vh-56px)] p-4">
            {/* Score Overview */}
            <div className="mb-6 pb-4 border-b border-zinc-800">
              <div className="text-xs text-zinc-600 uppercase tracking-wider mb-2">SPRS Score</div>
              <div className="flex items-end gap-2 mb-2">
                <div className="text-3xl font-medium text-zinc-100">{sprsScore ?? '—'}</div>
                <div className="text-sm text-zinc-600 pb-1">/ {sprsTotal}</div>
              </div>
              <div className="h-1 bg-zinc-800 rounded-full overflow-hidden">
                <div className="h-full rounded-full transition-all" style={{
                  width: sprsScore !== null ? `${Math.max(0, ((sprsScore + 203) / 313) * 100)}%` : '0%',
                  background: sprsScore !== null && sprsScore >= 88 ? '#34d399' : sprsScore !== null && sprsScore >= 50 ? '#fb923c' : '#ef4444',
                }} />
              </div>
            </div>

            {/* Navigation */}
            <nav className="space-y-1">
              {menuItems.map((item) => {
                const isActive = location.pathname === item.path;
                // Status dot logic:
                //   - skipDot: never show (Settings)
                //   - !statusLoaded: hide until data arrives (no flash of wrong state)
                //   - nextStep match: pulsing teal "go here next" indicator
                //   - hasData: solid emerald "complete/has data" dot
                //   - else: no dot
                const isNext = statusLoaded && !item.skipDot && item.key === nextStep && !item.hasData;
                const showGreen = statusLoaded && !item.skipDot && item.hasData;
                const tooltip = isNext
                  ? 'Recommended next step'
                  : showGreen && item.count > 0
                    ? `${item.count} ${item.key === 'evidence' ? 'artifacts' : item.key === 'poam' ? 'items' : item.key === 'ssp' || item.key === 'overview' ? 'sections generated' : 'complete'}`
                    : showGreen ? 'Complete' : undefined;
                return (
                  <Link
                    key={item.path}
                    to={item.path}
                    title={tooltip}
                    className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors text-sm ${
                      isActive
                        ? 'bg-zinc-800 text-zinc-200'
                        : 'text-zinc-500 hover:text-zinc-300 hover:bg-zinc-800/50'
                    }`}
                  >
                    <item.icon className="w-4 h-4" />
                    <span className="flex-1">{item.label}</span>
                    {isNext && (
                      <span className="relative flex w-2 h-2" aria-label="Recommended next step">
                        <span className="absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-60 animate-ping" />
                        <span className="relative inline-flex w-2 h-2 rounded-full bg-blue-400" />
                      </span>
                    )}
                    {showGreen && (
                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-400/80" aria-label="Has data" />
                    )}
                  </Link>
                );
              })}
            </nav>

            {/* Footer */}
            <div className="mt-auto pt-6 border-t border-zinc-800">
              <div className="text-xs text-zinc-600">
                <button onClick={() => navigate('/app/settings')} className="font-medium text-zinc-500 hover:text-zinc-300 transition-colors mb-1 cursor-pointer">
                  {orgName || 'Organization'}
                </button>
                <div>CMMC Level 2</div>
                <div className="mt-2 opacity-50">v0.9.0</div>
              </div>
            </div>
          </aside>

          {/* Main Content */}
          <main className="flex-1">
            <Outlet />
          </main>
        </div>
      </div>
  );
}
