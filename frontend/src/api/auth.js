// src/api/auth.js
// Authentication API calls
import api from './axiosInstance';

export const loginUser = (email, password) =>
  api.post('/api/auth/login', { email, password });

export const registerUser = (fullname, email, phone, password) =>
  api.post('/api/auth/register', { fullname, email, phone, password });

export const logoutUser = () =>
  api.post('/api/auth/logout');

export const getMe = () =>
  api.get('/api/auth/me');
