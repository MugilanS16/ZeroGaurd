// src/components/Footer.jsx
import React from 'react';
import { Link } from 'react-router-dom';
import './Footer.css';

export default function Footer() {
  const year = new Date().getFullYear();
  return (
    <footer className="footer" role="contentinfo">
      <div className="footer-inner container">
        <div className="footer-brand">
          <span className="footer-logo-text">CrimeShield AI</span>
          <p>AI-powered cybercrime reporting for every Indian citizen.</p>
        </div>

        <div className="footer-links">
          <div className="footer-col">
            <h4>Platform</h4>
            <Link to="/">Home</Link>
            <Link to="/report">Report Crime</Link>
            <Link to="/chatbot">AI Assistant</Link>
            <Link to="/dashboard">Dashboard</Link>
          </div>
          <div className="footer-col">
            <h4>Resources</h4>
            <Link to="/awareness">Awareness</Link>
            <Link to="/emergency">Emergency Helplines</Link>
            <a href="https://cybercrime.gov.in" target="_blank" rel="noopener noreferrer">cybercrime.gov.in ↗</a>
          </div>
          <div className="footer-col">
            <h4>Helplines</h4>
            <a href="tel:1930">📞 1930 — Cyber Helpline</a>
            <a href="tel:14440">📞 14440 — RBI Fraud</a>
            <a href="tel:100">📞 100 — Police</a>
          </div>
        </div>
      </div>

      <div className="footer-bottom">
        <div className="container">
          <span>© {year} CrimeShield AI. Government of India Initiative.</span>
          <span className="footer-disclaimer">This is a demo portal. For official reporting visit <a href="https://cybercrime.gov.in" target="_blank" rel="noopener noreferrer">cybercrime.gov.in</a></span>
        </div>
      </div>
    </footer>
  );
}
