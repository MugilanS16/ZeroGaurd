// src/pages/Emergency.jsx
import React from 'react';
import { Link } from 'react-router-dom';
import './Emergency.css';

const HELPLINES = [
  {
    name: 'National Cyber Crime Helpline',
    number: '1930',
    tel: '1930',
    type: 'Emergency Hotline',
    availability: '24×7 Available (Toll-Free)',
    desc: 'Government of India central helpline to immediately freeze unauthorized financial transactions and file FIRs.',
    highlight: true,
  },
  {
    name: 'RBI Banking Fraud Helpline',
    number: '14440',
    tel: '14440',
    type: 'Banking Security',
    availability: '24×7 Available',
    desc: 'Reserve Bank of India helpline for reporting unauthorized banking, card, or ATM fraud.',
  },
  {
    name: 'National Police Emergency',
    number: '112 / 100',
    tel: '112',
    type: 'Police Emergency',
    availability: '24×7 Available',
    desc: 'All-in-one emergency response support for cyber stalking, harassment, or physical threats.',
  },
  {
    name: 'Women & Child Cyber Helpline',
    number: '1091 / 181',
    tel: '1091',
    type: 'Specialized Cell',
    availability: '24×7 Available',
    desc: 'Dedicated support for online harassment, sextortion, and cyber bullying targeting women and minors.',
  },
];

const BANK_HOTLINES = [
  { bank: 'State Bank of India (SBI)', number: '1800 1234 / 1800 2100' },
  { bank: 'HDFC Bank Fraud Desk', number: '1800 202 6161' },
  { bank: 'ICICI Bank Emergency Block', number: '1800 1080' },
  { bank: 'Axis Bank Fraud Reporting', number: '1800 419 5959' },
  { bank: 'Punjab National Bank (PNB)', number: '1800 180 2222' },
  { bank: 'Bank of Baroda (BoB)', number: '1800 5700' },
];

export default function Emergency() {
  return (
    <div className="emergency-page page-wrapper container">
      {/* Top Banner */}
      <div className="emergency-top-hero card">
        <div className="emergency-hero-icon">🚨</div>
        <div>
          <div className="hero-badge">CRITICAL INCIDENT RESPONSE</div>
          <h1 className="emergency-hero-title">Emergency Cyber Helplines</h1>
          <p className="emergency-hero-desc">
            If money was debited from your account or you are experiencing active blackmail, call <strong>1930</strong> immediately. The first <strong>2 hours</strong> (Golden Hours) are critical to freeze illicit fund transfers.
          </p>
        </div>
      </div>

      {/* Main Helplines Grid */}
      <div className="helplines-grid">
        {HELPLINES.map((hl) => (
          <div
            key={hl.name}
            className={`helpline-item-card card ${hl.highlight ? 'highlight-card' : ''}`}
          >
            <div className="helpline-header">
              <span className="helpline-type">{hl.type}</span>
              <span className="helpline-status">{hl.availability}</span>
            </div>

            <h3 className="helpline-title">{hl.name}</h3>
            <p className="helpline-desc">{hl.desc}</p>

            <a href={`tel:${hl.tel}`} className={`btn ${hl.highlight ? 'btn-danger' : 'btn-primary'} btn-lg helpline-call-btn`}>
              📞 Call {hl.number}
            </a>
          </div>
        ))}
      </div>

      {/* Bank Emergency Blocking Numbers */}
      <div className="bank-section card">
        <h2 className="section-title">🏦 Bank Fraud Hotlines (Immediate Card & Account Freeze)</h2>
        <p className="bank-subtitle">
          If your debit/credit card or netbanking credentials have been compromised, contact your bank's fraud control unit immediately:
        </p>

        <div className="banks-grid">
          {BANK_HOTLINES.map((b) => (
            <div key={b.bank} className="bank-card">
              <span className="bank-name">{b.bank}</span>
              <span className="bank-num">📞 {b.number}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Next Steps CTA */}
      <div className="emergency-action-box card">
        <div>
          <h3>Ready to file your digital complaint?</h3>
          <p>Generate a formal complaint document with AI assistance to hand over to the investigating officer.</p>
        </div>
        <Link to="/report" className="btn btn-primary btn-lg">
          📋 File Cybercrime Report
        </Link>
      </div>
    </div>
  );
}
