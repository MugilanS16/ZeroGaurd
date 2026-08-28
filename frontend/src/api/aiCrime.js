// src/api/aiCrime.js
// AI Crime analysis & chat API calls
import api from './axiosInstance';

export const analyzeText = (text) =>
  api.post('/api/ai-crime/analyze', { text });

export const sendChatMessage = (message, history = []) =>
  api.post('/api/ai-crime/chat', { message, history });

export const enhanceReport = (text) =>
  api.post('/api/ai-enhance-report', { text });
