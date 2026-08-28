// src/pages/ReportDetail.jsx
import React, { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { getReportById, updateReportStatus } from '../api/reports';
import { useAuth } from '../hooks/useAuth';
import SeverityBadge from '../components/SeverityBadge';
import LoadingSpinner from '../components/LoadingSpinner';
import toast from 'react-hot-toast';
import './ReportDetail.css';

export default function ReportDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { isAdmin } = useAuth();

  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(true);
  const [updating, setUpdating] = useState(false);

  useEffect(() => {
    setLoading(true);
    getReportById(id)
      .then((res) => {
        setReport(res.data.report);
      })
      .catch((err) => {
        console.error('Failed to load report detail:', err);
        toast.error('Could not load report details.');
        navigate('/dashboard');
      })
      .finally(() => {
        setLoading(false);
      });
  }, [id, navigate]);

  const handleStatusChange = async (newStatus) => {
    setUpdating(true);
    try {
      const res = await updateReportStatus(id, newStatus);
      setReport(res.data.report);
      toast.success(`Status updated to: ${newStatus}`);
    } catch (err) {
      console.error(err);
      toast.error('Failed to update status.');
    } finally {
      setUpdating(false);
    }
  };

  if (loading) {
    return <LoadingSpinner fullPage label="Retrieving investigation dossier…" />;
  }

  if (!report) {
    return null;
  }

  // Progress Stepper calculation
  const steps = ['Pending', 'In Review', 'Resolved'];
  const currentStepIdx = steps.indexOf(report.status);

  return (
    <div className="report-detail-page page-wrapper container">
      {/* Top Breadcrumb & Actions */}
      <div className="detail-top-nav">
        <Link to={isAdmin ? '/admin' : '/dashboard'} className="back-link">
          ← Back to {isAdmin ? 'Admin Console' : 'My Dashboard'}
        </Link>

        <div className="detail-actions">
          <button
            onClick={() => window.print()}
            className="btn btn-secondary btn-sm"
            title="Print or Save PDF"
          >
            🖨️ Print Dossier
          </button>
        </div>
      </div>

      {/* Main Header Banner */}
      <div className="detail-header-card card">
        <div className="detail-header-main">
          <div className="ref-badge-group">
            <span className="case-label">CYBERCRIME DOSSIER</span>
            <h1 className="case-ref-number">{report.reference_number}</h1>
          </div>
          <div className="badges-row">
            <SeverityBadge severity={report.severity || 'medium'} />
            <span className={`badge status-${report.status?.toLowerCase().replace(' ', '-')}`}>
              {report.status === 'Resolved' ? '✅' : report.status === 'In Review' ? '🔍' : '⏳'}{' '}
              {report.status}
            </span>
          </div>
        </div>

        {/* Investigation Stepper */}
        <div className="stepper-wrapper">
          <div className="stepper-track">
            {steps.map((stepName, idx) => {
              const isCompleted = idx <= currentStepIdx;
              const isCurrent = idx === currentStepIdx;
              return (
                <div
                  key={stepName}
                  className={`stepper-item ${isCompleted ? 'completed' : ''} ${isCurrent ? 'active' : ''}`}
                >
                  <div className="step-circle">
                    {idx < currentStepIdx ? '✓' : idx + 1}
                  </div>
                  <span className="step-title">{stepName}</span>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Detail Layout */}
      <div className="detail-grid">
        {/* Left Column: Complaint & Evidence */}
        <div className="detail-left">
          {/* Incident Description */}
          <div className="detail-section card">
            <h3 className="section-title">📝 Incident Description</h3>
            <div className="description-box">
              <p>{report.description}</p>
            </div>
          </div>

          {/* Structured Answers / Metadata */}
          {report.answers && report.answers.length > 0 && (
            <div className="detail-section card">
              <h3 className="section-title">📋 Case Specifics & Information</h3>
              <div className="qa-list">
                {report.answers.map((qa, idx) => (
                  <div key={idx} className="qa-item">
                    <span className="qa-question">{qa.question}</span>
                    <span className="qa-answer">{qa.answer || 'Not provided'}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Extracted Evidence Entities */}
          {report.entities && report.entities.length > 0 && (
            <div className="detail-section card">
              <h3 className="section-title">🔍 AI Identified Evidence Entities</h3>
              <div className="entities-chips">
                {report.entities.map((ent, idx) => (
                  <span key={idx} className="entity-chip">
                    🏷️ {ent}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Right Column: AI Analysis & Admin Controls */}
        <div className="detail-right">
          {/* Admin Workflow Card */}
          {isAdmin && (
            <div className="detail-section card admin-workflow-card">
              <h3 className="section-title">⚡ Case Management</h3>
              <p className="admin-help-text">Update investigation status for this complaint:</p>
              <div className="status-button-group">
                {['Pending', 'In Review', 'Resolved'].map((st) => (
                  <button
                    key={st}
                    disabled={updating || report.status === st}
                    onClick={() => handleStatusChange(st)}
                    className={`btn ${report.status === st ? 'btn-primary' : 'btn-secondary'} btn-sm`}
                  >
                    {st}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* AI Guidance Card */}
          <div className="detail-section card">
            <h3 className="section-title">🤖 Recommended Safety Protocol</h3>
            {report.recommended_action && (
              <div className="immediate-action-alert">
                <strong>Priority Action:</strong> {report.recommended_action}
              </div>
            )}
            {report.guidance && report.guidance.length > 0 ? (
              <ul className="guidance-steps-list">
                {report.guidance.map((step, idx) => (
                  <li key={idx}>
                    <span className="step-num-pill">{idx + 1}</span>
                    <span>{step}</span>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="empty-text">Standard precautions apply. Contact 1930 for guidance.</p>
            )}
          </div>

          {/* Emergency Helpline Box */}
          <div className="detail-section card helpline-card">
            <div className="helpline-icon">📞</div>
            <div>
              <h4>Need Emergency Assistance?</h4>
              <p>National Cyber Crime Helpline (24×7)</p>
              <a href="tel:1930" className="helpline-btn">
                Call 1930 Free
              </a>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
