// src/pages/AdminDashboard.jsx
import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { getAllReports, updateReportStatus, getAdminStats } from '../api/reports';
import SeverityBadge from '../components/SeverityBadge';
import LoadingSpinner from '../components/LoadingSpinner';
import toast from 'react-hot-toast';
import {
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
} from 'recharts';
import './AdminDashboard.css';

const SEVERITY_COLORS = {
  low: '#22c55e',
  medium: '#eab308',
  high: '#f97316',
  critical: '#ef4444',
};

const CRIME_TYPE_OPTIONS = [
  'ALL',
  'UPI Fraud',
  'Banking Fraud',
  'Credit/Debit Card Fraud',
  'Phishing',
  'Identity Theft',
  'Social Media Hacking',
  'Email Hacking',
  'Online Shopping Fraud',
  'Job Scam',
  'Investment Scam',
  'Lottery/Prize Scam',
  'Cyber Bullying',
  'Sextortion',
  'Malware/Ransomware',
  'Fake Customer Care Scam',
];

export default function AdminDashboard() {
  const [reports, setReports] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [updatingId, setUpdatingId] = useState(null);

  // Filters
  const [crimeTypeFilter, setCrimeTypeFilter] = useState('ALL');
  const [severityFilter, setSeverityFilter] = useState('ALL');
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [searchTerm, setSearchTerm] = useState('');

  const loadData = async () => {
    setLoading(true);
    try {
      const [reportsRes, statsRes] = await Promise.all([
        getAllReports(),
        getAdminStats(),
      ]);
      setReports(reportsRes.data.reports || []);
      setStats(statsRes.data || null);
    } catch (err) {
      console.error('Admin data load failed:', err);
      toast.error('Failed to load admin telemetry and reports.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  // Handle inline status update
  const handleStatusChange = async (reportId, newStatus) => {
    setUpdatingId(reportId);
    try {
      const res = await updateReportStatus(reportId, newStatus);
      const updated = res.data.report;

      setReports((prev) =>
        prev.map((r) => (r.id === reportId ? { ...r, status: updated.status } : r))
      );
      toast.success(`Report #${updated.reference_number} updated to ${newStatus}`);

      // Refresh summary stats quietly
      getAdminStats().then((sRes) => setStats(sRes.data));
    } catch (err) {
      console.error('Status update failed:', err);
      toast.error('Could not update status. Please try again.');
    } finally {
      setUpdatingId(null);
    }
  };

  // Filtered reports list
  const filteredReports = reports.filter((r) => {
    const matchesCrime =
      crimeTypeFilter === 'ALL' || r.crime_type === crimeTypeFilter;
    const matchesSev =
      severityFilter === 'ALL' ||
      r.severity?.toLowerCase() === severityFilter.toLowerCase();
    const matchesStatus =
      statusFilter === 'ALL' ||
      r.status?.toLowerCase() === statusFilter.toLowerCase();

    const matchesSearch =
      !searchTerm ||
      r.reference_number?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      r.user_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      r.user_email?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      r.crime_type?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      r.description?.toLowerCase().includes(searchTerm.toLowerCase());

    return matchesCrime && matchesSev && matchesStatus && matchesSearch;
  });

  // Prepare chart data
  const severityChartData = stats?.by_severity
    ? Object.entries(stats.by_severity).map(([name, value]) => ({
        name: name.toUpperCase(),
        value,
        color: SEVERITY_COLORS[name] || '#8b5cf6',
      }))
    : [];

  const crimeTypeChartData = stats?.by_type || [];

  return (
    <div className="admin-page page-wrapper container">
      {/* Header */}
      <div className="admin-header">
        <div>
          <div className="section-eyebrow">COMMAND & CONTROL</div>
          <h1 className="page-title">National Cyber Incident Dashboard</h1>
          <p className="page-subtitle">
            Administer filed complaints, monitor threat trends, and assign investigation workflows.
          </p>
        </div>
        <button onClick={loadData} className="btn btn-secondary" title="Reload admin data">
          🔄 Refresh
        </button>
      </div>

      {loading ? (
        <LoadingSpinner fullPage label="Loading admin telemetry…" />
      ) : (
        <>
          {/* Top Metric Cards */}
          <div className="metrics-grid">
            <div className="metric-card card">
              <div className="metric-icon" style={{ background: 'rgba(99,102,241,0.15)', color: '#818cf8' }}>
                📁
              </div>
              <div className="metric-info">
                <span className="metric-value">{stats?.total || 0}</span>
                <span className="metric-label">Total Incidents</span>
              </div>
            </div>

            <div className="metric-card card">
              <div className="metric-icon" style={{ background: 'rgba(234,179,8,0.15)', color: '#facc15' }}>
                ⏳
              </div>
              <div className="metric-info">
                <span className="metric-value">{stats?.pending || 0}</span>
                <span className="metric-label">Pending Action</span>
              </div>
            </div>

            <div className="metric-card card">
              <div className="metric-icon" style={{ background: 'rgba(6,182,212,0.15)', color: '#22d3ee' }}>
                🔍
              </div>
              <div className="metric-info">
                <span className="metric-value">{stats?.in_review || 0}</span>
                <span className="metric-label">Active Review</span>
              </div>
            </div>

            <div className="metric-card card">
              <div className="metric-icon" style={{ background: 'rgba(34,197,94,0.15)', color: '#4ade80' }}>
                🛡️
              </div>
              <div className="metric-info">
                <span className="metric-value">{stats?.resolved || 0}</span>
                <span className="metric-label">Resolved</span>
              </div>
            </div>
          </div>

          {/* Analytics Charts Row */}
          <div className="charts-row grid-2">
            {/* Chart 1: Severity Distribution */}
            <div className="chart-card card">
              <h3 className="chart-title">🚨 Threat Severity Distribution</h3>
              <p className="chart-subtitle">Breakdown of reported crimes by AI risk score</p>
              <div className="chart-container">
                <ResponsiveContainer width="100%" height={240}>
                  <PieChart>
                    <Pie
                      data={severityChartData}
                      dataKey="value"
                      nameKey="name"
                      cx="50%"
                      cy="50%"
                      innerRadius={60}
                      outerRadius={85}
                      paddingAngle={4}
                    >
                      {severityChartData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip
                      contentStyle={{
                        background: 'var(--bg-card)',
                        border: '1px solid var(--border)',
                        borderRadius: '8px',
                        color: 'var(--text-primary)',
                      }}
                    />
                    <Legend verticalAlign="bottom" height={36} />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Chart 2: Crime Categories */}
            <div className="chart-card card">
              <h3 className="chart-title">📊 Top Incident Categories</h3>
              <p className="chart-subtitle">Volume of complaints by threat type</p>
              <div className="chart-container">
                <ResponsiveContainer width="100%" height={240}>
                  <BarChart data={crimeTypeChartData} margin={{ top: 10, right: 10, left: -20, bottom: 25 }}>
                    <XAxis
                      dataKey="name"
                      stroke="var(--text-muted)"
                      tick={{ fill: 'var(--text-muted)', fontSize: 11 }}
                      interval={0}
                      angle={-25}
                      textAnchor="end"
                    />
                    <YAxis
                      stroke="var(--text-muted)"
                      tick={{ fill: 'var(--text-muted)', fontSize: 11 }}
                      allowDecimals={false}
                    />
                    <Tooltip
                      contentStyle={{
                        background: 'var(--bg-card)',
                        border: '1px solid var(--border)',
                        borderRadius: '8px',
                        color: 'var(--text-primary)',
                      }}
                    />
                    <Bar dataKey="count" fill="url(#barGradient)" radius={[4, 4, 0, 0]} />
                    <defs>
                      <linearGradient id="barGradient" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor="#6366f1" />
                        <stop offset="100%" stopColor="#06b6d4" />
                      </linearGradient>
                    </defs>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>

          {/* Table Filters */}
          <div className="table-filter-bar card">
            <div className="search-input-wrapper">
              <span className="search-icon">🔍</span>
              <input
                type="text"
                className="form-input search-input"
                placeholder="Search reference #, citizen name, email, or details…"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>

            <div className="filter-dropdowns">
              <select
                className="form-select admin-select"
                value={crimeTypeFilter}
                onChange={(e) => setCrimeTypeFilter(e.target.value)}
              >
                {CRIME_TYPE_OPTIONS.map((ct) => (
                  <option key={ct} value={ct}>
                    {ct === 'ALL' ? 'All Crime Categories' : ct}
                  </option>
                ))}
              </select>

              <select
                className="form-select admin-select"
                value={severityFilter}
                onChange={(e) => setSeverityFilter(e.target.value)}
              >
                <option value="ALL">All Severities</option>
                <option value="low">Low</option>
                <option value="medium">Medium</option>
                <option value="high">High</option>
                <option value="critical">Critical</option>
              </select>

              <select
                className="form-select admin-select"
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
              >
                <option value="ALL">All Statuses</option>
                <option value="Pending">Pending</option>
                <option value="In Review">In Review</option>
                <option value="Resolved">Resolved</option>
              </select>
            </div>
          </div>

          {/* Reports Table */}
          <div className="table-wrapper card">
            <table>
              <thead>
                <tr>
                  <th>Ref Number</th>
                  <th>Citizen / Complainant</th>
                  <th>Crime Category</th>
                  <th>Severity</th>
                  <th>Status Workflow</th>
                  <th>Date Filed</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredReports.length === 0 ? (
                  <tr>
                    <td colSpan="7" style={{ textAlign: 'center', padding: '3rem 1rem' }}>
                      <span style={{ fontSize: '1.5rem', display: 'block', marginBottom: '0.5rem' }}>🔍</span>
                      No complaints match the filter parameters.
                    </td>
                  </tr>
                ) : (
                  filteredReports.map((r) => (
                    <tr key={r.id}>
                      <td>
                        <Link to={`/reports/${r.id}`} className="ref-link">
                          {r.reference_number}
                        </Link>
                      </td>
                      <td>
                        <div className="user-cell">
                          <strong>{r.user_name || 'Citizen'}</strong>
                          <span className="user-email">{r.user_email || '—'}</span>
                        </div>
                      </td>
                      <td>
                        <span className="crime-pill">{r.crime_type || 'Unknown'}</span>
                      </td>
                      <td>
                        <SeverityBadge severity={r.severity || 'medium'} size="sm" />
                      </td>
                      <td>
                        <select
                          className={`status-select status-${r.status?.toLowerCase().replace(' ', '-')}`}
                          value={r.status}
                          disabled={updatingId === r.id}
                          onChange={(e) => handleStatusChange(r.id, e.target.value)}
                        >
                          <option value="Pending">⏳ Pending</option>
                          <option value="In Review">🔍 In Review</option>
                          <option value="Resolved">✅ Resolved</option>
                        </select>
                      </td>
                      <td className="date-cell">
                        {r.created_at
                          ? new Date(r.created_at).toLocaleDateString('en-IN', {
                              day: '2-digit',
                              month: 'short',
                              year: 'numeric',
                            })
                          : '—'}
                      </td>
                      <td>
                        <Link to={`/reports/${r.id}`} className="btn btn-secondary btn-sm">
                          Inspect →
                        </Link>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
}
