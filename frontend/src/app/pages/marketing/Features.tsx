import { useEffect } from 'react';
import { Link } from 'react-router';

const features = [
  { title: 'AI-Powered SSP Generation', desc: 'Generates all 110 NIST 800-171 Rev 2 implementation narratives using sovereign AI inference. Each narrative includes evidence traceability, gap identification, and control-specific context from your organization profile.', icon: 'M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z' },
  { title: 'Evidence Hashing & Audit Trails', desc: 'SHA-256 cryptographic hashing for every evidence artifact. Tamper-evident hash-chained audit log with GENESIS seed. CMMC-format hash manifests for C3PAO assessors. State machine enforces DRAFT → REVIEWED → APPROVED → PUBLISHED lifecycle.', icon: 'M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z' },
  { title: 'SPRS Scoring Engine', desc: 'Real-time Supplier Performance Risk System score calculation. 1, 3, and 5-point control weights per DoD methodology. Score range from 110 (all met) to -203 (floor). POA&M conditional credit above 88-point threshold.', icon: 'M18 20V10M12 20V4M6 20v-6' },
  { title: 'Gap Assessment', desc: 'Five gap types automatically detected: NO_SSP, NO_EVIDENCE, PARTIAL_IMPLEMENTATION, STATUS_MISMATCH, and INSUFFICIENT_EVIDENCE. Three severity tiers (CRITICAL, HIGH, MEDIUM) with automatic remediation recommendations.', icon: 'M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z' },
  { title: 'Document Generation', desc: 'Seven compliance documents generated from guided intake: Incident Response Plan, Policy Manual, Configuration Management Plan, Risk Assessment, Security Training Program, Scope & Boundary Package, and Customer Responsibility Matrix.', icon: 'M4 4h16v16H4zM9 9h6M9 13h6M9 17h4' },
  { title: 'POA&M Management', desc: 'Auto-generated Plan of Action & Milestones with 180-day deadlines. Risk levels assigned by control point weight. CA.L2-3.12.4 (System Security Plan) hard-blocked from POA&M per CMMC assessment rules.', icon: 'M9 11l3 3L22 4M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11' },
  { title: 'Guided Intake Wizard', desc: 'The "TurboTax of CMMC assessments." Module-based questionnaire walks contractors through organizational scoping, access control, and system boundary definition. Answers auto-map to NIST controls for gap detection.', icon: 'M12 20h9M16.5 3.5a2.12 2.12 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z' },
  { title: 'Sovereign Deployment', desc: 'Fully on-premises architecture. No CUI leaves the network. Production inference via vLLM on customer GPU hardware. Air-gapped deployment option with Snowflake Arctic embeddings. No cloud dependencies for sensitive data processing.', icon: 'M2 2h20v8H2zM2 14h20v8H2zM6 6h.01M6 18h.01' },
];

export function Features() {
  useEffect(() => { document.title = 'Features — Intranest'; }, []);

  return (
    <>
      <section className="py-20 md:py-28">
        <div className="max-w-6xl mx-auto px-6">
          <div className="max-w-2xl mb-14">
            <h1 className="text-4xl font-bold text-white mb-4">Platform Features</h1>
            <p className="text-lg text-slate-400 leading-relaxed">
              Every capability a small defense contractor needs to achieve CMMC Level 2 certification — from initial scoping through C3PAO assessment.
            </p>
          </div>

          <div className="grid md:grid-cols-2 gap-6">
            {features.map((f, i) => (
              <div key={i} className="p-6 bg-[#1E293B]/40 border border-white/5 rounded-xl hover:border-blue-500/20 transition-colors">
                <div className="w-10 h-10 rounded-lg bg-blue-500/10 flex items-center justify-center mb-4">
                  <svg className="w-5 h-5 text-blue-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                    <path d={f.icon} />
                  </svg>
                </div>
                <h3 className="text-lg font-semibold text-white mb-2">{f.title}</h3>
                <p className="text-sm text-slate-400 leading-relaxed">{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="py-16 bg-[#0B1120]">
        <div className="max-w-3xl mx-auto px-6 text-center">
          <h2 className="text-2xl font-bold text-white mb-4">See it in action</h2>
          <p className="text-slate-400 mb-6">Schedule a walkthrough with our team to see how Intranest handles your specific compliance requirements.</p>
          <Link to="/contact" className="inline-flex items-center justify-center px-6 py-3 bg-blue-600 hover:bg-blue-500 rounded-lg text-sm font-medium transition-colors">Request a Demo</Link>
        </div>
      </section>
    </>
  );
}
