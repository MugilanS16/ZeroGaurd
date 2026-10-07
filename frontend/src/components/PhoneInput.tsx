// frontend/src/components/PhoneInput.tsx
import React, { useState, ChangeEvent } from 'react';

interface CountryCode {
  code: string;
  dialCode: string;
  name: string;
  flag: string;
}

const COUNTRIES: CountryCode[] = [
  { code: 'IN', dialCode: '+91', name: 'India', flag: '🇮🇳' },
  { code: 'US', dialCode: '+1', name: 'United States', flag: '🇺🇸' },
  { code: 'GB', dialCode: '+44', name: 'United Kingdom', flag: '🇬🇧' },
  { code: 'AE', dialCode: '+971', name: 'United Arab Emirates', flag: '🇦🇪' },
  { code: 'SG', dialCode: '+65', name: 'Singapore', flag: '🇸🇬' },
  { code: 'AU', dialCode: '+61', name: 'Australia', flag: '🇦🇺' },
  { code: 'CA', dialCode: '+1', name: 'Canada', flag: '🇨🇦' },
];

interface PhoneInputProps {
  value: string;
  onChange: (fullE164: string, rawDigits: string) => void;
  disabled?: boolean;
  required?: boolean;
  placeholder?: string;
  id?: string;
  className?: string;
}

export const PhoneInput: React.FC<PhoneInputProps> = ({
  value,
  onChange,
  disabled = false,
  required = false,
  placeholder = '98765 43210',
  id = 'phone-input',
  className = '',
}) => {
  const [selectedDialCode, setSelectedDialCode] = useState<string>('+91');
  const [digits, setDigits] = useState<string>(() => {
    if (value.startsWith('+91')) return value.slice(3).trim();
    if (value.startsWith('+')) {
      const match = COUNTRIES.find((c) => value.startsWith(c.dialCode));
      if (match) return value.slice(match.dialCode.length).trim();
    }
    return value;
  });

  const handleCountryChange = (e: ChangeEvent<HTMLSelectElement>) => {
    const newCode = e.target.value;
    setSelectedDialCode(newCode);
    const cleanDigits = digits.replace(/\D/g, '');
    onChange(`${newCode}${cleanDigits}`, cleanDigits);
  };

  const handleDigitsChange = (e: ChangeEvent<HTMLInputElement>) => {
    const raw = e.target.value;
    const cleanDigits = raw.replace(/\D/g, '').slice(0, 15);
    setDigits(cleanDigits);
    onChange(`${selectedDialCode}${cleanDigits}`, cleanDigits);
  };

  return (
    <div className={`relative flex items-center rounded-xl bg-slate-900/80 border border-slate-700/80 focus-within:border-cyan-500 focus-within:ring-2 focus-within:ring-cyan-500/20 transition-all duration-200 shadow-inner ${className}`}>
      {/* Country Selector */}
      <div className="relative flex items-center pl-3 pr-2 border-r border-slate-700/80">
        <select
          id={`${id}-country`}
          value={selectedDialCode}
          onChange={handleCountryChange}
          disabled={disabled}
          className="appearance-none bg-transparent text-sm font-medium text-slate-200 pr-5 py-2.5 focus:outline-none cursor-pointer disabled:opacity-50"
          title="Select Country Dial Code"
        >
          {COUNTRIES.map((c) => (
            <option key={c.code} value={c.dialCode} className="bg-slate-900 text-slate-100">
              {c.flag} {c.dialCode} ({c.code})
            </option>
          ))}
        </select>
        <span className="pointer-events-none absolute right-1 text-slate-400 text-xs">▼</span>
      </div>

      {/* Number Input */}
      <input
        id={id}
        type="tel"
        value={digits}
        onChange={handleDigitsChange}
        disabled={disabled}
        required={required}
        placeholder={placeholder}
        className="w-full bg-transparent px-3.5 py-2.5 text-slate-100 placeholder-slate-500 text-sm font-medium focus:outline-none disabled:opacity-50 tracking-wider"
        autoComplete="tel"
      />
    </div>
  );
};

export default PhoneInput;
