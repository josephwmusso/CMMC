import { ChevronLeft, ChevronRight, AlertTriangle } from 'lucide-react';
import { useState } from 'react';

export function Intake() {
  const [selectedAnswer, setSelectedAnswer] = useState<number | null>(null);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);

  const sections = [
    { id: 1, name: 'Company Information', complete: true },
    { id: 2, name: 'Layered & CUI Scoping', complete: true },
    { id: 3, name: 'Environment Scoping', complete: true },
    { id: 4, name: 'Technology Stack', complete: true },
    { id: 5, name: 'Existing Compliance', complete: false },
    { id: 6, name: 'Account Management', complete: false, active: true },
    { id: 7, name: 'Login Details', complete: false },
    { id: 8, name: 'Remote Access', complete: false },
  ];

  const answers = [
    { 
      id: 1, 
      text: 'Formal request and approval process (e.g., ticketing system, manager sign-off)', 
      severity: null 
    },
    { 
      id: 2, 
      text: 'Manager sends email or verbal request to IT', 
      severity: null 
    },
    { 
      id: 3, 
      text: 'IT creates accounts as needed without formal approval', 
      severity: 'HIGH' 
    },
    { 
      id: 4, 
      text: 'Users can self-register or create their own accounts', 
      severity: 'CRITICAL' 
    },
  ];

  return (
    <div className="flex h-[calc(100vh-56px)]">
      {/* Left Sidebar - Progress */}
      <aside className="w-64 border-r border-zinc-800 bg-zinc-900/30 p-4 overflow-y-auto">
        <div className="mb-6">
          <div className="text-xs text-zinc-600 uppercase tracking-wider mb-2">Foundation</div>
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-zinc-400">COMPLETE</span>
            <span className="px-2 py-0.5 bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 rounded text-xs font-medium">
              100%
            </span>
          </div>
        </div>

        <div className="space-y-1">
          {sections.map((section) => (
            <button
              key={section.id}
              className={`w-full flex items-center justify-between px-3 py-2.5 rounded-lg transition-colors text-left ${
                section.active
                  ? 'bg-blue-500/80 text-white'
                  : section.complete
                  ? 'text-zinc-500 hover:bg-zinc-800/50'
                  : 'text-zinc-600 hover:bg-zinc-800/50'
              }`}
            >
              <span className="text-sm">{section.name}</span>
              {section.complete && !section.active && (
                <span className="text-xs">✓</span>
              )}
            </button>
          ))}
        </div>

        <div className="mt-6 pt-6 border-t border-zinc-800">
          <div className="text-xs text-zinc-600 mb-2">Overall Progress</div>
          <div className="h-1.5 bg-zinc-800 rounded-full overflow-hidden mb-2">
            <div className="h-full bg-blue-500/80 rounded-full" style={{ width: '62%' }} />
          </div>
          <div className="text-xs text-zinc-500">5 of 28 answered</div>
        </div>
      </aside>

      {/* Main Content */}
      <div className="flex-1 overflow-y-auto bg-black">
        <div className="w-full max-w-4xl mx-auto p-12">
          {/* Progress Indicator */}
          <div className="text-center mb-8">
            <div className="text-sm text-zinc-500 mb-3">6 of 28 answered</div>
            <div className="h-1 bg-zinc-800 rounded-full overflow-hidden max-w-md mx-auto">
              <div className="h-full bg-blue-500/80 rounded-full" style={{ width: '21%' }} />
            </div>
          </div>

          {/* Question Card */}
          <div className="bg-zinc-900/50 border border-zinc-800 rounded-xl p-8 mb-6">
            {/* Section Badge */}
            <div className="mb-6">
              <span className="px-3 py-1 bg-zinc-800 text-zinc-400 border border-zinc-700 rounded-full text-xs font-medium uppercase tracking-wider">
                Account Management
              </span>
            </div>

            {/* Question Number and Navigation */}
            <div className="flex items-center justify-between mb-4">
              <div className="text-xs text-zinc-600">Question {currentQuestionIndex + 1} of 4</div>
            </div>

            {/* Tooltip/Help */}
            <div className="flex items-start gap-2 mb-8 p-4 bg-zinc-800/30 rounded-lg">
              <div className="w-5 h-5 rounded-full bg-zinc-700 flex items-center justify-center flex-shrink-0 mt-0.5">
                <span className="text-xs text-zinc-400">?</span>
              </div>
              <p className="text-sm text-zinc-400">
                Why we ask this: This control verifies that your organization has a formal process for authorizing new user accounts on systems handling CUI.
              </p>
            </div>

            {/* Control IDs */}
            <div className="flex items-center gap-2 mb-6">
              <span className="text-xs text-zinc-600">Relates to:</span>
              <span className="px-2 py-0.5 bg-zinc-800 text-zinc-500 rounded text-xs font-mono">AC.L2-3.1.1</span>
              <span className="px-2 py-0.5 bg-zinc-800 text-zinc-500 rounded text-xs font-mono">IA.L2-3.5.1</span>
            </div>

            {/* Answer Options */}
            <div className="space-y-3">
              {answers.map((answer) => (
                <button
                  key={answer.id}
                  onClick={() => setSelectedAnswer(answer.id)}
                  className={`w-full p-5 rounded-lg border-2 transition-all text-left ${
                    selectedAnswer === answer.id
                      ? 'border-blue-500/80 bg-blue-500/5'
                      : 'border-zinc-800 hover:border-zinc-700 bg-black/50'
                  }`}
                >
                  <div className="flex items-start gap-4">
                    <div className={`w-5 h-5 rounded-full border-2 flex items-center justify-center flex-shrink-0 mt-0.5 ${
                      selectedAnswer === answer.id
                        ? 'border-blue-500/80 bg-blue-500/80'
                        : 'border-zinc-700'
                    }`}>
                      {selectedAnswer === answer.id && (
                        <div className="w-2 h-2 rounded-full bg-white" />
                      )}
                    </div>
                    
                    <div className="flex-1">
                      <p className="text-sm text-zinc-300 mb-2">{answer.text}</p>
                      {answer.severity && (
                        <span className={`inline-block px-2 py-0.5 rounded text-xs font-medium ${
                          answer.severity === 'CRITICAL'
                            ? 'bg-red-500/10 text-red-400 border border-red-500/20'
                            : 'bg-orange-500/10 text-orange-400 border border-orange-500/20'
                        }`}>
                          {answer.severity}
                        </span>
                      )}
                    </div>
                  </div>
                </button>
              ))}
            </div>

            {/* Alert for Gap-Triggering Answer */}
            {selectedAnswer === 4 && (
              <div className="mt-6 p-4 bg-red-500/5 border border-red-500/20 rounded-lg">
                <div className="flex items-start gap-3">
                  <AlertTriangle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
                  <div>
                    <div className="text-sm font-medium text-red-400 mb-1">Critical Gap Identified</div>
                    <p className="text-sm text-zinc-400">
                      Self-registration without approval creates a critical compliance gap. You'll need to implement a formal account approval process and document it in your SSP.
                    </p>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Navigation */}
          <div className="flex items-center justify-between">
            <button className="px-6 py-3 bg-zinc-800 hover:bg-zinc-700 rounded-lg text-sm text-zinc-300 transition-colors flex items-center gap-2">
              <ChevronLeft className="w-4 h-4" />
              Previous
            </button>
            
            <span className="text-sm text-zinc-600">Question 6 of 28</span>
            
            <button 
              className="px-6 py-3 bg-blue-500/80 hover:bg-blue-500 rounded-lg text-sm font-medium text-white transition-colors flex items-center gap-2"
              disabled={selectedAnswer === null}
            >
              Next
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}