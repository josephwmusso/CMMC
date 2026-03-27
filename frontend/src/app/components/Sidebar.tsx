import { Home, FileText, Settings, Armchair, Tag, Puzzle, Users, ChevronRight, CalendarDays, Shield, AlertTriangle } from 'lucide-react';
import { motion } from 'motion/react';

interface SidebarProps {
  isOpen: boolean;
}

export function Sidebar({ isOpen }: SidebarProps) {
  const menuItems = [
    { icon: Home, label: 'Overview', active: true },
    { icon: FileText, label: 'SSP' },
    { icon: Shield, label: 'Evidence' },
    { icon: AlertTriangle, label: 'POA&M' },
    { icon: Users, label: 'Setup Wizard' },
    { icon: Settings, label: 'Settings' },
  ];

  return (
    <aside className="w-[220px] border-r border-zinc-800/30 bg-zinc-900/30 backdrop-blur-sm min-h-[calc(100vh-72px)] p-6">
      {/* Assessment Info */}
      <div className="mb-8 pb-6 border-b border-zinc-800/30">
        <div className="mb-3">
          <h2 className="text-sm font-medium mb-1 text-zinc-300">NIST CSF 2.0</h2>
          <p className="text-xs text-zinc-600">Last updated 2 days ago</p>
        </div>
        <div className="flex items-center gap-2">
          <div className="flex-1 h-1 bg-zinc-800/50 rounded-full overflow-hidden">
            <div className="h-full bg-[#2563eb]/70 rounded-full" style={{ width: '78%' }} />
          </div>
          <span className="text-xs text-zinc-500">78</span>
        </div>
      </div>

      {/* Main Navigation */}
      <nav className="space-y-1 mb-auto">
        {menuItems.map((item) => (
          <motion.button
            key={item.label}
            whileHover={{ x: 2 }}
            whileTap={{ scale: 0.98 }}
            className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors text-sm ${
              item.active
                ? 'bg-zinc-800/50 text-zinc-200'
                : 'text-zinc-500 hover:text-zinc-300 hover:bg-zinc-800/30'
            }`}
          >
            <item.icon className="w-4 h-4" />
            <span className="font-normal">{item.label}</span>
          </motion.button>
        ))}
      </nav>

      {/* Sidebar Footer */}
      <div className="mt-auto pt-6 border-t border-zinc-800/30">
        <div className="text-xs text-zinc-600">
          <div className="font-medium text-zinc-500 mb-1">Apex Defense Solutions</div>
          <div>Org ID: ADS-2026</div>
          <div className="mt-2 opacity-50">v1.0.0</div>
        </div>
      </div>
    </aside>
  );
}