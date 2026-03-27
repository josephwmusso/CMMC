import { AlertTriangle, Upload, FileCheck, ArrowRight, CheckCircle2, Shield, FileText, Clock, AlertCircle } from 'lucide-react';

export function DashboardContent() {
  return (
    <div className="p-6 w-full">
      
      {/* Top Row: Score + Quick Stats */}
      <div className="grid grid-cols-12 gap-4 mb-6">
        
        {/* Score */}
        <div className="col-span-4">
          <div className="bg-zinc-900/30 border border-zinc-800/30 rounded-xl p-5">
            <div className="text-xs text-zinc-600 uppercase tracking-wider mb-3">Compliance Score</div>
            <div className="flex items-end gap-3 mb-3">
              <div className="text-5xl font-medium text-zinc-100">78</div>
              <div className="pb-2 text-zinc-500 text-sm">/ 110</div>
            </div>
            <div className="h-1.5 bg-zinc-800/50 rounded-full overflow-hidden mb-2">
              <div className="h-full bg-[#ea580c] rounded-full" style={{ width: '71%' }} />
            </div>
            <div className="text-xs text-zinc-500">Target: 95+ for certification</div>
          </div>
        </div>

        {/* Quick Stats */}
        <div className="col-span-8 grid grid-cols-4 gap-4">
          <div className="bg-zinc-900/30 border border-zinc-800/30 rounded-xl p-4">
            <div className="flex items-center gap-2 mb-2">
              <Shield className="w-3.5 h-3.5 text-zinc-600" />
              <div className="text-xs text-zinc-600">Controls</div>
            </div>
            <div className="text-2xl font-medium text-zinc-100">284</div>
            <div className="text-xs text-zinc-600 mt-0.5">of 380</div>
          </div>

          <div className="bg-zinc-900/30 border border-zinc-800/30 rounded-xl p-4">
            <div className="flex items-center gap-2 mb-2">
              <FileText className="w-3.5 h-3.5 text-zinc-600" />
              <div className="text-xs text-zinc-600">Evidence</div>
            </div>
            <div className="text-2xl font-medium text-zinc-100">26</div>
            <div className="text-xs text-zinc-600 mt-0.5">published</div>
          </div>

          <div className="bg-zinc-900/30 border border-zinc-800/30 rounded-xl p-4">
            <div className="flex items-center gap-2 mb-2">
              <AlertCircle className="w-3.5 h-3.5 text-zinc-600" />
              <div className="text-xs text-zinc-600">POA&M</div>
            </div>
            <div className="text-2xl font-medium text-zinc-100">37</div>
            <div className="text-xs text-[#dc2626] mt-0.5">5 overdue</div>
          </div>

          <div className="bg-zinc-900/30 border border-zinc-800/30 rounded-xl p-4">
            <div className="flex items-center gap-2 mb-2">
              <Clock className="w-3.5 h-3.5 text-zinc-600" />
              <div className="text-xs text-zinc-600">Audit</div>
            </div>
            <div className="text-2xl font-medium text-zinc-100">145</div>
            <div className="text-xs text-zinc-600 mt-0.5">entries</div>
          </div>
        </div>
      </div>

      {/* Main Content: Actions + Activity */}
      <div className="grid grid-cols-12 gap-6">
        
        {/* Left: Priority Actions */}
        <div className="col-span-8">
          <h2 className="text-base font-medium text-zinc-200 mb-4">What needs your attention</h2>
          
          <div className="space-y-2">
            {/* Action 1 - Urgent */}
            <button className="w-full bg-zinc-900/30 border border-zinc-800/30 hover:border-zinc-700/50 rounded-lg p-4 text-left transition-all group">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg bg-[#dc2626]/10 border border-[#dc2626]/20 flex items-center justify-center flex-shrink-0">
                  <AlertTriangle className="w-4 h-4 text-[#dc2626]" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <h3 className="text-sm font-medium text-zinc-200">2 controls overdue</h3>
                    <span className="px-1.5 py-0.5 bg-[#dc2626]/10 border border-[#dc2626]/20 rounded text-xs font-medium text-[#dc2626]">URGENT</span>
                  </div>
                  <div className="flex items-center gap-2 text-xs text-zinc-600">
                    <span className="font-mono text-zinc-500">AC-2</span>
                    <span className="font-mono text-zinc-500">IR-4</span>
                    <span>• 2 days overdue</span>
                  </div>
                </div>
                <ArrowRight className="w-4 h-4 text-zinc-600 group-hover:text-zinc-400 transition-colors" />
              </div>
            </button>

            {/* Action 2 - High Priority */}
            <button className="w-full bg-zinc-900/30 border border-zinc-800/30 hover:border-zinc-700/50 rounded-lg p-4 text-left transition-all group">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg bg-[#ea580c]/10 border border-[#ea580c]/20 flex items-center justify-center flex-shrink-0">
                  <Upload className="w-4 h-4 text-[#ea580c]" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <h3 className="text-sm font-medium text-zinc-200">3 controls need evidence</h3>
                    <span className="text-xs text-zinc-500">Due tomorrow</span>
                  </div>
                  <div className="flex items-center gap-2 text-xs text-zinc-600">
                    <span className="font-mono text-zinc-500">SC-7</span>
                    <span className="font-mono text-zinc-500">AU-6</span>
                    <span className="font-mono text-zinc-500">CP-9</span>
                  </div>
                </div>
                <ArrowRight className="w-4 h-4 text-zinc-600 group-hover:text-zinc-400 transition-colors" />
              </div>
            </button>

            {/* Action 3 - Important */}
            <button className="w-full bg-zinc-900/30 border border-zinc-800/30 hover:border-zinc-700/50 rounded-lg p-4 text-left transition-all group">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg bg-[#2563eb]/10 border border-[#2563eb]/20 flex items-center justify-center flex-shrink-0">
                  <FileCheck className="w-4 h-4 text-[#2563eb]" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <h3 className="text-sm font-medium text-zinc-200">18 assessment questions left</h3>
                    <span className="text-xs text-zinc-500">~30 min</span>
                  </div>
                  <div className="text-xs text-zinc-600">Complete questionnaire to increase score by up to 12 points</div>
                </div>
                <ArrowRight className="w-4 h-4 text-zinc-600 group-hover:text-zinc-400 transition-colors" />
              </div>
            </button>

            {/* Action 4 - Review */}
            <button className="w-full bg-zinc-900/30 border border-zinc-800/30 hover:border-zinc-700/50 rounded-lg p-4 text-left transition-all group">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg bg-[#7c3aed]/10 border border-[#7c3aed]/20 flex items-center justify-center flex-shrink-0">
                  <CheckCircle2 className="w-4 h-4 text-[#7c3aed]" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <h3 className="text-sm font-medium text-zinc-200">5 POA&M items need review</h3>
                    <span className="text-xs text-zinc-500">Due this week</span>
                  </div>
                  <div className="text-xs text-zinc-600">Review remediation plans and update status</div>
                </div>
                <ArrowRight className="w-4 h-4 text-zinc-600 group-hover:text-zinc-400 transition-colors" />
              </div>
            </button>

            <button className="w-full mt-2 py-2 text-sm text-zinc-500 hover:text-zinc-300 transition-colors">
              View all tasks (42) →
            </button>
          </div>
        </div>

        {/* Right: Recent Activity */}
        <div className="col-span-4">
          <h3 className="text-sm font-medium text-zinc-400 mb-4">Recent activity</h3>
          <div className="space-y-3">
            <div className="flex items-start gap-2.5 text-sm">
              <div className="w-2 h-2 rounded-full bg-[#16a34a] mt-1.5 flex-shrink-0" />
              <div className="flex-1 min-w-0">
                <p className="text-zinc-500">J. Mitchell completed <span className="text-zinc-400 font-medium">IA-5</span></p>
                <span className="text-zinc-600 text-xs">2h ago</span>
              </div>
            </div>
            
            <div className="flex items-start gap-2.5 text-sm">
              <div className="w-2 h-2 rounded-full bg-[#2563eb] mt-1.5 flex-shrink-0" />
              <div className="flex-1 min-w-0">
                <p className="text-zinc-500">S. Chen uploaded evidence for <span className="text-zinc-400 font-medium">SC-7</span></p>
                <span className="text-zinc-600 text-xs">5h ago</span>
              </div>
            </div>
            
            <div className="flex items-start gap-2.5 text-sm">
              <div className="w-2 h-2 rounded-full bg-[#ea580c] mt-1.5 flex-shrink-0" />
              <div className="flex-1 min-w-0">
                <p className="text-zinc-500">IR-4 deadline extended to Mar 28</p>
                <span className="text-zinc-600 text-xs">1d ago</span>
              </div>
            </div>
            
            <div className="flex items-start gap-2.5 text-sm">
              <div className="w-2 h-2 rounded-full bg-zinc-600 mt-1.5 flex-shrink-0" />
              <div className="flex-1 min-w-0">
                <p className="text-zinc-500">M. Rodriguez started POA&M review</p>
                <span className="text-zinc-600 text-xs">2d ago</span>
              </div>
            </div>

            <div className="flex items-start gap-2.5 text-sm">
              <div className="w-2 h-2 rounded-full bg-[#16a34a] mt-1.5 flex-shrink-0" />
              <div className="flex-1 min-w-0">
                <p className="text-zinc-500">Evidence verified for <span className="text-zinc-400 font-medium">CM-7</span></p>
                <span className="text-zinc-600 text-xs">2d ago</span>
              </div>
            </div>
          </div>
        </div>

      </div>

    </div>
  );
}
