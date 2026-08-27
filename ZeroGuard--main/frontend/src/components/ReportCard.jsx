// src/components/ReportCard.jsx
import React from 'react';
import { Link } from 'react-router-dom';
import SeverityBadge from './SeverityBadge';
import './ReportCard.css';

function formatDate(dateStr) {
  if (!dateStr) return 'Unknown date';
  return new Date(dateStr).toLocaleDateString('en-IN', {
    day: '2-digit', month: 'short', year: 'numeric',
  });
}

const STATUS_MAP = {
  'Pending':   { cls: 'status-pending',  icon: '⏳' },
  'In Review': { cls: 'status-review',   icon: '🔍' },
  'Resolved':  { cls: 'status-resolved', icon: '✅' },
};

export default function ReportCard({ report }) {
  const { id, reference_number, crime_type, status, severity, created_at, description } = report;
  const statusInfo = STATUS_MAP[status] || STATUS_MAP['Pending'];

  return (
    <Link to={`/reports/${id}`} className="report-card card" id={`report-card-${id}`} aria-label={`Report ${reference_number}`}>
      <div className="report-card-header">
        <div className="report-card-ref">{reference_number}</div>
        <span className={`badge ${statusInfo.cls}`}>
          {statusInfo.icon} {status}
        </span>
      </div>

      <div className="report-card-type">{crime_type || 'Unknown Crime Type'}</div>

      <p className="report-card-desc">
        {description ? description.slice(0, 120) + (description.length > 120 ? '…' : '') : 'No description available.'}
      </p>

      <div className="report-card-footer">
        <SeverityBadge severity={severity || 'medium'} size="sm" />
        <span className="report-card-date">📅 {formatDate(created_at)}</span>
      </div>
    </Link>
  );
}
