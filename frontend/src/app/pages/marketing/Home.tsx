import { Link } from 'react-router';
import { useEffect } from 'react';

function ShieldIcon({ className = '' }: { className?: string }) {
  return <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>;
}
function LockIcon({ className = '' }: { className?: string }) {
  return <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>;
}
function ChartIcon({ className = '' }: { className?: string }) {
  return <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>;
}
function ServerIcon({ className = '' }: { className?: string }) {
  return <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><rect x="2" y="2" width="20" height="8" rx="2"/><rect x="2" y="14" width="20" height="8" rx="2"/><line x1="6" y1="6" x2="6.01" y2="6"/><line x1="6" y1="18" x2="6.01" y2="18"/></svg>;
}
function DocIcon({ className = '' }: { className?: string }) {
  return <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>;
}

export function Home() {
  useEffect(() => { document.title = 'Intranest — Sovereign CMMC Compliance Platform'; }, []);

  const valueProps = [
    { icon: <DocIcon className="w-6 h-6 text-blue-400" />, title: 'AI-Powered SSP Generation', desc: 'Generate all 110 NIST 800-171 implementation narratives with evidence traceability using sovereign AI inference.' },
    { icon: <LockIcon className="w-6 h-6 text-blue-400" />, title: 'Evidence Hashing & Audit Trails', desc: 'SHA-256 cryptographic hashing with tamper-evident audit chains and CMMC-format hash manifests.' },
    { icon: <ChartIcon className="w-6 h-6 text-blue-400" />, title: 'SPRS Scoring & Gap Assessment', desc: 'Real-time SPRS score calculation with 1/3/5 point weights, gap severity tiers, and remediation plans.' },
    { icon: <ServerIcon className="w-6 h-6 text-blue-400" />, title: 'Sovereign Deployment', desc: 'Fully on-premises. No CUI leaves your network. Production inference runs on your hardware.' },
  ];

  const steps = [
    { num: '01', title: 'Answer Questions', desc: 'Guided intake wizard walks you through scoping and system boundary definition.' },
    { num: '02', title: 'Generate Documents', desc: 'AI generates your SSP, policies, and compliance documentation from your answers.' },
    { num: '03', title: 'Build Evidence', desc: 'Upload, hash, and link evidence artifacts to controls with tamper-proof audit chains.' },
    { num: '04', title: 'Get Certified', desc: 'Export assessment binders, hash manifests, and POA&M reports for your C3PAO assessment.' },
  ];

  return (
    <>
      {/* Hero */}
      <section className="relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-b from-blue-500/5 via-transparent to-transparent" />
        <div className="max-w-6xl mx-auto px-6 pt-24 pb-20 md:pt-32 md:pb-28 relative">
          <div className="max-w-3xl">
            <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-blue-500/10 border border-blue-500/20 rounded-full text-xs font-medium text-blue-400 mb-6">
              <ShieldIcon className="w-3.5 h-3.5" /> CMMC Level 2 &middot; NIST 800-171 Rev 2
            </div>
            <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold text-white leading-tight tracking-tight mb-6">
              CMMC Level 2 compliance<br className="hidden md:block" /> in weeks, not months
            </h1>
            <p className="text-lg md:text-xl text-slate-400 mb-8 max-w-2xl leading-relaxed">
              AI-generated System Security Plans with evidence traceability. The only compliance platform with tamper-evident evidence hashing and sovereign on-premises deployment.
            </p>
            <div className="flex flex-col sm:flex-row gap-3">
              <Link to="/contact" className="inline-flex items-center justify-center px-6 py-3 bg-blue-600 hover:bg-blue-500 rounded-lg text-sm font-medium transition-colors">
                Request a Demo
              </Link>
              <Link to="/features" className="inline-flex items-center justify-center px-6 py-3 bg-white/5 hover:bg-white/10 border border-white/10 rounded-lg text-sm font-medium text-slate-300 transition-colors">
                View Features
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Value Props */}
      <section className="py-20 bg-[#0B1120]">
        <div className="max-w-6xl mx-auto px-6">
          <div className="text-center mb-14">
            <h2 className="text-3xl font-bold text-white mb-3">Built for the Defense Industrial Base</h2>
            <p className="text-slate-400 max-w-xl mx-auto">Everything small defense contractors need to achieve and maintain CMMC Level 2 certification.</p>
          </div>
          <div className="grid md:grid-cols-2 gap-6">
            {valueProps.map((v, i) => (
              <div key={i} className="p-6 bg-[#1E293B]/50 border border-white/5 rounded-xl hover:border-blue-500/20 transition-colors">
                <div className="w-10 h-10 rounded-lg bg-blue-500/10 flex items-center justify-center mb-4">{v.icon}</div>
                <h3 className="text-lg font-semibold text-white mb-2">{v.title}</h3>
                <p className="text-sm text-slate-400 leading-relaxed">{v.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section className="py-20">
        <div className="max-w-6xl mx-auto px-6">
          <div className="text-center mb-14">
            <h2 className="text-3xl font-bold text-white mb-3">How It Works</h2>
            <p className="text-slate-400">From initial assessment to C3PAO certification in four steps.</p>
          </div>
          <div className="grid md:grid-cols-4 gap-6">
            {steps.map((s, i) => (
              <div key={i} className="relative">
                <div className="text-5xl font-bold text-white/5 mb-3">{s.num}</div>
                <h3 className="text-base font-semibold text-white mb-2">{s.title}</h3>
                <p className="text-sm text-slate-500 leading-relaxed">{s.desc}</p>
                {i < 3 && <div className="hidden md:block absolute top-8 -right-3 w-6 text-slate-700">&rarr;</div>}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Social Proof */}
      <section className="py-16 bg-[#0B1120]">
        <div className="max-w-6xl mx-auto px-6 text-center">
          <p className="text-sm text-slate-500 uppercase tracking-wider font-medium mb-8">Trusted by defense contractors across the Defense Industrial Base</p>
          <div className="flex flex-wrap justify-center gap-x-12 gap-y-6 opacity-30">
            {['APEX DEFENSE', 'SHIELD SYSTEMS', 'VECTOR OPS', 'TRIDENT TECH', 'IRONCLAD SEC'].map(n => (
              <div key={n} className="text-sm font-semibold text-slate-400 tracking-widest">{n}</div>
            ))}
          </div>
        </div>
      </section>

      {/* Final CTA */}
      <section className="py-20">
        <div className="max-w-3xl mx-auto px-6 text-center">
          <h2 className="text-3xl font-bold text-white mb-4">Ready to simplify CMMC compliance?</h2>
          <p className="text-slate-400 mb-8">Join defense contractors who are achieving CMMC Level 2 certification with Intranest.</p>
          <Link to="/contact" className="inline-flex items-center justify-center px-8 py-3.5 bg-blue-600 hover:bg-blue-500 rounded-lg text-sm font-medium transition-colors">
            Request a Demo
          </Link>
        </div>
      </section>
    </>
  );
}
