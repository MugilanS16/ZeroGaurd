// frontend/src/types/guardian.ts
// Strict TypeScript definitions for Guardian management and verification

import { OTPChannel } from './auth';

export interface Guardian {
  id: number;
  user_id: number;
  name: string;
  relationship: string;
  phone_number: string;
  masked_phone: string;
  preferred_channel: OTPChannel;
  consent_given: boolean;
  consent_at?: string | null;
  verified: boolean;
  opted_out: boolean;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface AddGuardianRequest {
  name: string;
  phone: string;
  relationship?: string;
  preferred_channel?: OTPChannel;
  consent_given: boolean;
}

export interface AddGuardianResponse {
  success: boolean;
  guardian: Guardian;
  challenge_id: number;
  channel: OTPChannel;
  message: string;
  error?: string;
}

export interface VerifyGuardianRequest {
  guardian_id: number;
  challenge_id: number;
  otp: string;
}

export interface VerifyGuardianResponse {
  success: boolean;
  guardian: Guardian;
  message: string;
  error?: string;
}

export interface GuardiansListResponse {
  success: boolean;
  guardians: Guardian[];
}
