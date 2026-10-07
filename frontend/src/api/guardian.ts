// frontend/src/api/guardian.ts
// Typed Axios API client for Guardian Management & Verification
import api from './axiosInstance';
import {
  GuardiansListResponse,
  AddGuardianRequest,
  AddGuardianResponse,
  VerifyGuardianRequest,
  VerifyGuardianResponse
} from '../types/guardian';

export const getGuardians = () =>
  api.get<GuardiansListResponse>('/api/guardian');

export const addGuardian = (data: AddGuardianRequest) =>
  api.post<AddGuardianResponse>('/api/guardian', data);

export const verifyGuardian = (data: VerifyGuardianRequest) =>
  api.post<VerifyGuardianResponse>('/api/guardian/verify', data);

export const deleteGuardian = (guardianId: number) =>
  api.delete<{ success: boolean; message: string }>(`/api/guardian/${guardianId}`);
