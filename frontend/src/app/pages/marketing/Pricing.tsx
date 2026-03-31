import { useEffect } from 'react';
import { Link } from 'react-router';

const tiers = [
  {
    name: 'Essential',
    price: '$8,000',
    period: '/year',
    desc: 'Self-assessment preparation for small contractors.',
    features: [
      'AI-powered SSP generation (110 controls)',
      'SPRS scoring with real-time calculations',
      'Evidence management & SHA-256 hashing',
      'Gap assessment with remediation plans',
      'DOCX & PDF export',
      'Guided intake wizard',
      'Email support',
    ],
    cta: 'Request Demo',
    highlight: false,
  },
  {
    name: 'Professional',
    price: '$15,000',
    period: '/year',
    desc: 'Full certification preparation for C3PAO assessment.',
    features: [
      'Everything in Essential, plus:',
      'Continuous monitoring & re-assessment',
      'POA&M management with auto-generation',
      'Evidence binder export (ZIP)',
      'Document generation (7 templates)',
      'Hash manifest generation for assessors',
      'Audit chain integrity verification',
      'Priority support',
    ],
    cta: 'Request Demo',
    highlight: true,
  },
];

const addons = [
  { name: 'Assessor Pack', price: '$2,500', desc: 'Automated hash manifests, assessment room evidence exports, and C3PAO-ready binder formatting.' },
  { name: 'Connector Packs', price: '$1,200/ea', desc: 'Per-category API evidence collection from Entra ID, CrowdStrike, SentinelOne, and other security tools.' },
  { name: 'Sovereign Deployment', price: 'Contact us', desc: 'Fully air-gapped on-premises installation with vLLM inference on your GPU hardware. No CUI leaves your network.' },
];

export function Pricing() {
  useEffect(() => { document.title = 'Pricing — Intranest'; }, []);

  return (
    <>
      <section className="py-20 md:py-28">
        <div className="max-w-6xl mx-auto px-6">
          <div className="text-center mb-14">
            <h1 className="text-4xl font-bold text-white mb-4">Simple, transparent pricing</h1>
            <p className="text-lg text-slate-400 max-w-xl mx-auto">
              Replaces $30K–$60K in CMMC consulting labor. No per-user fees, no surprises.
            </p>
          </div>

          <div className="grid md:grid-cols-2 gap-6 max-w-4xl mx-auto mb-16">
            {tiers.map(t => (
              <div key={t.name} className={`p-8 rounded-xl border ${t.highlight ? 'border-blue-500/30 bg-blue-500/5' : 'border-white/5 bg-[#1E293B]/40'}`}>
                {t.highlight && <div className="text-xs font-medium text-blue-400 uppercase tracking-wider mb-3">Most Popular</div>}
                <h3 className="text-xl font-semibold text-white mb-1">{t.name}</h3>
                <p className="text-sm text-slate-400 mb-5">{t.desc}</p>
                <div className="flex items-baseline gap-1 mb-6">
                  <span className="text-4xl font-bold text-white">{t.price}</span>
                  <span className="text-sm text-slate-500">{t.period}</span>
                </div>
                <ul className="space-y-3 mb-8">
                  {t.features.map((f, i) => (
                    <li key={i} className="flex items-start gap-2.5 text-sm text-slate-300">
                      <svg className="w-4 h-4 text-blue-400 mt-0.5 flex-shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="20 6 9 17 4 12" /></svg>
                      {f}
                    </li>
                  ))}
                </ul>
                <Link to="/contact" className={`block text-center py-2.5 rounded-lg text-sm font-medium transition-colors ${t.highlight ? 'bg-blue-600 hover:bg-blue-500 text-white' : 'bg-white/5 hover:bg-white/10 border border-white/10 text-slate-300'}`}>
                  {t.cta}
                </Link>
              </div>
            ))}
          </div>

          {/* Add-ons */}
          <div className="max-w-4xl mx-auto">
            <h2 className="text-2xl font-bold text-white mb-6 text-center">Add-ons</h2>
            <div className="grid md:grid-cols-3 gap-4">
              {addons.map(a => (
                <div key={a.name} className="p-5 bg-[#1E293B]/30 border border-white/5 rounded-xl">
                  <h3 className="text-base font-semibold text-white mb-1">{a.name}</h3>
                  <div className="text-sm font-medium text-blue-400 mb-2">{a.price}</div>
                  <p className="text-xs text-slate-400 leading-relaxed">{a.desc}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>
    </>
  );
}
