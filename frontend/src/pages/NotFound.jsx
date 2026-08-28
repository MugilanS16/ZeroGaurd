// src/pages/NotFound.jsx
import React from 'react';
import { Link } from 'react-router-dom';

export default function NotFound() {
  return (
    <div className="page-wrapper" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <div style={{ textAlign: 'center', padding: '4rem 1rem' }}>
        <div style={{ fontSize: '5rem', marginBottom: '1rem' }}>🔍</div>
        <h2 style={{ fontSize: '3rem', fontWeight: 900, background: 'var(--brand-gradient)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>404</h2>
        <h3 style={{ marginTop: '0.5rem' }}>Page Not Found</h3>
        <p style={{ marginTop: '0.5rem', color: 'var(--text-muted)' }}>The page you're looking for doesn't exist or has been moved.</p>
        <div style={{ marginTop: '2rem', display: 'flex', gap: '1rem', justifyContent: 'center', flexWrap: 'wrap' }}>
          <Link to="/" className="btn btn-primary">Go Home</Link>
          <Link to="/report" className="btn btn-secondary">Report a Crime</Link>
        </div>
      </div>
    </div>
  );
}
