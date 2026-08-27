// src/components/SeverityBadge.jsx
import React from 'react';

const SEVERITY_CONFIG = {
  low:      { label: 'Low',      color: 'var(--severity-low)',      bg: 'var(--severity-low-bg)',      icon: '🟢' },
  medium:   { label: 'Medium',   color: 'var(--severity-medium)',   bg: 'var(--severity-medium-bg)',   icon: '🟡' },
  high:     { label: 'High',     color: 'var(--severity-high)',     bg: 'var(--severity-high-bg)',     icon: '🟠' },
  critical: { label: 'Critical', color: 'var(--severity-critical)', bg: 'var(--severity-critical-bg)', icon: '🔴' },
};

// Map backend risk strings to our severity keys
function normalizeSeverity(raw) {
  if (!raw) return 'medium';
  const lower = raw.toString().toLowerCase();
  if (lower.includes('critical')) return 'critical';
  if (lower.includes('high'))     return 'high';
  if (lower.includes('low'))      return 'low';
  return 'medium';
}

/**
 * @param {string} severity - 'low' | 'medium' | 'high' | 'critical' (or backend risk string)
 * @param {boolean} showIcon
 * @param {string}  size    - 'sm' | 'md'
 */
export default function SeverityBadge({ severity, showIcon = true, size = 'md' }) {
  const key = normalizeSeverity(severity);
  const cfg = SEVERITY_CONFIG[key] || SEVERITY_CONFIG.medium;

  return (
    <span
      className="badge"
      style={{
        color: cfg.color,
        background: cfg.bg,
        border: `1px solid ${cfg.color}40`,
        fontSize: size === 'sm' ? '0.7rem' : '0.75rem',
        padding: size === 'sm' ? '0.15rem 0.5rem' : '0.25rem 0.65rem',
      }}
      aria-label={`Severity: ${cfg.label}`}
    >
      {showIcon && <span aria-hidden="true">{cfg.icon}</span>}
      {cfg.label}
    </span>
  );
}
