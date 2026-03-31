import { useEffect } from 'react';
import { Link } from 'react-router';

export function About() {
  useEffect(() => { document.title = 'About — Intranest'; }, []);

  const audience = [
    { title: 'Small Defense Contractors', desc: '10–200 employees handling CUI under DoD contracts. Subcontractors who need CMMC Level 2 to keep their prime contracts.' },
    { title: 'CISOs & ISSEs', desc: 'Information System Security Engineers and officers responsible for developing and maintaining the SSP and evidence portfolio.' },
    { title: 'Compliance Officers', desc: 'Teams managing the self-assessment process, SPRS score submission, and C3PAO certification timeline.' },
    { title: 'Business Owners', desc: 'Small business leaders who need to understand their compliance posture and the investment required for certification.' },
  ];

  return (
    <section className="py-20 md:py-24">
      <div className="max-w-3xl mx-auto px-6">
        <h1 className="text-3xl font-bold text-zinc-100 mb-5" style={{ fontFamily: 'Space Grotesk, sans-serif' }}>Making CMMC compliance accessible</h1>
        <p className="text-sm text-zinc-400 leading-relaxed mb-4">
          Small defense contractors are the backbone of the Defense Industrial Base. They handle Controlled Unclassified Information critical to national security — but most can't afford the $30K–$60K consulting engagements required for CMMC Level 2 certification.
        </p>
        <p className="text-sm text-zinc-400 leading-relaxed mb-10">
          Intranest automates the hardest parts of CMMC compliance — generating System Security Plans, managing evidence with cryptographic integrity, calculating SPRS scores, and producing assessment-ready documentation — so contractors can focus on their mission.
        </p>

        <div className="border-t border-zinc-800 pt-10 mb-10">
          <h2 className="text-xl font-bold text-zinc-100 mb-3" style={{ fontFamily: 'Space Grotesk, sans-serif' }}>Why sovereign compliance matters</h2>
          <p className="text-sm text-zinc-400 leading-relaxed mb-4">
            The irony of most compliance platforms is that they ask you to upload Controlled Unclassified Information to their cloud servers. Intranest takes a different approach: our sovereign deployment option runs entirely within your network boundary. Production AI inference runs on your GPU hardware. Your CUI never leaves your facility.
          </p>
          <p className="text-sm text-zinc-400 leading-relaxed">
            This isn't just a feature — it's a fundamental architectural decision. When you're certifying that your organization properly handles CUI per NIST 800-171, your compliance tooling should meet the same standard.
          </p>
        </div>

        <div className="border-t border-zinc-800 pt-10 mb-10">
          <h2 className="text-xl font-bold text-zinc-100 mb-5" style={{ fontFamily: 'Space Grotesk, sans-serif' }}>Who we're built for</h2>
          <div className="grid md:grid-cols-2 gap-4">
            {audience.map(a => (
              <div key={a.title} className="bg-zinc-900/50 border border-zinc-800 rounded-xl p-5">
                <h3 className="text-sm font-medium text-zinc-200 mb-1.5">{a.title}</h3>
                <p className="text-sm text-zinc-500 leading-relaxed">{a.desc}</p>
              </div>
            ))}
          </div>
        </div>

        <div className="border-t border-zinc-800 pt-10 text-center">
          <p className="text-xs text-zinc-600 mb-5">Built in San Francisco for the Defense Industrial Base</p>
          <Link to="/contact" className="inline-flex items-center justify-center px-5 py-2.5 bg-blue-500/80 hover:bg-blue-500 rounded-lg text-sm font-medium text-white transition-colors">
            Get in touch
          </Link>
        </div>
      </div>
    </section>
  );
}
