import { ChevronLeft, ChevronRight, AlertTriangle, Check, Building2, Shield, Server, Loader2, HelpCircle } from 'lucide-react';
import { useState, useEffect, useCallback } from 'react';
import { createIntakeSession, getIntakeModule, saveIntakeResponses } from '../api/client';

const MODULES = [
  { id: 0, label: 'Foundation', icon: Building2 },
  { id: 1, label: 'Access Control', icon: Shield },
];

export function SetupWizard() {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [activeModule, setActiveModule] = useState(0);
  const [moduleData, setModuleData] = useState<Record<number, any>>({});
  const [currentIdx, setCurrentIdx] = useState(0);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [showHelp, setShowHelp] = useState(false);
  const [completed, setCompleted] = useState(false);
  const [flags, setFlags] = useState<any[]>([]);
  const [progress, setProgress] = useState({ answered: 0, gaps: 0 });

  const questions = moduleData[activeModule]?.questions || [];
  const answers = moduleData[activeModule]?.answers || {};

  useEffect(() => {
    async function init() {
      try {
        const sess = await createIntakeSession();
        setSessionId(sess.session_id);
        await loadModule(sess.session_id, 0);
      } catch (e) { console.error('Failed to init intake:', e); }
      finally { setLoading(false); }
    }
    init();
  }, []);

  const loadModule = async (sid: string, moduleId: number) => {
    const mod = await getIntakeModule(sid, moduleId);
    const existing: Record<string, string> = {};
    (mod.questions || []).forEach((q: any) => { if (q.current_answer) existing[q.id] = q.current_answer.answer_value; });
    setModuleData(prev => ({ ...prev, [moduleId]: { questions: mod.questions || [], info: mod, answers: existing } }));
  };

  const switchModule = async (moduleId: number) => {
    setCompleted(false); setCurrentIdx(0); setShowHelp(false); setActiveModule(moduleId);
    if (!moduleData[moduleId] && sessionId) { setLoading(true); await loadModule(sessionId, moduleId); setLoading(false); }
  };

  const setAnswer = (qid: string, val: string) => {
    setModuleData(prev => ({ ...prev, [activeModule]: { ...prev[activeModule], answers: { ...prev[activeModule]?.answers, [qid]: val } } }));
  };

  const saveAnswer = useCallback(async (qid: string, val: string) => {
    if (!sessionId || !val) return;
    setSaving(true);
    try {
      const q = questions.find((q: any) => q.id === qid);
      const result = await saveIntakeResponses(sessionId, [{
        question_id: qid, module_id: activeModule, control_ids: q?.control_ids || [],
        answer_type: q?.answer_type || 'text', answer_value: val,
      }]);
      if (result.flags?.length) setFlags(prev => [...prev.filter((f: any) => f.question_id !== qid), ...result.flags]);
      setProgress(result.progress || progress);
    } catch (e) { console.error('Save failed:', e); }
    finally { setSaving(false); }
  }, [sessionId, questions, activeModule]);

  const currentQ = questions[currentIdx];
  const getQText = (q: any) => q?.text || q?.question || '';
  const getQHelp = (q: any) => q?.help || q?.help_text || '';

  const goNext = () => {
    if (currentQ && answers[currentQ.id]) saveAnswer(currentQ.id, answers[currentQ.id]);
    if (currentIdx < questions.length - 1) { setCurrentIdx(currentIdx + 1); setShowHelp(false); }
    else setCompleted(true);
  };
  const goPrev = () => { if (currentIdx > 0) { setCurrentIdx(currentIdx - 1); setShowHelp(false); } };

  if (loading) return <div className="flex items-center justify-center h-[60vh]"><Loader2 className="w-6 h-6 text-zinc-500 animate-spin" /></div>;

  if (completed) {
    const nextMod = MODULES.find(m => m.id === activeModule + 1);
    return (
      <div className="w-full max-w-xl mx-auto p-8 text-center">
        <Check className="w-12 h-12 text-emerald-400 mx-auto mb-4" />
        <h2 className="text-2xl font-medium text-zinc-100 mb-2">{MODULES.find(m => m.id === activeModule)?.label} Complete</h2>
        <p className="text-zinc-500 mb-6">{Object.keys(answers).length} questions answered{progress.gaps > 0 ? `, ${progress.gaps} gaps found` : ''}</p>
        {flags.filter(f => f.severity === 'critical').length > 0 && (
          <div className="bg-red-500/10 border border-red-500/20 rounded-xl p-4 mb-6 text-left">
            <div className="flex items-center gap-2 text-red-400 mb-2"><AlertTriangle className="w-4 h-4" /> Critical issues found</div>
            {flags.filter(f => f.severity === 'critical').map((f, i) => <p key={i} className="text-sm text-zinc-400">{f.message}</p>)}
          </div>
        )}
        {nextMod ? (
          <button onClick={() => switchModule(nextMod.id)} className="px-6 py-3 bg-blue-500/80 hover:bg-blue-500 rounded-lg text-sm font-medium text-white">
            Continue to {nextMod.label} &rarr;
          </button>
        ) : (
          <p className="text-zinc-500 text-sm">All available modules complete. More coming soon.</p>
        )}
      </div>
    );
  }

  const answeredCount = Object.keys(answers).filter(k => answers[k]).length;
  const pct = questions.length > 0 ? Math.round((answeredCount / questions.length) * 100) : 0;

  return (
    <div className="flex h-[calc(100vh-56px)]">
      {/* Sidebar */}
      <aside className="w-64 border-r border-zinc-800 bg-zinc-900/50 p-4 flex flex-col">
        <div className="mb-4">
          {MODULES.map(m => {
            const md = moduleData[m.id];
            const cnt = md ? Object.keys(md.answers || {}).filter(k => md.answers[k]).length : 0;
            const total = md?.questions?.length || 0;
            return (
              <button key={m.id} onClick={() => switchModule(m.id)}
                className={`w-full flex items-center gap-2 px-3 py-2.5 rounded-lg mb-1 text-sm transition-colors ${activeModule === m.id ? 'bg-zinc-800 text-zinc-200' : 'text-zinc-500 hover:text-zinc-300 hover:bg-zinc-800/50'}`}>
                <m.icon className="w-4 h-4" />
                <span className="flex-1 text-left">{m.label}</span>
                {total > 0 && <span className="text-xs text-zinc-600">{cnt}/{total}</span>}
              </button>
            );
          })}
        </div>
        <div className="text-xs text-zinc-600 uppercase tracking-wider mb-2">Sections</div>
        {(() => {
          const sections: { name: string; start: number; count: number; answered: number }[] = [];
          let last = '';
          questions.forEach((q: any, i: number) => {
            const sec = q.section || '';
            if (sec !== last) { sections.push({ name: sec, start: i, count: 0, answered: 0 }); last = sec; }
            sections[sections.length - 1].count++;
            if (answers[q.id]) sections[sections.length - 1].answered++;
          });
          return sections.map(sec => (
            <button key={sec.name} onClick={() => { setCurrentIdx(sec.start); setShowHelp(false); }}
              className={`w-full text-left px-3 py-2 rounded text-xs transition-colors mb-0.5 ${
                currentQ && (currentQ.section || '') === sec.name ? 'bg-zinc-800 text-zinc-300' : 'text-zinc-500 hover:text-zinc-400'
              }`}>
              <span>{sec.name}</span>
              <span className="float-right text-zinc-600">{sec.answered}/{sec.count}</span>
            </button>
          ));
        })()}
      </aside>

      {/* Main */}
      <main className="flex-1 w-full max-w-3xl mx-auto p-8">
        {/* Progress */}
        <div className="mb-6">
          <div className="h-1 bg-zinc-800 rounded-full overflow-hidden">
            <div className="h-full bg-blue-500 rounded-full transition-all" style={{ width: `${pct}%` }} />
          </div>
          <div className="flex justify-between mt-2 text-xs text-zinc-500">
            <span>{answeredCount} of {questions.length} answered</span>
            {progress.gaps > 0 && <span className="text-amber-400">{progress.gaps} gaps</span>}
          </div>
        </div>

        {/* Question */}
        {currentQ && (
          <div className="bg-zinc-900/50 border border-zinc-800 rounded-xl p-8">
            <div className="flex justify-between items-center mb-4">
              <span className="text-xs text-blue-400 uppercase tracking-wider font-medium">{currentQ.section}</span>
              <span className="text-xs text-zinc-600">{currentIdx + 1} / {questions.length}</span>
            </div>
            <h2 className="text-lg font-medium text-zinc-100 mb-3 leading-relaxed">{getQText(currentQ)}</h2>

            {currentQ.control_ids?.length > 0 && (
              <div className="flex gap-2 mb-3">{currentQ.control_ids.map((c: string) => <span key={c} className="text-xs font-mono px-2 py-0.5 bg-zinc-800 rounded text-zinc-500">{c}</span>)}</div>
            )}

            <button onClick={() => setShowHelp(!showHelp)} className="text-xs text-zinc-500 hover:text-blue-400 flex items-center gap-1 mb-4">
              <HelpCircle className="w-3.5 h-3.5" /> {showHelp ? 'Hide help' : 'Why are we asking this?'}
            </button>
            {showHelp && <div className="bg-zinc-800/50 rounded-lg p-4 mb-4 text-sm text-zinc-400 leading-relaxed">{getQHelp(currentQ)}</div>}

            {/* Answer inputs */}
            <div className="space-y-2 mb-6">
              {currentQ.answer_type === 'yes_no_unsure' && ['yes', 'no', 'unsure'].map(v => (
                <button key={v} onClick={() => setAnswer(currentQ.id, v)}
                  className={`w-full text-left px-4 py-3 rounded-lg border text-sm transition-colors ${answers[currentQ.id] === v ? 'border-blue-500 bg-blue-500/10 text-zinc-200' : 'border-zinc-800 text-zinc-400 hover:border-zinc-700'}`}>
                  {v === 'yes' ? 'Yes' : v === 'no' ? 'No' : "I'm not sure"}
                </button>
              ))}

              {(currentQ.answer_type === 'single_choice') && (currentQ.options || []).map((opt: any) => (
                <button key={opt.value} onClick={() => setAnswer(currentQ.id, opt.value)}
                  className={`w-full text-left px-4 py-3 rounded-lg border text-sm transition-colors ${answers[currentQ.id] === opt.value
                    ? (opt.gap ? 'border-amber-500 bg-amber-500/10' : 'border-blue-500 bg-blue-500/10') + ' text-zinc-200'
                    : 'border-zinc-800 text-zinc-400 hover:border-zinc-700'}`}>
                  <div className="flex items-center justify-between">
                    <span>{opt.label}</span>
                    {opt.gap && opt.severity && <span className={`text-xs font-medium px-1.5 py-0.5 rounded ${opt.severity === 'CRITICAL' ? 'bg-red-500/10 text-red-400' : opt.severity === 'HIGH' ? 'bg-orange-500/10 text-orange-400' : 'bg-amber-500/10 text-amber-400'}`}>{opt.severity}</span>}
                  </div>
                </button>
              ))}

              {(currentQ.answer_type === 'multi_choice' || currentQ.answer_type === 'multiple_choice') && (() => {
                let selected: string[] = [];
                try { selected = JSON.parse(answers[currentQ.id] || '[]'); } catch { selected = []; }
                const toggle = (v: string) => {
                  const next = selected.includes(v) ? selected.filter(s => s !== v) : [...selected, v];
                  setAnswer(currentQ.id, JSON.stringify(next));
                };
                const options = (currentQ.options || []).map((o: any) => typeof o === 'string' ? { value: o, label: o } : o);
                return options.map((opt: any) => (
                  <button key={opt.value} onClick={() => toggle(opt.value)}
                    className={`w-full text-left px-4 py-3 rounded-lg border text-sm transition-colors ${selected.includes(opt.value) ? 'border-blue-500 bg-blue-500/10 text-zinc-200' : 'border-zinc-800 text-zinc-400 hover:border-zinc-700'}`}>
                    <div className="flex items-center gap-3">
                      <div className={`w-4 h-4 rounded border flex items-center justify-center text-xs ${selected.includes(opt.value) ? 'border-blue-500 bg-blue-500/20 text-blue-400' : 'border-zinc-600'}`}>
                        {selected.includes(opt.value) && '✓'}
                      </div>
                      <span>{opt.label}</span>
                    </div>
                  </button>
                ));
              })()}

              {(currentQ.answer_type === 'text' || currentQ.answer_type === 'number') && (
                <input type={currentQ.answer_type === 'number' ? 'number' : 'text'} value={answers[currentQ.id] || ''} onChange={e => setAnswer(currentQ.id, e.target.value)}
                  placeholder="Type your answer..." className="w-full px-4 py-3 bg-zinc-900 border border-zinc-800 rounded-lg text-sm text-zinc-300 focus:outline-none focus:border-zinc-700" />
              )}
            </div>

            {/* Flags */}
            {flags.filter(f => f.question_id === currentQ?.id).map((f, i) => (
              <div key={i} className={`flex items-start gap-3 p-3 rounded-lg mb-4 ${f.severity === 'critical' ? 'bg-red-500/10 border border-red-500/20' : 'bg-amber-500/10 border border-amber-500/20'}`}>
                <AlertTriangle className="w-4 h-4 text-red-400 mt-0.5 flex-shrink-0" />
                <div className="text-sm text-zinc-300">{f.message}</div>
              </div>
            ))}

            {/* Nav */}
            <div className="flex justify-between pt-4 border-t border-zinc-800">
              <button onClick={goPrev} disabled={currentIdx === 0} className="px-4 py-2 bg-zinc-800 hover:bg-zinc-700 disabled:opacity-30 rounded-lg text-sm text-zinc-300 flex items-center gap-2">
                <ChevronLeft className="w-4 h-4" /> Previous
              </button>
              <button onClick={goNext} className="px-4 py-2 bg-blue-500/80 hover:bg-blue-500 rounded-lg text-sm font-medium text-white flex items-center gap-2">
                {saving && <Loader2 className="w-4 h-4 animate-spin" />}
                {currentIdx < questions.length - 1 ? <>Next <ChevronRight className="w-4 h-4" /></> : <>Complete <Check className="w-4 h-4" /></>}
              </button>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
