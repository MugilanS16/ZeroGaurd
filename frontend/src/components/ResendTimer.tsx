// frontend/src/components/ResendTimer.tsx
import React, { useState, useEffect } from 'react';

interface ResendTimerProps {
  initialSeconds?: number;
  onResend: () => Promise<void> | void;
  disabled?: boolean;
  loading?: boolean;
  channel?: 'sms' | 'whatsapp';
  className?: string;
}

export const ResendTimer: React.FC<ResendTimerProps> = ({
  initialSeconds = 30,
  onResend,
  disabled = false,
  loading = false,
  channel = 'sms',
  className = '',
}) => {
  const [timeLeft, setTimeLeft] = useState<number>(initialSeconds);

  useEffect(() => {
    setTimeLeft(initialSeconds);
  }, [initialSeconds]);

  useEffect(() => {
    if (timeLeft <= 0) return;

    const timer = setInterval(() => {
      setTimeLeft((prev) => (prev > 0 ? prev - 1 : 0));
    }, 1000);

    return () => clearInterval(timer);
  }, [timeLeft]);

  const handleResendClick = async () => {
    if (timeLeft > 0 || disabled || loading) return;
    await onResend();
    setTimeLeft(initialSeconds);
  };

  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
  };

  return (
    <div className={`flex items-center justify-between text-xs sm:text-sm text-slate-400 ${className}`}>
      <span>Didn't receive the code?</span>
      {timeLeft > 0 ? (
        <span className="font-mono font-medium text-cyan-400 bg-cyan-950/40 px-2.5 py-1 rounded-md border border-cyan-800/40">
          Resend in {formatTime(timeLeft)}
        </span>
      ) : (
        <button
          type="button"
          id="resend-otp-btn"
          onClick={handleResendClick}
          disabled={disabled || loading}
          className="font-semibold text-cyan-400 hover:text-cyan-300 hover:underline transition-colors focus:outline-none disabled:opacity-50 flex items-center gap-1.5"
        >
          {loading ? (
            <span className="animate-spin inline-block w-3 h-3 border-2 border-cyan-400 border-t-transparent rounded-full" />
          ) : (
            <span>🔄</span>
          )}
          <span>Resend OTP via {channel === 'whatsapp' ? 'WhatsApp' : 'SMS'}</span>
        </button>
      )}
    </div>
  );
};

export default ResendTimer;
