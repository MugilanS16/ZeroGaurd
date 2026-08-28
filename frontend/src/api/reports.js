// src/api/reports.js
// Report submission & retrieval API calls
import api from './axiosInstance';

export const submitReport = (payload) =>
  api.post('/api/reports', payload);

export const getMyReports = () =>
  api.get('/api/reports/mine');

export const getReportById = (id) =>
  api.get(`/api/reports/${id}`);

export const getAllReports = (params = {}) =>
  api.get('/api/admin/reports', { params });

export const updateReportStatus = (id, status) =>
  api.patch(`/api/admin/reports/${id}`, { status });

export const getAdminStats = () =>
  api.get('/api/admin/stats');
