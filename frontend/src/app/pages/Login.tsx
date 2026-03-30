import { useState, useEffect } from 'react';
import { Shield, Loader2, AlertCircle } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

declare global {
  interface Window {
    google?: any;
    microsalInstance?: any;
  }
}

function GoogleIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 48 48"><path fill="#EA4335" d="M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5z"/><path fill="#4285F4" d="M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.94c-.58 2.96-2.26 5.48-4.78 7.18l7.73 6c4.51-4.18 7.09-10.36 7.09-17.65z"/><path fill="#FBBC05" d="M10.53 28.59c-.48-1.45-.76-2.99-.76-4.59s.27-3.14.76-4.59l-7.98-6.19C.92 16.46 0 20.12 0 24c0 3.88.92 7.54 2.56 10.78l7.97-6.19z"/><path fill="#34A853" d="M24 48c6.48 0 11.93-2.13 15.89-5.81l-7.73-6c-2.15 1.45-4.92 2.3-8.16 2.3-6.26 0-11.57-4.22-13.47-9.91l-7.98 6.19C6.51 42.62 14.62 48 24 48z"/></svg>
  );
}

function MicrosoftIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 21 21"><rect x="1" y="1" width="9" height="9" fill="#f25022"/><rect x="11" y="1" width="9" height="9" fill="#7fba00"/><rect x="1" y="11" width="9" height="9" fill="#00a4ef"/><rect x="11" y="11" width="9" height="9" fill="#ffb900"/></svg>
  );
}

function AppleIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M17.05 20.28c-.98.95-2.05.88-3.08.4-1.09-.5-2.08-.48-3.24 0-1.44.62-2.2.44-3.06-.4C2.79 15.25 3.51 7.59 9.05 7.31c1.35.07 2.29.74 3.08.8 1.18-.24 2.31-.93 3.57-.84 1.51.12 2.65.72 3.4 1.8-3.12 1.87-2.38 5.98.48 7.13-.57 1.5-1.31 2.99-2.54 4.09zM12.03 7.25c-.15-2.23 1.66-4.07 3.74-4.25.29 2.58-2.34 4.5-3.74 4.25z"/></svg>
  );
}

const GOOGLE_CLIENT_ID = '886737425498-d0i75gbgnbmsodqcrgkqq9fvl3r8s3u8.apps.googleusercontent.com';

export function Login() {
  const { login, loginWithOAuth } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [showEmailForm, setShowEmailForm] = useState(false);

  // Load Google Sign-In SDK
  useEffect(() => {
    if (document.getElementById('google-gsi')) return;
    const script = document.createElement('script');
    script.id = 'google-gsi';
    script.src = 'https://accounts.google.com/gsi/client';
    script.async = true;
    script.onload = () => {
      window.google?.accounts.id.initialize({
        client_id: GOOGLE_CLIENT_ID,
        callback: handleGoogleResponse,
      });
    };
    document.head.appendChild(script);
  }, []);

  const handleGoogleResponse = async (response: any) => {
    setError('');
    setLoading(true);
    try {
      await loginWithOAuth(response.credential, 'google');
    } catch (err: any) {
      setError(err.message || 'Google sign-in failed');
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleClick = () => {
    if (window.google) {
      window.google.accounts.id.prompt();
    } else {
      setError('Google Sign-In is loading, try again in a moment');
    }
  };

  const handleMicrosoftClick = () => {
    // Microsoft OAuth via popup
    const msClientId = ''; // Set via env if needed
    if (!msClientId) {
      setError('Microsoft sign-in coming soon');
      return;
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await login(email, password);
    } catch (err: any) {
      setError(err.message || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-black flex items-center justify-center p-4">
      <div className="w-full max-w-sm">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="w-14 h-14 rounded-2xl bg-zinc-900 border border-zinc-800 flex items-center justify-center mx-auto mb-5" style={{ boxShadow: '0 0 30px rgba(255,255,255,0.03)' }}>
            <Shield className="w-8 h-8 text-zinc-400" />
          </div>
          <h1 className="text-2xl font-semibold text-zinc-100 tracking-tight" style={{ fontFamily: 'Space Grotesk, sans-serif' }}>
            INTRANEST
          </h1>
          <p className="text-sm text-zinc-600 mt-1">CMMC Compliance Platform</p>
        </div>

        <div className="bg-zinc-900/40 border border-zinc-800 rounded-2xl p-6">
          {error && (
            <div className="mb-5 flex items-center gap-2 px-3 py-2.5 bg-red-500/10 border border-red-500/20 rounded-xl">
              <AlertCircle className="w-4 h-4 text-red-400 flex-shrink-0" />
              <span className="text-sm text-red-400">{error}</span>
            </div>
          )}

          {/* Social Login Buttons */}
          <div className="space-y-2.5 mb-5">
            <button
              onClick={handleGoogleClick}
              disabled={loading}
              className="w-full flex items-center justify-center gap-3 px-4 py-2.5 bg-white hover:bg-zinc-100 rounded-xl text-sm font-medium text-zinc-800 transition-colors disabled:opacity-50"
            >
              <GoogleIcon /> Continue with Google
            </button>

            <button
              onClick={handleMicrosoftClick}
              disabled={loading}
              className="w-full flex items-center justify-center gap-3 px-4 py-2.5 bg-zinc-800 hover:bg-zinc-700 border border-zinc-700 rounded-xl text-sm font-medium text-zinc-200 transition-colors disabled:opacity-50"
            >
              <MicrosoftIcon /> Continue with Microsoft
            </button>

            <button
              disabled={true}
              className="w-full flex items-center justify-center gap-3 px-4 py-2.5 bg-zinc-800 hover:bg-zinc-700 border border-zinc-700 rounded-xl text-sm font-medium text-zinc-200 transition-colors opacity-40 cursor-not-allowed"
            >
              <AppleIcon /> Continue with Apple
            </button>
          </div>

          {/* Divider */}
          <div className="flex items-center gap-3 mb-5">
            <div className="flex-1 h-px bg-zinc-800" />
            <span className="text-xs text-zinc-600 uppercase tracking-wider">or</span>
            <div className="flex-1 h-px bg-zinc-800" />
          </div>

          {/* Email Login */}
          {!showEmailForm ? (
            <button
              onClick={() => setShowEmailForm(true)}
              className="w-full py-2.5 bg-zinc-800/50 hover:bg-zinc-800 border border-zinc-800 rounded-xl text-sm text-zinc-400 hover:text-zinc-300 transition-colors"
            >
              Sign in with email
            </button>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-3">
              <input
                type="email"
                value={email}
                onChange={e => setEmail(e.target.value)}
                required
                autoFocus
                className="w-full px-3.5 py-2.5 bg-black border border-zinc-800 rounded-xl text-sm text-zinc-200 placeholder:text-zinc-700 focus:outline-none focus:border-zinc-600 transition-colors"
                placeholder="Email address"
              />
              <input
                type="password"
                value={password}
                onChange={e => setPassword(e.target.value)}
                required
                className="w-full px-3.5 py-2.5 bg-black border border-zinc-800 rounded-xl text-sm text-zinc-200 placeholder:text-zinc-700 focus:outline-none focus:border-zinc-600 transition-colors"
                placeholder="Password"
              />
              <button
                type="submit"
                disabled={loading}
                className="w-full py-2.5 bg-zinc-100 hover:bg-white text-black rounded-xl text-sm font-medium transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
              >
                {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : null}
                {loading ? 'Signing in...' : 'Sign in'}
              </button>
            </form>
          )}
        </div>

        <p className="text-center text-xs text-zinc-700 mt-6">
          Secured by Intranest
        </p>
      </div>
    </div>
  );
}
