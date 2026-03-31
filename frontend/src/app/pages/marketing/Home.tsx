import { Link } from 'react-router';
import { useEffect } from 'react';

export function Home() {
  useEffect(() => { document.title = 'Intranest — Sovereign CMMC Compliance Platform'; }, []);

  const valueProps = [
    { icon: 'M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8zM14 2v6h6M16 13H8M16 17H8', title: 'AI-Powered SSP Generation', desc: 'Generate all 110 NIST 800-171 implementation narratives with evidence traceability using sovereign AI inference.' },
    { icon: 'M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z', title: 'Evidence Hashing & Audit Trails', desc: 'SHA-256 cryptographic hashing with tamper-evident audit chains and CMMC-format hash manifests.' },
    { icon: 'M18 20V10M12 20V4M6 20v-6', title: 'SPRS Scoring & Gap Assessment', desc: 'Real-time SPRS score calculation with 1/3/5 point weights, gap severity tiers, and remediation plans.' },
    { icon: 'M2 2h20v8H2zM2 14h20v8H2zM6 6h.01M6 18h.01', title: 'Sovereign Deployment', desc: 'Fully on-premises. No CUI leaves your network. Production inference runs on your hardware.' },
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
      <section className="py-24 md:py-32">
        <div className="max-w-5xl mx-auto px-6">
          <div className="max-w-3xl">
            <div className="inline-flex items-center gap-2 px-2.5 py-1 bg-zinc-900/50 border border-zinc-800 rounded-full text-xs text-zinc-500 mb-6">
              <svg className="w-3.5 h-3.5 text-zinc-600" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
              CMMC Level 2 &middot; NIST 800-171 Rev 2
            </div>
            <h1 className="text-4xl md:text-5xl font-bold text-zinc-100 leading-tight tracking-tight mb-5" style={{ fontFamily: 'Space Grotesk, sans-serif' }}>
              CMMC Level 2 compliance in weeks, not months
            </h1>
            <p className="text-lg text-zinc-500 mb-8 max-w-2xl leading-relaxed">
              AI-generated System Security Plans with evidence traceability. The only compliance platform with tamper-evident evidence hashing and sovereign on-premises deployment.
            </p>
            <div className="flex flex-col sm:flex-row gap-3">
              <Link to="/contact" className="inline-flex items-center justify-center px-5 py-2.5 bg-blue-500/80 hover:bg-blue-500 rounded-lg text-sm font-medium text-white transition-colors">
                Request a Demo
              </Link>
              <Link to="/features" className="inline-flex items-center justify-center px-5 py-2.5 bg-zinc-800 hover:bg-zinc-700 border border-zinc-700 rounded-lg text-sm font-medium text-zinc-300 transition-colors">
                View Features
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Value Props — platform card style */}
      <section className="py-16 border-t border-zinc-800/50">
        <div className="max-w-5xl mx-auto px-6">
          <div className="mb-10">
            <h2 className="text-2xl font-bold text-zinc-100 mb-2" style={{ fontFamily: 'Space Grotesk, sans-serif' }}>Built for the Defense Industrial Base</h2>
            <p className="text-sm text-zinc-500">Everything small defense contractors need to achieve and maintain CMMC Level 2 certification.</p>
          </div>
          <div className="grid md:grid-cols-2 gap-4">
            {valueProps.map((v, i) => (
              <div key={i} className="bg-zinc-900/50 border border-zinc-800 rounded-xl p-5 hover:border-zinc-700 transition-colors">
                <div className="w-9 h-9 rounded-lg bg-zinc-800 flex items-center justify-center mb-3">
                  <svg className="w-4.5 h-4.5 text-zinc-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d={v.icon} />
                  </svg>
                </div>
                <h3 className="text-sm font-medium text-zinc-200 mb-1.5">{v.title}</h3>
                <p className="text-sm text-zinc-500 leading-relaxed">{v.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section className="py-16 border-t border-zinc-800/50">
        <div className="max-w-5xl mx-auto px-6">
          <div className="mb-10">
            <h2 className="text-2xl font-bold text-zinc-100 mb-2" style={{ fontFamily: 'Space Grotesk, sans-serif' }}>How It Works</h2>
            <p className="text-sm text-zinc-500">From initial assessment to C3PAO certification in four steps.</p>
          </div>
          <div className="grid md:grid-cols-4 gap-4">
            {steps.map((s, i) => (
              <div key={i} className="bg-zinc-900/50 border border-zinc-800 rounded-xl p-5">
                <div className="text-xs font-medium text-zinc-600 uppercase tracking-wider mb-3">{s.num}</div>
                <h3 className="text-sm font-medium text-zinc-200 mb-1.5">{s.title}</h3>
                <p className="text-xs text-zinc-500 leading-relaxed">{s.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Social Proof */}
      <section className="py-12 border-t border-zinc-800/50">
        <div className="max-w-5xl mx-auto px-6 text-center">
          <p className="text-xs text-zinc-600 uppercase tracking-wider mb-6">Trusted by defense contractors across the Defense Industrial Base</p>
          <div className="flex flex-wrap justify-center gap-x-10 gap-y-4">
            {['APEX DEFENSE', 'SHIELD SYSTEMS', 'VECTOR OPS', 'TRIDENT TECH', 'IRONCLAD SEC'].map(n => (
              <div key={n} className="text-xs font-medium text-zinc-700 tracking-widest">{n}</div>
            ))}
          </div>
        </div>
      </section>

      {/* Final CTA */}
      <section className="py-16 border-t border-zinc-800/50">
        <div className="max-w-2xl mx-auto px-6 text-center">
          <h2 className="text-2xl font-bold text-zinc-100 mb-3" style={{ fontFamily: 'Space Grotesk, sans-serif' }}>Ready to simplify CMMC compliance?</h2>
          <p className="text-sm text-zinc-500 mb-6">Join defense contractors who are achieving CMMC Level 2 certification with Intranest.</p>
          <Link to="/contact" className="inline-flex items-center justify-center px-6 py-2.5 bg-blue-500/80 hover:bg-blue-500 rounded-lg text-sm font-medium text-white transition-colors">
            Request a Demo
          </Link>
        </div>
      </section>
    </>
  );
}
