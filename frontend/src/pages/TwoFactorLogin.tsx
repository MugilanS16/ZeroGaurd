// frontend/src/pages/TwoFactorLogin.tsx
import React, { useState } from 'react';
import { useNavigate, useLocation, Link } from 'react-router-dom';
import toast from 'react-hot-toast';
import { useAuth } from '../hooks/useAuth';
import { sendOtp, verifyOtp, resendOtp } from '../api/otp';
import { OTPChannel } from '../types/auth';
import PhoneInput from '../components/PhoneInput';
import ChannelToggle from '../components/ChannelToggle';
import OtpInput from '../components/OtpInput';
import ResendTimer from '../components/ResendTimer';
import LoadingSpinner from '../components/LoadingSpinner';

type Step = 'CREDENTIALS' | 'PHONE_ONLY' | 'OTP_VERIFICATION';

export const TwoFactorLogin: React.FC = () => {
  const { login, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const from = location.state?.from?.pathname || '/dashboard';

  // Navigation redirect if already authenticated
  if (isAuthenticated) {
    navigate(from, { replace: true });
    return null;
  }

  // Form states
  const [step, setStep] = useState<Step>('CREDENTIALS');
  const [authMode, setAuthMode] = useState<'password' | 'phone_otp'>('password');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [phone, setPhone] = useState('+919876543210');
  const [channel, setChannel] = useState<OTPChannel>('sms');
  const [otp, setOtp] = useState('');
  
  // Challenge states
  const [challengeId, setChallengeId] = useState<number | null>(null);
  const [maskedPhone, setMaskedPhone] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string>('');

  // 1. Handle Step 1 Submit (Email/Password or Direct Phone OTP)
  const handleInitialSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (authMode === 'password') {
      if (!email || !password) {
        setError('Please enter both your email address and password.');
        return;
      }
      setLoading(true);
      try {
        const res = await login(email, password);
        // If server returns requires_2fa
        if (res && (res as any).requires_2fa) {
          const res2fa = res as any;
          setChallengeId(res2fa.challenge_id);
          setChannel(res2fa.channel || 'sms');
          setMaskedPhone(res2fa.masked_phone || '');
          setStep('OTP_VERIFICATION');
          toast.success(res2fa.message || 'Verification code sent!');
        } else {
          toast.success('Welcome back to ZeroGuard AI! 🛡️');
          navigate(from, { replace: true });
        }
      } catch (err: any) {
        const msg = err.response?.data?.message || err.response?.data?.error || 'Authentication failed. Please verify credentials.';
        setError(msg);
        toast.error(msg);
      } finally {
        setLoading(false);
      }
    } else {
      // Direct Phone OTP Login
      if (!phone || phone.length < 10) {
        setError('Please provide a valid mobile number.');
        return;
      }
      setLoading(true);
      try {
        const res = await sendOtp({ phone, channel, purpose: '2fa_login' });
        if (res.data.success) {
          setChallengeId(res.data.challenge_id);
          setChannel(res.data.channel);
          setMaskedPhone(phone.slice(0, 4) + '******' + phone.slice(-4));
          setStep('OTP_VERIFICATION');
          toast.success(res.data.message);
        }
      } catch (err: any) {
        const msg = err.response?.data?.error || 'Failed to dispatch verification code.';
        setError(msg);
        toast.error(msg);
      } finally {
        setLoading(false);
      }
    }
  };

  // 2. Handle Step 2: OTP Verification
  const handleVerifyOtp = async (codeToVerify?: string) => {
    const finalOtp = codeToVerify || otp;
    if (!challengeId || finalOtp.length !== 6) {
      setError('Please enter the complete 6-digit verification code.');
      return;
    }

    setLoading(true);
    setError('');
    try {
      const res = await verifyOtp({ challenge_id: challengeId, otp: finalOtp });
      if (res.data.success && res.data.access_token) {
        localStorage.setItem('access_token', res.data.access_token);
        toast.success('Two-step verification successful! 👋');
        // Force hydration / redirect
        window.location.href = from;
      }
    } catch (err: any) {
      const msg = err.response?.data?.error || 'Invalid or expired verification code.';
      setError(msg);
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  };

  // 3. Handle Resend OTP
  const handleResend = async () => {
    if (!challengeId) return;
    setLoading(true);
    setError('');
    try {
      const res = await resendOtp({ challenge_id: challengeId });
      if (res.data.success) {
        setChallengeId(res.data.challenge_id);
        setChannel(res.data.channel);
        toast.success(res.data.message);
      }
    } catch (err: any) {
      const msg = err.response?.data?.error || 'Unable to resend OTP at this moment.';
      setError(msg);
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  };

  const fillDemo = () => {
    setEmail('citizen@cybercrime.gov.in');
    setPassword('CitizenPass123!');
    setPhone('+919876543210');
    setError('');
  };

  return (
    <div className="min-h-[85vh] flex items-center justify-center px-4 py-12">
      <div className="w-full max-w-md bg-slate-900/90 backdrop-blur-xl border border-slate-800 rounded-3xl p-6 sm:p-8 shadow-2xl relative overflow-hidden">
        {/* Glow accent */}
        <div className="absolute -top-24 -right-24 w-48 h-48 bg-cyan-500/15 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute -bottom-24 -left-24 w-48 h-48 bg-blue-500/15 rounded-full blur-3xl pointer-events-none" />

        {/* Card Header */}
        <div className="text-center mb-6">
          <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-cyan-500/10 border border-cyan-500/20 text-2xl mb-3 shadow-inner">
            {step === 'OTP_VERIFICATION' ? '🔒' : '🛡️'}
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-white">
            {step === 'OTP_VERIFICATION' ? 'Two-Step Verification' : 'Citizen Sign In'}
          </h1>
          <p className="text-xs sm:text-sm text-slate-400 mt-1">
            {step === 'OTP_VERIFICATION'
              ? `Enter the 6-digit code dispatched via ${channel.toUpperCase()} to ${maskedPhone || 'your phone'}.`
              : 'Secure cybercrime reporting & incident investigation portal.'}
          </p>
        </div>

        {/* Error Alert */}
        {error && (
          <div className="mb-5 p-3.5 bg-red-950/50 border border-red-800/60 rounded-xl text-red-200 text-xs sm:text-sm flex items-start gap-2.5 animate-shake">
            <span className="text-red-400 font-bold">⚠️</span>
            <span>{error}</span>
          </div>
        )}

        {/* STEP 1: INITIAL CREDENTIAL / PHONE ENTRY */}
        {step === 'CREDENTIALS' && (
          <form onSubmit={handleInitialSubmit} className="space-y-4">
            {/* Auth Mode Tabs */}
            <div className="grid grid-cols-2 gap-1 p-1 bg-slate-950/80 rounded-xl border border-slate-800/80 mb-4">
              <button
                type="button"
                onClick={() => { setAuthMode('password'); setError(''); }}
                className={`py-2 text-xs font-semibold rounded-lg transition-all ${
                  authMode === 'password'
                    ? 'bg-slate-800 text-cyan-400 shadow-sm'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                Password Sign In
              </button>
              <button
                type="button"
                onClick={() => { setAuthMode('phone_otp'); setError(''); }}
                className={`py-2 text-xs font-semibold rounded-lg transition-all ${
                  authMode === 'phone_otp'
                    ? 'bg-slate-800 text-cyan-400 shadow-sm'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                Instant OTP Sign In
              </button>
            </div>

            {authMode === 'password' ? (
              <>
                <div>
                  <label htmlFor="login-email" className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1.5">
                    Email Address
                  </label>
                  <input
                    id="login-email"
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="citizen@cybercrime.gov.in"
                    required
                    className="w-full bg-slate-950/80 border border-slate-700/80 rounded-xl px-4 py-2.5 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-cyan-500 focus:ring-2 focus:ring-cyan-500/20"
                  />
                </div>

                <div>
                  <label htmlFor="login-password" className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1.5">
                    Password
                  </label>
                  <input
                    id="login-password"
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="••••••••••••"
                    required
                    className="w-full bg-slate-950/80 border border-slate-700/80 rounded-xl px-4 py-2.5 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-cyan-500 focus:ring-2 focus:ring-cyan-500/20"
                  />
                </div>
              </>
            ) : (
              <>
                <div>
                  <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1.5">
                    Registered Mobile Number
                  </label>
                  <PhoneInput
                    value={phone}
                    onChange={(full) => setPhone(full)}
                    required
                  />
                </div>

                <ChannelToggle
                  selectedChannel={channel}
                  onChange={setChannel}
                />
              </>
            )}

            <button
              type="submit"
              disabled={loading}
              id="signin-btn"
              className="w-full py-3 px-4 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-slate-950 font-bold text-sm shadow-lg shadow-cyan-500/25 transition-all duration-200 flex items-center justify-center gap-2 disabled:opacity-50 mt-2"
            >
              {loading ? <LoadingSpinner size="sm" /> : null}
              <span>{loading ? 'Authenticating…' : (authMode === 'password' ? 'Sign In' : 'Send Verification Code')}</span>
            </button>

            <button
              type="button"
              onClick={fillDemo}
              className="w-full py-2.5 px-3 rounded-xl bg-slate-800/80 hover:bg-slate-700 text-slate-300 text-xs font-medium border border-slate-700/80 transition-colors"
            >
              Fill Demo Citizen Credentials
            </button>
          </form>
        )}

        {/* STEP 2: 6-BOX OTP VERIFICATION */}
        {step === 'OTP_VERIFICATION' && (
          <div className="space-y-6">
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-3 text-center">
                6-Digit Security Code
              </label>
              <OtpInput
                length={6}
                value={otp}
                onChange={setOtp}
                onComplete={(code) => handleVerifyOtp(code)}
                error={!!error}
                autoFocus
              />
            </div>

            <ResendTimer
              initialSeconds={30}
              onResend={handleResend}
              loading={loading}
              channel={channel}
            />

            <button
              type="button"
              id="verify-otp-submit-btn"
              onClick={() => handleVerifyOtp()}
              disabled={loading || otp.length !== 6}
              className="w-full py-3 px-4 rounded-xl bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-400 hover:to-teal-500 text-slate-950 font-bold text-sm shadow-lg shadow-emerald-500/25 transition-all duration-200 flex items-center justify-center gap-2 disabled:opacity-50"
            >
              {loading ? <LoadingSpinner size="sm" /> : null}
              <span>{loading ? 'Verifying Code…' : 'Verify & Continue'}</span>
            </button>

            <button
              type="button"
              onClick={() => { setStep('CREDENTIALS'); setError(''); setOtp(''); }}
              className="w-full text-center text-xs text-slate-400 hover:text-slate-200 transition-colors"
            >
              ← Back to Sign In
            </button>
          </div>
        )}

        {/* Footer info */}
        <div className="mt-8 pt-5 border-t border-slate-800/80 text-center text-xs text-slate-500">
          ZeroGuard AI uses 256-bit HMAC verification & telecom DLT encryption.
          <p className="mt-2 text-slate-400">
            Don't have an account? <Link to="/register" className="text-cyan-400 hover:underline">Register here</Link>
          </p>
        </div>
      </div>
    </div>
  );
};

export default TwoFactorLogin;
