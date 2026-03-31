import { Outlet, Link, useLocation } from 'react-router';
import { useState, useEffect } from 'react';

export function MarketingLayout() {
  const location = useLocation();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 10);
    window.addEventListener('scroll', onScroll);
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  useEffect(() => { setMobileOpen(false); }, [location.pathname]);

  const navLinks = [
    { to: '/features', label: 'Features' },
    { to: '/pricing', label: 'Pricing' },
    { to: '/about', label: 'About' },
    { to: '/contact', label: 'Contact' },
  ];

  return (
    <div className="min-h-screen bg-black text-zinc-100">
      {/* Navbar — matches Root.tsx header pattern */}
      <nav className={`fixed top-0 w-full z-50 h-14 flex items-center justify-between px-6 border-b transition-colors ${scrolled ? 'bg-zinc-900/80 backdrop-blur-sm border-zinc-800' : 'bg-transparent border-transparent'}`}>
        <Link to="/" className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-zinc-800 flex items-center justify-center">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#71717a" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
          </div>
          <span className="text-lg font-semibold text-zinc-100 tracking-tight" style={{ fontFamily: 'Space Grotesk, sans-serif' }}>INTRANEST</span>
        </Link>

        {/* Desktop nav */}
        <div className="hidden md:flex items-center gap-6">
          {navLinks.map(l => (
            <Link key={l.to} to={l.to}
              className={`text-sm transition-colors ${location.pathname === l.to ? 'text-zinc-200' : 'text-zinc-500 hover:text-zinc-300'}`}>
              {l.label}
            </Link>
          ))}
        </div>

        <div className="hidden md:flex items-center gap-3">
          <Link to="/login" className="text-sm text-zinc-500 hover:text-zinc-300 transition-colors px-3 py-1.5">Sign in</Link>
          <Link to="/contact" className="text-sm font-medium bg-blue-500/80 hover:bg-blue-500 px-4 py-2 rounded-lg text-white transition-colors">Request Demo</Link>
        </div>

        {/* Mobile hamburger */}
        <button onClick={() => setMobileOpen(!mobileOpen)} className="md:hidden p-2 text-zinc-500">
          <svg width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2"><path d={mobileOpen ? "M4 4l12 12M4 16L16 4" : "M2 6h16M2 12h16"} /></svg>
        </button>
      </nav>

      {/* Mobile menu */}
      {mobileOpen && (
        <div className="fixed inset-0 z-40 pt-14 bg-black/95 backdrop-blur-sm md:hidden">
          <div className="p-6 space-y-1">
            {navLinks.map(l => (
              <Link key={l.to} to={l.to}
                className="block px-3 py-2.5 rounded-lg text-sm text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800/50 transition-colors">{l.label}</Link>
            ))}
            <Link to="/login" className="block px-3 py-2.5 rounded-lg text-sm text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800/50 transition-colors">Sign in</Link>
            <Link to="/contact" className="block mt-3 text-center px-4 py-2.5 bg-blue-500/80 rounded-lg text-sm font-medium text-white">Request Demo</Link>
          </div>
        </div>
      )}

      {/* Page content */}
      <main className="pt-14">
        <Outlet />
      </main>

      {/* Footer — matches platform muted style */}
      <footer className="border-t border-zinc-800">
        <div className="max-w-5xl mx-auto px-6 py-10">
          <div className="flex flex-col md:flex-row justify-between items-start gap-8">
            <div>
              <Link to="/" className="flex items-center gap-2 mb-3">
                <div className="w-6 h-6 rounded-md bg-zinc-800 flex items-center justify-center">
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#52525b" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
                </div>
                <span className="text-sm font-semibold text-zinc-500 tracking-tight" style={{ fontFamily: 'Space Grotesk, sans-serif' }}>INTRANEST</span>
              </Link>
              <p className="text-xs text-zinc-600 max-w-xs">Sovereign CMMC Level 2 compliance platform for the Defense Industrial Base.</p>
            </div>
            <div className="flex gap-10">
              <div>
                <div className="text-xs text-zinc-600 uppercase tracking-wider mb-2">Product</div>
                <div className="space-y-1.5">
                  <Link to="/features" className="block text-sm text-zinc-500 hover:text-zinc-300 transition-colors">Features</Link>
                  <Link to="/pricing" className="block text-sm text-zinc-500 hover:text-zinc-300 transition-colors">Pricing</Link>
                </div>
              </div>
              <div>
                <div className="text-xs text-zinc-600 uppercase tracking-wider mb-2">Company</div>
                <div className="space-y-1.5">
                  <Link to="/about" className="block text-sm text-zinc-500 hover:text-zinc-300 transition-colors">About</Link>
                  <Link to="/contact" className="block text-sm text-zinc-500 hover:text-zinc-300 transition-colors">Contact</Link>
                </div>
              </div>
            </div>
          </div>
          <div className="mt-8 pt-6 border-t border-zinc-800/50 text-xs text-zinc-700">
            &copy; {new Date().getFullYear()} Intranest, Inc. All rights reserved.
          </div>
        </div>
      </footer>
    </div>
  );
}
