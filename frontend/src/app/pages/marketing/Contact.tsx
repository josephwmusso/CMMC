import { useState, useEffect } from 'react';

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
      setError('Something went wrong. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const inputClass = "w-full px-3 py-2.5 bg-zinc-900/50 border border-zinc-800 rounded-lg text-sm text-zinc-200 placeholder:text-zinc-600 focus:outline-none focus:border-zinc-700 transition-colors";

  if (submitted) {
    return (
      <section className="py-24 md:py-32">
        <div className="max-w-md mx-auto px-6 text-center">
          <div className="w-10 h-10 rounded-lg bg-emerald-500/10 flex items-center justify-center mx-auto mb-4">
            <svg className="w-5 h-5 text-emerald-400/80" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="20 6 9 17 4 12" /></svg>
          </div>
          <h1 className="text-xl font-bold text-zinc-100 mb-2" style={{ fontFamily: 'Space Grotesk, sans-serif' }}>Demo request received</h1>
          <p className="text-sm text-zinc-500">We'll be in touch within one business day to schedule your walkthrough.</p>
        </div>
      </section>
    );
  }

  return (
    <section className="py-20 md:py-24">
      <div className="max-w-md mx-auto px-6">
        <h1 className="text-2xl font-bold text-zinc-100 mb-2" style={{ fontFamily: 'Space Grotesk, sans-serif' }}>Request a Demo</h1>
        <p className="text-sm text-zinc-500 mb-8">Tell us about your organization and we'll schedule a personalized walkthrough.</p>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs text-zinc-600 uppercase tracking-wider mb-1.5">Full Name *</label>
            <input type="text" required value={form.name} onChange={e => setForm(f => ({ ...f, name: e.target.value }))}
              className={inputClass} placeholder="Jane Smith" />
          </div>
          <div>
            <label className="block text-xs text-zinc-600 uppercase tracking-wider mb-1.5">Work Email *</label>
            <input type="email" required value={form.email} onChange={e => setForm(f => ({ ...f, email: e.target.value }))}
              className={inputClass} placeholder="jane@company.com" />
          </div>
          <div>
            <label className="block text-xs text-zinc-600 uppercase tracking-wider mb-1.5">Company Name</label>
            <input type="text" value={form.company} onChange={e => setForm(f => ({ ...f, company: e.target.value }))}
              className={inputClass} placeholder="Acme Defense Corp" />
          </div>
          <div>
            <label className="block text-xs text-zinc-600 uppercase tracking-wider mb-1.5">Number of Employees</label>
            <select value={form.employee_count} onChange={e => setForm(f => ({ ...f, employee_count: e.target.value }))}
              className={inputClass}>
              <option value="">Select...</option>
              <option value="1-25">1–25</option>
              <option value="26-50">26–50</option>
              <option value="51-100">51–100</option>
              <option value="100+">100+</option>
            </select>
          </div>
          <div>
            <label className="block text-xs text-zinc-600 uppercase tracking-wider mb-1.5">Message</label>
            <textarea rows={3} value={form.message} onChange={e => setForm(f => ({ ...f, message: e.target.value }))}
              className={`${inputClass} resize-none`} placeholder="Tell us about your compliance needs..." />
          </div>

          {error && <p className="text-sm text-red-400">{error}</p>}

          <button type="submit" disabled={loading}
            className="w-full py-2.5 bg-blue-500/80 hover:bg-blue-500 rounded-lg text-sm font-medium text-white transition-colors disabled:opacity-50 flex items-center justify-center gap-2">
            {loading ? 'Submitting...' : 'Request Demo'}
          </button>
        </form>
      </div>
    </section>
  );
}
