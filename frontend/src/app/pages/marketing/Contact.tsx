import { useState, useEffect } from 'react';
import { CheckCircle, Loader2 } from 'lucide-react';

export function Contact() {
  useEffect(() => { document.title = 'Request a Demo — Intranest'; }, []);

  const [form, setForm] = useState({ name: '', email: '', company: '', employee_count: '', message: '' });
  const [loading, setLoading] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      const res = await fetch('/api/contact', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form),
      });
      if (!res.ok) throw new Error('Submission failed');
      setSubmitted(true);
    } catch {
      setError('Something went wrong. Please try again or email us directly.');
    } finally {
      setLoading(false);
    }
  };

  if (submitted) {
    return (
      <section className="py-20 md:py-32">
        <div className="max-w-lg mx-auto px-6 text-center">
          <CheckCircle className="w-12 h-12 text-emerald-400 mx-auto mb-4" />
          <h1 className="text-2xl font-bold text-white mb-3">Demo request received</h1>
          <p className="text-slate-400">We'll be in touch within one business day to schedule your walkthrough.</p>
        </div>
      </section>
    );
  }

  return (
    <section className="py-20 md:py-28">
      <div className="max-w-lg mx-auto px-6">
        <h1 className="text-3xl font-bold text-white mb-2">Request a Demo</h1>
        <p className="text-slate-400 mb-8">Tell us about your organization and we'll schedule a personalized walkthrough.</p>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs text-slate-400 uppercase tracking-wider mb-1.5">Full Name *</label>
            <input type="text" required value={form.name} onChange={e => setForm(f => ({ ...f, name: e.target.value }))}
              className="w-full px-3.5 py-2.5 bg-[#1E293B] border border-white/10 rounded-lg text-sm text-white placeholder:text-slate-600 focus:outline-none focus:border-blue-500/50 transition-colors"
              placeholder="Jane Smith" />
          </div>
          <div>
            <label className="block text-xs text-slate-400 uppercase tracking-wider mb-1.5">Work Email *</label>
            <input type="email" required value={form.email} onChange={e => setForm(f => ({ ...f, email: e.target.value }))}
              className="w-full px-3.5 py-2.5 bg-[#1E293B] border border-white/10 rounded-lg text-sm text-white placeholder:text-slate-600 focus:outline-none focus:border-blue-500/50 transition-colors"
              placeholder="jane@company.com" />
          </div>
          <div>
            <label className="block text-xs text-slate-400 uppercase tracking-wider mb-1.5">Company Name</label>
            <input type="text" value={form.company} onChange={e => setForm(f => ({ ...f, company: e.target.value }))}
              className="w-full px-3.5 py-2.5 bg-[#1E293B] border border-white/10 rounded-lg text-sm text-white placeholder:text-slate-600 focus:outline-none focus:border-blue-500/50 transition-colors"
              placeholder="Acme Defense Corp" />
          </div>
          <div>
            <label className="block text-xs text-slate-400 uppercase tracking-wider mb-1.5">Number of Employees</label>
            <select value={form.employee_count} onChange={e => setForm(f => ({ ...f, employee_count: e.target.value }))}
              className="w-full px-3.5 py-2.5 bg-[#1E293B] border border-white/10 rounded-lg text-sm text-white focus:outline-none focus:border-blue-500/50 transition-colors">
              <option value="">Select...</option>
              <option value="1-25">1–25</option>
              <option value="26-50">26–50</option>
              <option value="51-100">51–100</option>
              <option value="100+">100+</option>
            </select>
          </div>
          <div>
            <label className="block text-xs text-slate-400 uppercase tracking-wider mb-1.5">Message</label>
            <textarea rows={3} value={form.message} onChange={e => setForm(f => ({ ...f, message: e.target.value }))}
              className="w-full px-3.5 py-2.5 bg-[#1E293B] border border-white/10 rounded-lg text-sm text-white placeholder:text-slate-600 focus:outline-none focus:border-blue-500/50 transition-colors resize-none"
              placeholder="Tell us about your compliance needs..." />
          </div>

          {error && <p className="text-sm text-red-400">{error}</p>}

          <button type="submit" disabled={loading}
            className="w-full py-3 bg-blue-600 hover:bg-blue-500 rounded-lg text-sm font-medium text-white transition-colors disabled:opacity-50 flex items-center justify-center gap-2">
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : null}
            {loading ? 'Submitting...' : 'Request Demo'}
          </button>
        </form>
      </div>
    </section>
  );
}
