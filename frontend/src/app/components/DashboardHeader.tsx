import { Plus, ChevronDown } from 'lucide-react';

export function DashboardHeader() {
  return (
    <header className="h-[72px] border-b border-zinc-800/30 bg-zinc-900/30 backdrop-blur-xl sticky top-0 z-50">
      <div className="flex items-center justify-between h-full px-8">
        <div className="flex items-center gap-8">
          {/* Logo */}
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-zinc-800 rounded-xl flex items-center justify-center">
              <svg className="w-6 h-6 text-zinc-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </div>
            <div>
              <div className="text-lg font-bold tracking-tight text-zinc-200">NIST Compliance</div>
              <div className="text-[10px] text-zinc-600 uppercase tracking-wider">Security Dashboard</div>
            </div>
          </div>

          {/* Create Assessment Button */}
          <button className="flex items-center gap-2 px-4 py-2.5 bg-[#2563eb] hover:bg-[#1d4ed8] rounded-lg transition-all border border-[#1d4ed8]/30">
            <Plus className="w-4 h-4" />
            <span className="text-sm font-medium">New Assessment</span>
          </button>

          {/* Navigation Links */}
          <nav className="flex items-center gap-6">
            <a href="#" className="text-sm font-medium text-zinc-500 hover:text-zinc-300 transition-colors">
              Assessments
            </a>
            <a href="#" className="text-sm font-medium text-zinc-500 hover:text-zinc-300 transition-colors">
              Reports
            </a>
          </nav>
        </div>

        {/* Organization Dropdown */}
        <button className="flex items-center gap-2 px-4 py-2.5 bg-zinc-800/50 rounded-lg hover:bg-zinc-800 transition-colors border border-zinc-700/30">
          <span className="text-sm font-medium text-zinc-300">Organization name</span>
          <ChevronDown className="w-4 h-4 text-zinc-500" />
        </button>
      </div>
    </header>
  );
}