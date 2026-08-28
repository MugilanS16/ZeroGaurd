// src/pages/UserDashboard.jsx
import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { getMyReports } from '../api/reports';
import ReportCard from '../components/ReportCard';
import LoadingSpinner from '../components/LoadingSpinner';
import toast from 'react-hot-toast';
import './UserDashboard.css';

export default function UserDashboard() {
  const { user } = useAuth();
  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('ALL');

  const fetchReports = async () => {
    setLoading(true);
    try {
      const res = await getMyReports();
      setReports(res.data.reports || []);
    } catch (err) {
      console.error('Failed to load user reports:', err);
      toast.error('Could not load your reports. Please check your connection.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReports();
  }, []);

  // Filtered reports
  const filteredReports = reports.filter((r) => {
    const matchesStatus =
      statusFilter === 'ALL' ||
      r.status?.toLowerCase() === statusFilter.toLowerCase();

    const matchesSearch =
      !searchTerm ||
      r.reference_number?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      r.crime_type?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      r.description?.toLowerCase().includes(searchTerm.toLowerCase());

    return matchesStatus && matchesSearch;
  });

  // Summary Metrics
  const totalCount = reports.length;
  const pendingCount = reports.filter((r) => r.status === 'Pending').length;
  const inReviewCount = reports.filter((r) => r.status === 'In Review').length;
  const resolvedCount = reports.filter((r) => r.status === 'Resolved').length;

  return (
    <div className="dashboard-page page-wrapper container">
      {/* Top Banner / Welcome */}
      <div className="dashboard-header">
        <div>
          <div className="section-eyebrow">CITIZEN PORTAL</div>
          <h1 className="page-title">My Cybercrime Reports</h1>
          <p className="page-subtitle">
            Track investigation status, download legal PDFs, and manage your filed complaints.
          </p>
        </div>
        <div className="dashboard-header-actions">
          <button onClick={fetchReports} className="btn btn-secondary" title="Refresh reports">
            🔄 Refresh
          </button>
          <Link to="/report" className="btn btn-primary btn-lg" id="dashboard-new-report-btn">
            + File New Report
          </Link>
        </div>
      </div>

      {/* Metrics Row */}
      <div className="metrics-grid">
        <div className="metric-card card">
          <div className="metric-icon" style={{ background: 'rgba(99,102,241,0.15)', color: '#818cf8' }}>
            📋
          </div>
          <div className="metric-info">
            <span className="metric-value">{totalCount}</span>
            <span className="metric-label">Total Filed</span>
          </div>
        </div>

        <div className="metric-card card">
          <div className="metric-icon" style={{ background: 'rgba(234,179,8,0.15)', color: '#facc15' }}>
            ⏳
          </div>
          <div className="metric-info">
            <span className="metric-value">{pendingCount}</span>
            <span className="metric-label">Pending</span>
          </div>
        </div>

        <div className="metric-card card">
          <div className="metric-icon" style={{ background: 'rgba(6,182,212,0.15)', color: '#22d3ee' }}>
            🔍
          </div>
          <div className="metric-info">
            <span className="metric-value">{inReviewCount}</span>
            <span className="metric-label">Under Investigation</span>
          </div>
        </div>

        <div className="metric-card card">
          <div className="metric-icon" style={{ background: 'rgba(34,197,94,0.15)', color: '#4ade80' }}>
            ✅
          </div>
          <div className="metric-info">
            <span className="metric-value">{resolvedCount}</span>
            <span className="metric-label">Resolved</span>
          </div>
        </div>
      </div>

      {/* Filter and Search Controls */}
      <div className="dashboard-filter-bar card">
        <div className="search-input-wrapper">
          <span className="search-icon">🔍</span>
          <input
            type="text"
            className="form-input search-input"
            placeholder="Search by Ref #, crime category, or description…"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
          {searchTerm && (
            <button className="clear-search-btn" onClick={() => setSearchTerm('')}>
              ✕
            </button>
          )}
        </div>

        <div className="status-filter-pills">
          {['ALL', 'Pending', 'In Review', 'Resolved'].map((st) => (
            <button
              key={st}
              className={`filter-pill ${statusFilter === st ? 'active' : ''}`}
              onClick={() => setStatusFilter(st)}
            >
              {st}
            </button>
          ))}
        </div>
      </div>

      {/* Reports Grid or Empty State */}
      {loading ? (
        <LoadingSpinner fullPage label="Loading your complaints…" />
      ) : filteredReports.length === 0 ? (
        <div className="empty-state card">
          <div className="empty-icon">📂</div>
          <h3>No reports found</h3>
          <p>
            {searchTerm || statusFilter !== 'ALL'
              ? 'No complaints match your selected search or filter criteria.'
              : "You haven't filed any cybercrime complaints yet."}
          </p>
          <Link to="/report" className="btn btn-primary" style={{ marginTop: '1.25rem', display: 'inline-flex' }}>
            + File a Report Now
          </Link>
        </div>
      ) : (
        <div className="reports-grid animate-fade-in">
          {filteredReports.map((report) => (
            <ReportCard key={report.id} report={report} />
          ))}
        </div>
      )}
    </div>
  );
}
