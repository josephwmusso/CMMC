import { Outlet, Link, useLocation } from 'react-router';
import { useState } from 'react';

export function MarketingLayout() {
  const location = useLocation();
  const [mobileOpen, setMobileOpen] = useState(false);

  const navLinks = [
    { to: '/features', label: 'Features' },
    { to: '/pricing', label: 'Pricing' },
    { to: '/about', label: 'About' },
    { to: '/contact', label: 'Contact' },
  ];

  return (
    <div className="min-h-screen bg-[#0F172A] text-white" style={{ fontFamily: "'Inter', sans-serif" }}>
      {/* Navbar */}
      <nav className="fixed top-0 w-full z-50 border-b border-white/5 bg-[#0F172A]/90 backdrop-blur-md">
        <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-blue-500/10 border border-blue-500/20 flex items-center justify-center">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#3B82F6" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
            </div>
            <span className="text-lg font-semibold tracking-tight">INTRANEST</span>
          </Link>

          {/* Desktop nav */}
          <div className="hidden md:flex items-center gap-8">
            {navLinks.map(l => (
              <Link key={l.to} to={l.to}
                className={`text-sm transition-colors ${location.pathname === l.to ? 'text-white' : 'text-slate-400 hover:text-white'}`}>
                {l.label}
              </Link>
            ))}
          </div>

          <div className="hidden md:flex items-center gap-3">
            <Link to="/login" className="text-sm text-slate-400 hover:text-white transition-colors px-4 py-2">Sign in</Link>
            <Link to="/contact" className="text-sm font-medium bg-blue-600 hover:bg-blue-500 px-4 py-2 rounded-lg transition-colors">Request Demo</Link>
          </div>

          {/* Mobile hamburger */}
          <button onClick={() => setMobileOpen(!mobileOpen)} className="md:hidden p-2 text-slate-400">
            <svg width="24" height="24" fill="none" stroke="currentColor" strokeWidth="2"><path d={mobileOpen ? "M6 6l12 12M6 18L18 6" : "M4 8h16M4 16h16"} /></svg>
          </button>
        </div>

        {/* Mobile menu */}
        {mobileOpen && (
          <div className="md:hidden border-t border-white/5 bg-[#0F172A] px-6 py-4 space-y-3">
            {navLinks.map(l => (
              <Link key={l.to} to={l.to} onClick={() => setMobileOpen(false)}
                className="block text-sm text-slate-300 py-2">{l.label}</Link>
            ))}
            <Link to="/login" onClick={() => setMobileOpen(false)} className="block text-sm text-slate-300 py-2">Sign in</Link>
            <Link to="/contact" onClick={() => setMobileOpen(false)} className="block text-sm font-medium bg-blue-600 text-center py-2.5 rounded-lg mt-2">Request Demo</Link>
          </div>
        )}
      </nav>

      {/* Page content */}
      <main className="pt-16">
        <Outlet />
      </main>

      {/* Footer */}
      <footer className="border-t border-white/5 bg-[#0B1120]">
        <div className="max-w-6xl mx-auto px-6 py-12">
          <div className="flex flex-col md:flex-row justify-between items-start gap-8">
            <div>
              <Link to="/" className="flex items-center gap-2.5 mb-3">
                <div className="w-7 h-7 rounded-md bg-blue-500/10 border border-blue-500/20 flex items-center justify-center">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#3B82F6" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
                </div>
                <span className="text-sm font-semibold tracking-tight">INTRANEST</span>
              </Link>
              <p className="text-xs text-slate-500 max-w-xs">Sovereign CMMC Level 2 compliance platform for the Defense Industrial Base.</p>
            </div>
            <div className="flex gap-12">
              <div>
                <div className="text-xs font-medium text-slate-400 uppercase tracking-wider mb-3">Product</div>
                <div className="space-y-2">
                  <Link to="/features" className="block text-sm text-slate-500 hover:text-slate-300 transition-colors">Features</Link>
                  <Link to="/pricing" className="block text-sm text-slate-500 hover:text-slate-300 transition-colors">Pricing</Link>
                </div>
              </div>
              <div>
                <div className="text-xs font-medium text-slate-400 uppercase tracking-wider mb-3">Company</div>
                <div className="space-y-2">
                  <Link to="/about" className="block text-sm text-slate-500 hover:text-slate-300 transition-colors">About</Link>
                  <Link to="/contact" className="block text-sm text-slate-500 hover:text-slate-300 transition-colors">Contact</Link>
                </div>
              </div>
            </div>
          </div>
          <div className="mt-10 pt-6 border-t border-white/5 text-xs text-slate-600">
            &copy; {new Date().getFullYear()} Intranest, Inc. All rights reserved.
          </div>
        </div>
      </footer>
    </div>
  );
}
