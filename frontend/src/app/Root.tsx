import { Outlet, Link, useLocation, useNavigate } from 'react-router';
import { Home, FileText, Shield, AlertTriangle, FileCheck, Settings, ChevronRight } from 'lucide-react';

export function Root() {
  const location = useLocation();
  const navigate = useNavigate();

  const menuItems = [
    { icon: Home, label: 'Overview', path: '/' },
    { icon: FileText, label: 'SSP', path: '/ssp' },
    { icon: Shield, label: 'Evidence', path: '/evidence' },
    { icon: AlertTriangle, label: 'POA&M', path: '/poam' },
    { icon: FileCheck, label: 'Setup Wizard', path: '/intake' },
    { icon: Settings, label: 'Settings', path: '/settings' },
  ];

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
          <button
            onClick={() => navigate('/settings')}
            className="flex items-center gap-2 px-3 py-1.5 rounded-lg hover:bg-zinc-800 transition-colors group cursor-pointer"
          >
            <div className="w-7 h-7 rounded-full bg-zinc-800 border border-zinc-700 flex items-center justify-center text-xs font-medium text-zinc-400 group-hover:border-zinc-600">
              AD
            </div>
            <span className="text-sm text-zinc-500 group-hover:text-zinc-300 transition-colors">Apex Defense Solutions</span>
            <ChevronRight className="w-3.5 h-3.5 text-zinc-600 group-hover:text-zinc-400 transition-colors" />
          </button>
        </header>

        <div className="flex">
          {/* Sidebar */}
          <aside className="w-[220px] border-r border-zinc-800 bg-zinc-900/50 min-h-[calc(100vh-56px)] p-4">
            {/* Score Overview */}
            <div className="mb-6 pb-4 border-b border-zinc-800">
              <div className="text-xs text-zinc-600 uppercase tracking-wider mb-2">SPRS Score</div>
              <div className="flex items-end gap-2 mb-2">
                <div className="text-3xl font-medium text-zinc-100">63</div>
                <div className="text-sm text-zinc-600 pb-1">/ 110</div>
              </div>
              <div className="h-1 bg-zinc-800 rounded-full overflow-hidden">
                <div className="h-full bg-orange-400/80 rounded-full" style={{ width: '57%' }} />
              </div>
            </div>

            {/* Navigation */}
            <nav className="space-y-1">
              {menuItems.map((item) => {
                const isActive = location.pathname === item.path;
                return (
                  <Link
                    key={item.path}
                    to={item.path}
                    className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors text-sm ${
                      isActive
                        ? 'bg-zinc-800 text-zinc-200'
                        : 'text-zinc-500 hover:text-zinc-300 hover:bg-zinc-800/50'
                    }`}
                  >
                    <item.icon className="w-4 h-4" />
                    <span>{item.label}</span>
                  </Link>
                );
              })}
            </nav>

            {/* Footer */}
            <div className="mt-auto pt-6 border-t border-zinc-800">
              <div className="text-xs text-zinc-600">
                <button onClick={() => navigate('/settings')} className="font-medium text-zinc-500 hover:text-zinc-300 transition-colors mb-1 cursor-pointer">
                  Apex Defense
                </button>
                <div>Org ID: ADS-2026</div>
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
