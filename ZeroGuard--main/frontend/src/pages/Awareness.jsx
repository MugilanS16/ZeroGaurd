// src/pages/Awareness.jsx
import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import './Awareness.css';

const SCAM_TOPICS = [
  {
    id: 'upi',
    title: 'UPI & Payment Scams',
    icon: '💳',
    summary: 'Fraudsters send fake payment requests or QR codes claiming you will receive money.',
    redFlags: [
      'Entering your UPI PIN to "receive" money (PIN is ONLY for sending money)',
      'Scanning QR codes to claim rewards or prizes',
      'Requests to install remote screen sharing apps like AnyDesk or TeamViewer',
    ],
    safetyTips: [
      'Never share your UPI PIN or OTP with anyone.',
      'Remember: You NEVER need to enter your PIN to receive funds.',
      'Verify the recipient name carefully before hitting confirm.',
    ],
  },
  {
    id: 'phishing',
    title: 'Phishing & Fake KYC Links',
    icon: '🎣',
    summary: 'SMS or WhatsApp messages warning your SIM or bank account will be blocked without immediate KYC update.',
    redFlags: [
      'Urgent threats of account suspension within 24 hours',
      'Unofficial domain names (e.g. sbi-kyc-update.xyz instead of onlinesbi.sbi)',
      'Unsolicited APK file downloads sent over WhatsApp or Telegram',
    ],
    safetyTips: [
      'Banks never send links asking to update KYC via SMS.',
      'Always visit your official bank branch or verified mobile banking app.',
      'Check website URLs carefully for misspellings or unofficial extensions.',
    ],
  },
  {
    id: 'job',
    title: 'Work From Home & Job Scams',
    icon: '💼',
    summary: 'Promises of easy daily income for liking YouTube videos, reviewing hotels, or crypto trading.',
    redFlags: [
      'Job offers without any interview or formal company verification',
      'Requirement to deposit "security fees" or "prepaid task funds"',
      'High guaranteed returns (e.g. "Earn ₹5,000 daily from home")',
    ],
    safetyTips: [
      'Legitimate employers never ask candidates to pay for a job.',
      'Verify company registration on MCA / LinkedIn.',
      'Never join unsolicited Telegram investment task groups.',
    ],
  },
  {
    id: 'sextortion',
    title: 'Sextortion & Video Call Blackmail',
    icon: '📹',
    summary: 'Unknown video calls where intimate or morphed clips are recorded and used for financial extortion.',
    redFlags: [
      'Video calls from unknown numbers on WhatsApp or Instagram',
      'Threats to share videos with your contacts or social media friends',
      'Demands for immediate money transfer to avoid defamation',
    ],
    safetyTips: [
      'Do NOT pay money — extortionists will keep demanding more.',
      'Immediately block and report the number on WhatsApp/Instagram.',
      'Preserve screenshots and call 1930 immediately.',
    ],
  },
];

export default function Awareness() {
  const [activeTopic, setActiveTopic] = useState('upi');

  const currentScam = SCAM_TOPICS.find((t) => t.id === activeTopic) || SCAM_TOPICS[0];

  return (
    <div className="awareness-page page-wrapper container">
      <div className="page-header">
        <div className="section-eyebrow">CITIZEN AWARENESS & EDUCATION</div>
        <h1 className="page-title">Cybercrime Prevention Guide</h1>
        <p className="page-subtitle">
          Learn how modern cyber scams operate, spot red flags before becoming a victim, and protect your digital life.
        </p>
      </div>

      {/* Interactive Tabs */}
      <div className="scam-tabs">
        {SCAM_TOPICS.map((topic) => (
          <button
            key={topic.id}
            className={`scam-tab-btn ${activeTopic === topic.id ? 'active' : ''}`}
            onClick={() => setActiveTopic(topic.id)}
          >
            <span className="scam-tab-icon">{topic.icon}</span>
            <span>{topic.title}</span>
          </button>
        ))}
      </div>

      {/* Active Scam Deep Dive */}
      <div className="scam-detail-card card animate-fade-in">
        <div className="scam-detail-header">
          <div className="scam-detail-icon">{currentScam.icon}</div>
          <div>
            <h2>{currentScam.title}</h2>
            <p>{currentScam.summary}</p>
          </div>
        </div>

        <div className="scam-columns grid-2">
          {/* Red Flags */}
          <div className="scam-block red-flags-block">
            <h3 className="block-title">🚩 Red Flags to Watch Out For</h3>
            <ul className="scam-list">
              {currentScam.redFlags.map((flag, idx) => (
                <li key={idx}>
                  <span className="bullet-cross">✕</span>
                  <span>{flag}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* Safety Checklist */}
          <div className="scam-block safety-block">
            <h3 className="block-title">🛡️ Recommended Protection Measures</h3>
            <ul className="scam-list">
              {currentScam.safetyTips.map((tip, idx) => (
                <li key={idx}>
                  <span className="bullet-check">✓</span>
                  <span>{tip}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>

        <div className="scam-footer-cta">
          <div>
            <h4>Already targeted by this scam?</h4>
            <p>File a report or get instant AI assistance to freeze transactions.</p>
          </div>
          <div style={{ display: 'flex', gap: '0.75rem' }}>
            <Link to="/report" className="btn btn-primary">
              📋 File a Report
            </Link>
            <a href="tel:1930" className="btn btn-danger">
              📞 Call 1930
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}
