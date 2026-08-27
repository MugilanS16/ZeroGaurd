// src/components/LoadingSpinner.jsx
import React from 'react';
import './LoadingSpinner.css';

/**
 * @param {string} size - 'sm' | 'md' | 'lg'
 * @param {string} label - Accessibility label
 * @param {boolean} fullPage - Centers on full viewport
 */
export default function LoadingSpinner({ size = 'md', label = 'Loading...', fullPage = false }) {
  return (
    <div className={`spinner-wrapper${fullPage ? ' spinner-fullpage' : ''}`} role="status" aria-label={label}>
      <div className={`spinner spinner-${size}`} aria-hidden="true" />
      {fullPage && <p className="spinner-label">{label}</p>}
    </div>
  );
}
