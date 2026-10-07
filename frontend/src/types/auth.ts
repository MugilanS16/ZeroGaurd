// frontend/src/types/auth.ts
// Strict TypeScript definitions for ZeroGuard AI Authentication and OTP

export type OTPChannel = 'sms' | 'whatsapp';

export interface User {
  id: number;
  fullname: string;
  name?: string;
  email: string;
  phone?: string | null;
  phone_number?: string | null;
  phone_verified?: boolean;
  preferred_otp_channel?: OTPChannel;
  role: 'citizen' | 'admin';
  is_verified?: boolean;
  created_at?: string | null;
  last_login?: string | null;
}

export interface OTPChallenge {
  id: number;
  phone_number: string;
  channel: OTPChannel;
  purpose: string;
  expires_at?: string;
  is_expired?: boolean;
  is_consumed?: boolean;
  attempts?: number;
  created_at?: string;
}

export interface SendOTPRequest {
  phone: string;
  channel?: OTPChannel;
  purpose?: string;
}

export interface SendOTPResponse {
  success: boolean;
  challenge_id: number;
  channel: OTPChannel;
  expires_in: number;
  cooldown_seconds: number;
  message: string;
  error?: string;
}

export interface VerifyOTPRequest {
  challenge_id: number;
  otp: string;
}

export interface VerifyOTPResponse {
  success: boolean;
  message: string;
  access_token?: string;
  user?: User;
  purpose?: string;
  error?: string;
}

export interface ResendOTPRequest {
  challenge_id: number;
}

export interface ResendOTPResponse {
  success: boolean;
  challenge_id: number;
  channel: OTPChannel;
  expires_in: number;
  cooldown_seconds: number;
  message: string;
  error?: string;
}

export interface LoginResponse {
  requires_2fa?: boolean;
  challenge_id?: number;
  channel?: OTPChannel;
  masked_phone?: string;
  access_token?: string;
  user?: User;
  message?: string;
}
