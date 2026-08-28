// src/pages/Home.jsx
import React from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import './Home.css';

const FEATURES = [
  { icon: '🤖', title: 'AI Crime Classification', desc: 'Our model identifies 15+ cybercrime types instantly from your description — UPI fraud, phishing, sextortion, ransomware, and more.' },
  { icon: '⚡', title: 'Live Risk Assessment', desc: 'Get a real-time severity score and colour-coded risk rating as you type. Know how urgent your case is before you finish writing.' },
  { icon: '🔍', title: 'Entity Extraction', desc: 'AI automatically surfaces phone numbers, UPI IDs, URLs, bank names, and amounts from your text — no manual highlighting needed.' },
  { icon: '📋', title: 'Legal-Grade PDF Report', desc: 'Generate a formal, structured complaint document in one click — ready to submit to cybercrime.gov.in or your local cyber cell.' },
  { icon: '💬', title: 'AI Safety Chatbot', desc: 'Step-by-step safety guidance, tailored to your crime type. Available 24×7 via the floating chat widget.' },
  { icon: '🛡️', title: 'Privacy-First Redaction', desc: 'Sensitive details like Aadhaar numbers and phone numbers are automatically redacted before any AI processing.' },
];

const STEPS = [
  { num: '01', title: 'Describe Your Incident', desc: 'Type what happened in plain language — any Indian language works.' },
  { num: '02', title: 'AI Analysis', desc: 'Crime type, severity, and evidence entities are extracted in real time.' },
  { num: '03', title: 'Review & Submit', desc: 'Confirm AI findings and file your report with a single click.' },
  { num: '04', title: 'Track Status', desc: 'Monitor your complaint status directly from your dashboard.' },
];

const STATS = [
  { value: '15+', label: 'Crime Categories' },
  { value: '1930', label: 'Emergency Helpline' },
  { value: '24×7', label: 'AI Assistance' },
  { value: '100%', label: 'Privacy Protected' },
];

export default function Home() {
  const { isAuthenticated } = useAuth();

  return (
    <div className="home-page">
      {/* HERO */}
      <section className="hero" aria-labelledby="hero-heading">
        <div className="hero-bg-orb hero-orb-1" aria-hidden="true" />
        <div className="hero-bg-orb hero-orb-2" aria-hidden="true" />
        <div className="hero-bg-grid" aria-hidden="true" />

        <div className="hero-content container">
          <div className="hero-badge animate-fade-up">
            <span className="pulse-dot" aria-hidden="true" />
            AI-POWERED CYBER PROTECTION
          </div>

          <h1 id="hero-heading" className="hero-title animate-fade-up" style={{ animationDelay: '0.1s' }}>
            Report Cybercrime<br />with <span className="hero-title-gradient">Smart AI</span>
          </h1>

          <p className="hero-desc animate-fade-up" style={{ animationDelay: '0.2s' }}>
            Describe your incident in plain words. Our AI classifies the threat, guides you step-by-step,
            and generates a legal-grade complaint document — all in minutes.
          </p>

          <div className="hero-cta animate-fade-up" style={{ animationDelay: '0.3s' }}>
            {isAuthenticated ? (
              <>
                <Link to="/report" className="btn btn-primary btn-lg" id="hero-report-btn">
                  📋 Report an Incident
                </Link>
                <Link to="/dashboard" className="btn btn-secondary btn-lg" id="hero-dashboard-btn">
                  📊 My Dashboard
                </Link>
              </>
            ) : (
              <>
                <Link to="/register" className="btn btn-primary btn-lg" id="hero-register-btn">
                  🚀 Get Started Free
                </Link>
                <Link to="/login" className="btn btn-secondary btn-lg" id="hero-login-btn">
                  Sign In
                </Link>
              </>
            )}
          </div>

          {/* Stats bar */}
          <div className="hero-stats animate-fade-up" style={{ animationDelay: '0.4s' }} aria-label="Platform statistics">
            {STATS.map((s) => (
              <div key={s.label} className="hero-stat">
                <span className="hero-stat-value">{s.value}</span>
                <span className="hero-stat-label">{s.label}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* HOW IT WORKS */}
      <section className="section" aria-labelledby="how-heading">
        <div className="container">
          <div className="section-header">
            <div className="section-eyebrow">HOW IT WORKS</div>
            <h2 id="how-heading">From Incident to Report in 4 Steps</h2>
            <p>Our streamlined process makes cybercrime reporting simple, fast, and stress-free.</p>
          </div>

          <div className="steps-grid">
            {STEPS.map((step, i) => (
              <div key={step.num} className="step-card card animate-fade-up" style={{ animationDelay: `${i * 0.1}s` }}>
                <div className="step-num">{step.num}</div>
                <h3 className="step-title">{step.title}</h3>
                <p className="step-desc">{step.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* FEATURES */}
      <section className="section section-alt" aria-labelledby="features-heading">
        <div className="container">
          <div className="section-header">
            <div className="section-eyebrow">FEATURES</div>
            <h2 id="features-heading">Everything You Need to Fight Cybercrime</h2>
            <p>Powered by Google Gemini AI and India's national cybercrime framework.</p>
          </div>

          <div className="features-grid">
            {FEATURES.map((feat, i) => (
              <div key={feat.title} className="feature-card card animate-fade-up" style={{ animationDelay: `${i * 0.08}s` }}>
                <div className="feature-icon" aria-hidden="true">{feat.icon}</div>
                <h3 className="feature-title">{feat.title}</h3>
                <p className="feature-desc">{feat.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* EMERGENCY CTA */}
      <section className="section" aria-labelledby="emergency-heading">
        <div className="container">
          <div className="emergency-cta card">
            <div className="emergency-cta-left">
              <div className="emergency-icon" aria-hidden="true">🚨</div>
              <div>
                <h2 id="emergency-heading">In an Active Cyber Emergency?</h2>
                <p>Don't wait — call the 24×7 National Cyber Crime Helpline immediately. Every minute counts.</p>
              </div>
            </div>
            <div className="emergency-cta-actions">
              <a href="tel:1930" className="btn btn-danger btn-lg" id="emergency-call-btn" aria-label="Call 1930 cybercrime helpline">
                📞 Call 1930
              </a>
              <Link to="/emergency" className="btn btn-secondary btn-lg" id="all-helplines-btn">
                View All Helplines
              </Link>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
