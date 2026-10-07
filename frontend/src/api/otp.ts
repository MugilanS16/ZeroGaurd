// frontend/src/api/otp.ts
// Typed Axios API client for 2FA SMS & WhatsApp OTP
import api from './axiosInstance';
import {
  SendOTPRequest,
  SendOTPResponse,
  VerifyOTPRequest,
  VerifyOTPResponse,
  ResendOTPRequest,
  ResendOTPResponse
} from '../types/auth';

export const sendOtp = (data: SendOTPRequest) =>
  api.post<SendOTPResponse>('/api/auth/otp/send', data);

export const verifyOtp = (data: VerifyOTPRequest) =>
  api.post<VerifyOTPResponse>('/api/auth/otp/verify', data);

export const resendOtp = (data: ResendOTPRequest) =>
  api.post<ResendOTPResponse>('/api/auth/otp/resend', data);
