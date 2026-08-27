// src/pages/ReportForm.jsx
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useDebounce } from '../hooks/useDebounce';
import { analyzeText, enhanceReport } from '../api/aiCrime';
import { submitReport } from '../api/reports';
import SeverityBadge from '../components/SeverityBadge';
import LoadingSpinner from '../components/LoadingSpinner';
import toast from 'react-hot-toast';
import './ReportForm.css';

export default function ReportForm() {
  const navigate = useNavigate();

  // Form State
  const [description, setDescription] = useState('');
  const [incidentDate, setIncidentDate] = useState(
    new Date().toISOString().split('T')[0]
  );
  const [financialLoss, setFinancialLoss] = useState('');
  const [suspectInfo, setSuspectInfo] = useState({
    nameOrHandle: '',
    phoneOrUpi: '',
    websiteOrLink: '',
  });

  // AI Live Feedback State
  const [aiData, setAiData] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [isPolishing, setIsPolishing] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Debounced description for live AI analysis (600ms)
  const debouncedDescription = useDebounce(description, 600);

  // Trigger live AI analysis when debounced description changes
  useEffect(() => {
    if (!debouncedDescription || debouncedDescription.trim().length < 15) {
      setAiData(null);
      return;
    }

    let isMounted = true;
    setIsAnalyzing(true);

    analyzeText(debouncedDescription)
      .then((res) => {
        if (isMounted) {
          setAiData(res.data);
        }
      })
      .catch((err) => {
        console.error('AI Analysis failed:', err);
      })
      .finally(() => {
        if (isMounted) {
          setIsAnalyzing(false);
        }
      });

    return () => {
      isMounted = false;
    };
  }, [debouncedDescription]);

  // AI Polish / Enhance Description
  const handleAiPolish = async () => {
    if (description.trim().length < 15) {
      toast.error('Please enter at least 15 characters before using AI Polish.');
      return;
    }

    setIsPolishing(true);
    const toastId = toast.loading('AI is formatting and polishing your complaint…');
    try {
      const res = await enhanceReport(description);
      if (res.data?.enhanced_text) {
        setDescription(res.data.enhanced_text);
        toast.success('Description formatted professionally!', { id: toastId });
      } else {
        toast.error('Could not polish text at this moment.', { id: toastId });
      }
    } catch (err) {
      console.error(err);
      toast.error('AI Polish service unavailable. Continuing with original.', { id: toastId });
    } finally {
      setIsPolishing(false);
    }
  };

  // Submit Handler
  const handleSubmit = async (e) => {
    e.preventDefault();

    if (description.trim().length < 20) {
      toast.error('Please describe the incident in at least 20 characters.');
      return;
    }

    setIsSubmitting(true);
    const toastId = toast.loading('Submitting your cybercrime complaint…');

    try {
      const payload = {
        description: description.trim(),
        crime_type: aiData?.crime_type || 'Unknown Cyber Incident',
        severity: aiData?.severity || 'medium',
        entities: aiData?.entities || [],
        recommended_action: aiData?.recommended_action || '',
        guidance: aiData?.guidance || [],
        answers: [
          { question: 'Incident Date', answer: incidentDate || 'Not specified' },
          { question: 'Financial Loss (INR)', answer: financialLoss ? `₹${financialLoss}` : 'None' },
          { question: 'Suspect Identifier', answer: suspectInfo.phoneOrUpi || suspectInfo.nameOrHandle || 'Not provided' },
          { question: 'Suspect Platform/URL', answer: suspectInfo.websiteOrLink || 'Not provided' },
        ],
      };

      const res = await submitReport(payload);
      toast.success(
        `Report submitted successfully! Ref: ${res.data.report.reference_number}`,
        { id: toastId, duration: 5000 }
      );
      navigate(`/reports/${res.data.report.id}`);
    } catch (err) {
      console.error(err);
      const msg = err.response?.data?.message || 'Failed to submit report. Please try again.';
      toast.error(msg, { id: toastId });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="report-page page-wrapper container">
      <div className="page-header">
        <div className="section-eyebrow">SMART REPORTING PORTAL</div>
        <h1 className="page-title">File a Cybercrime Report</h1>
        <p className="page-subtitle">
          Describe the incident naturally in any language. Our AI will classify the crime, assess the risk, and prepare a legal-grade report.
        </p>
      </div>

      <div className="report-layout">
        {/* LEFT COLUMN: Input Form */}
        <div className="report-form-container card">
          <form onSubmit={handleSubmit} className="report-form" noValidate>
            {/* Description Textarea */}
            <div className="form-group">
              <div className="label-with-action">
                <label htmlFor="incident-description" className="form-label">
                  Incident Description <span className="required-mark">*</span>
                </label>
                <button
                  type="button"
                  onClick={handleAiPolish}
                  disabled={isPolishing || description.length < 15}
                  className="btn-ai-polish"
                  title="Enhance structure and legal phrasing with AI"
                >
                  {isPolishing ? '✨ Polishing…' : '✨ AI Polish'}
                </button>
              </div>

              <textarea
                id="incident-description"
                className="form-textarea incident-textarea"
                rows="7"
                placeholder="Example: Yesterday at 3 PM, I received a WhatsApp message claiming to be from my bank asking to update KYC. I clicked the link (fakebank-verify.in) and entered my details. Shortly after, ₹45,000 was debited via UPI to merchant ID 9876543210@paytm..."
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                required
              />

              <div className="textarea-footer">
                <span className={`char-counter ${description.length < 20 ? 'warning' : 'valid'}`}>
                  {description.length} characters (min. 20)
                </span>
                {isAnalyzing && (
                  <span className="live-ai-badge">
                    <span className="pulse-dot"></span> AI analyzing live…
                  </span>
                )}
              </div>
            </div>

            <hr className="divider" />

            {/* Additional Metadata */}
            <h3 className="section-subheading">Incident Details</h3>
            <div className="grid-2">
              <div className="form-group">
                <label htmlFor="incident-date" className="form-label">Date of Incident</label>
                <input
                  id="incident-date"
                  type="date"
                  className="form-input"
                  value={incidentDate}
                  onChange={(e) => setIncidentDate(e.target.value)}
                  max={new Date().toISOString().split('T')[0]}
                />
              </div>

              <div className="form-group">
                <label htmlFor="financial-loss" className="form-label">Approximate Financial Loss (₹)</label>
                <input
                  id="financial-loss"
                  type="number"
                  min="0"
                  step="1"
                  className="form-input"
                  placeholder="e.g. 25000"
                  value={financialLoss}
                  onChange={(e) => setFinancialLoss(e.target.value)}
                />
              </div>
            </div>

            {/* Suspect Info (Optional) */}
            <h3 className="section-subheading" style={{ marginTop: '1rem' }}>
              Suspect Information <span className="optional-tag">(Optional)</span>
            </h3>
            <div className="grid-3">
              <div className="form-group">
                <label htmlFor="suspect-name" className="form-label">Name / Social Handle</label>
                <input
                  id="suspect-name"
                  type="text"
                  className="form-input"
                  placeholder="@fake_account"
                  value={suspectInfo.nameOrHandle}
                  onChange={(e) =>
                    setSuspectInfo({ ...suspectInfo, nameOrHandle: e.target.value })
                  }
                />
              </div>

              <div className="form-group">
                <label htmlFor="suspect-contact" className="form-label">Phone / UPI ID</label>
                <input
                  id="suspect-contact"
                  type="text"
                  className="form-input"
                  placeholder="+91 98765... or user@upi"
                  value={suspectInfo.phoneOrUpi}
                  onChange={(e) =>
                    setSuspectInfo({ ...suspectInfo, phoneOrUpi: e.target.value })
                  }
                />
              </div>

              <div className="form-group">
                <label htmlFor="suspect-url" className="form-label">Fraudulent Website / Link</label>
                <input
                  id="suspect-url"
                  type="text"
                  className="form-input"
                  placeholder="https://..."
                  value={suspectInfo.websiteOrLink}
                  onChange={(e) =>
                    setSuspectInfo({ ...suspectInfo, websiteOrLink: e.target.value })
                  }
                />
              </div>
            </div>

            {/* Submit Action */}
            <div className="form-submit-row">
              <button
                id="submit-report-btn"
                type="submit"
                className="btn btn-primary btn-lg"
                disabled={isSubmitting || description.trim().length < 20}
              >
                {isSubmitting ? (
                  <>
                    <LoadingSpinner size="sm" /> Filing Complaint…
                  </>
                ) : (
                  '🛡️ Submit Official Complaint'
                )}
              </button>
              <p className="privacy-notice">
                🔒 Protected by automated PII redaction and secure zero-trust storage.
              </p>
            </div>
          </form>
        </div>

        {/* RIGHT COLUMN: Live AI Feedback Panel */}
        <aside className="ai-feedback-panel card" aria-live="polite">
          <div className="ai-panel-header">
            <div className="ai-icon-badge">🤖</div>
            <div>
              <h3>AI Threat Intelligence</h3>
              <p>Real-time incident classification & analysis</p>
            </div>
          </div>

          {!aiData || !aiData.crime_type ? (
            <div className="ai-placeholder">
              <div className="ai-placeholder-icon">✍️</div>
              <h4>Start Typing Your Incident</h4>
              <p>
                As you describe what happened, our AI will automatically detect the crime category, calculate severity, and extract key evidence.
              </p>
              <div className="ai-hint-box">
                💡 <strong>Tip:</strong> Include specific details like timestamps, platform names (WhatsApp, Instagram, UPI app), and any links received.
              </div>
            </div>
          ) : (
            <div className="ai-analysis-results animate-fade-in">
              {/* Classification Card */}
              <div className="ai-result-block">
                <span className="ai-block-label">Predicted Crime Category</span>
                <div className="ai-crime-category">
                  <h4>{aiData.crime_type}</h4>
                  <span className="method-pill">
                    {aiData.method === 'ai' ? '✨ AI Model' : '⚡ Rule Engine'}
                  </span>
                </div>
              </div>

              {/* Severity & Threat Score */}
              <div className="ai-result-block">
                <div className="severity-row">
                  <div>
                    <span className="ai-block-label">Severity Level</span>
                    <div style={{ marginTop: '0.35rem' }}>
                      <SeverityBadge severity={aiData.severity || 'medium'} />
                    </div>
                  </div>
                  <div className="threat-score-box">
                    <span className="ai-block-label">Threat Score</span>
                    <span className="threat-score-val">{aiData.risk_score || 70}/100</span>
                  </div>
                </div>

                {/* Severity Bar */}
                <div className="threat-meter">
                  <div
                    className={`threat-meter-fill severity-${aiData.severity || 'medium'}`}
                    style={{ width: `${aiData.risk_score || 70}%` }}
                  />
                </div>
              </div>

              {/* Extracted Entities */}
              {aiData.entities && aiData.entities.length > 0 && (
                <div className="ai-result-block">
                  <span className="ai-block-label">Detected Evidence & Entities</span>
                  <div className="entities-chips">
                    {aiData.entities.map((entity, idx) => (
                      <span key={idx} className="entity-chip">
                        🔍 {entity}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Recommended Action */}
              {aiData.recommended_action && (
                <div className="ai-result-block recommendation-block">
                  <span className="ai-block-label">Recommended Immediate Action</span>
                  <p className="recommendation-text">
                    ⚡ <strong>{aiData.recommended_action}</strong>
                  </p>
                </div>
              )}

              {/* Step-by-Step Guidance Preview */}
              {aiData.guidance && aiData.guidance.length > 0 && (
                <div className="ai-result-block">
                  <span className="ai-block-label">Victim Protection Steps</span>
                  <ul className="guidance-list">
                    {aiData.guidance.slice(0, 3).map((step, idx) => (
                      <li key={idx}>
                        <span className="step-badge">{idx + 1}</span>
                        <span>{step}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Emergency reminder for critical */}
              {(aiData.severity === 'critical' || aiData.severity === 'high') && (
                <div className="ai-critical-alert">
                  🚨 <strong>High-risk incident detected!</strong> We recommend calling <strong>1930</strong> immediately to freeze financial transactions.
                </div>
              )}
            </div>
          )}
        </aside>
      </div>
    </div>
  );
}
