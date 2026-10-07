// frontend/src/components/ChannelToggle.tsx
import React from 'react';
import { OTPChannel } from '../types/auth';

interface ChannelToggleProps {
  selectedChannel: OTPChannel;
  onChange: (channel: OTPChannel) => void;
  disabled?: boolean;
  className?: string;
}

export const ChannelToggle: React.FC<ChannelToggleProps> = ({
  selectedChannel,
  onChange,
  disabled = false,
  className = '',
}) => {
  return (
    <div className={`flex flex-col gap-1.5 ${className}`}>
      <label className="text-xs font-semibold uppercase tracking-wider text-slate-400">
        Delivery Method
      </label>
      <div className="grid grid-cols-2 gap-2.5 p-1 bg-slate-900/90 rounded-xl border border-slate-800">
        {/* SMS Button */}
        <button
          type="button"
          id="toggle-channel-sms"
          disabled={disabled}
          onClick={() => onChange('sms')}
          className={`flex items-center justify-center gap-2 py-2.5 px-3 rounded-lg font-medium text-xs sm:text-sm transition-all duration-200 ${
            selectedChannel === 'sms'
              ? 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-lg shadow-blue-500/25 border border-blue-400/30'
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
          } disabled:opacity-50`}
        >
          <span className="text-base">📱</span>
          <span>SMS Text</span>
        </button>

        {/* WhatsApp Button */}
        <button
          type="button"
          id="toggle-channel-whatsapp"
          disabled={disabled}
          onClick={() => onChange('whatsapp')}
          className={`flex items-center justify-center gap-2 py-2.5 px-3 rounded-lg font-medium text-xs sm:text-sm transition-all duration-200 ${
            selectedChannel === 'whatsapp'
              ? 'bg-gradient-to-r from-emerald-600 to-teal-600 text-white shadow-lg shadow-emerald-500/25 border border-emerald-400/30'
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
          } disabled:opacity-50`}
        >
          <span className="text-base">💬</span>
          <span>WhatsApp</span>
        </button>
      </div>
    </div>
  );
};

export default ChannelToggle;
