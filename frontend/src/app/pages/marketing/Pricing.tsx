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
    highlight: true,
  },
];

const addons = [
  { name: 'Assessor Pack', price: '$2,500', desc: 'Automated hash manifests, assessment room evidence exports, and C3PAO-ready binder formatting.' },
  { name: 'Connector Packs', price: '$1,200/ea', desc: 'Per-category API evidence collection from Entra ID, CrowdStrike, SentinelOne, and other security tools.' },
  { name: 'Sovereign Deployment', price: 'Contact us', desc: 'Fully air-gapped on-premises installation with vLLM inference on your GPU hardware.' },
];

export function Pricing() {
  useEffect(() => { document.title = 'Pricing — Intranest'; }, []);

  return (
    <section className="py-20 md:py-24">
      <div className="max-w-5xl mx-auto px-6">
        <div className="text-center mb-10">
          <h1 className="text-3xl font-bold text-zinc-100 mb-3" style={{ fontFamily: 'Space Grotesk, sans-serif' }}>Simple, transparent pricing</h1>
          <p className="text-sm text-zinc-500">Replaces $30K–$60K in CMMC consulting labor. No per-user fees.</p>
        </div>

        <div className="grid md:grid-cols-2 gap-4 max-w-3xl mx-auto mb-12">
          {tiers.map(t => (
            <div key={t.name} className={`bg-zinc-900/50 border rounded-xl p-6 ${t.highlight ? 'border-blue-500/30' : 'border-zinc-800'}`}>
              {t.highlight && (
                <span className="inline-block px-2 py-0.5 bg-blue-500/10 text-blue-400 border border-blue-500/20 rounded text-xs font-medium mb-3">Most Popular</span>
              )}
              <h3 className="text-lg font-medium text-zinc-100 mb-1">{t.name}</h3>
              <p className="text-xs text-zinc-500 mb-4">{t.desc}</p>
              <div className="flex items-baseline gap-1 mb-5">
                <span className="text-3xl font-bold text-zinc-100">{t.price}</span>
                <span className="text-sm text-zinc-600">{t.period}</span>
              </div>
              <ul className="space-y-2.5 mb-6">
                {t.features.map((f, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm text-zinc-400">
                    <svg className="w-4 h-4 text-emerald-400/80 mt-0.5 flex-shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="20 6 9 17 4 12" /></svg>
                    {f}
                  </li>
                ))}
              </ul>
              <Link to="/contact" className={`block text-center py-2.5 rounded-lg text-sm font-medium transition-colors ${t.highlight ? 'bg-blue-500/80 hover:bg-blue-500 text-white' : 'bg-zinc-800 hover:bg-zinc-700 border border-zinc-700 text-zinc-300'}`}>
                Request a Demo
              </Link>
            </div>
          ))}
        </div>

        {/* Add-ons */}
        <div className="max-w-3xl mx-auto">
          <h2 className="text-xl font-bold text-zinc-100 mb-4 text-center" style={{ fontFamily: 'Space Grotesk, sans-serif' }}>Add-ons</h2>
          <div className="grid md:grid-cols-3 gap-4">
            {addons.map(a => (
              <div key={a.name} className="bg-zinc-900/50 border border-zinc-800 rounded-xl p-4">
                <h3 className="text-sm font-medium text-zinc-200 mb-1">{a.name}</h3>
                <div className="text-xs font-medium text-blue-400/80 mb-2">{a.price}</div>
                <p className="text-xs text-zinc-500 leading-relaxed">{a.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
