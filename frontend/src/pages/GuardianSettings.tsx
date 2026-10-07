// frontend/src/pages/GuardianSettings.tsx
import React, { useState, useEffect } from 'react';
import toast from 'react-hot-toast';
import { getGuardians, addGuardian, verifyGuardian, deleteGuardian } from '../api/guardian';
import { Guardian, AddGuardianRequest } from '../types/guardian';
import { OTPChannel } from '../types/auth';
import PhoneInput from '../components/PhoneInput';
import ChannelToggle from '../components/ChannelToggle';
import OtpInput from '../components/OtpInput';
import LoadingSpinner from '../components/LoadingSpinner';

export const GuardianSettings: React.FC = () => {
  const [guardians, setGuardians] = useState<Guardian[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [submitting, setSubmitting] = useState<boolean>(false);

  // Modal / Verification States
  const [isAddModalOpen, setIsAddModalOpen] = useState<boolean>(false);
  const [isVerifyModalOpen, setIsVerifyModalOpen] = useState<boolean>(false);
  const [activeGuardianId, setActiveGuardianId] = useState<number | null>(null);
  const [activeChallengeId, setActiveChallengeId] = useState<number | null>(null);
  const [verifyOtpCode, setVerifyOtpCode] = useState<string>('');
  const [verifyError, setVerifyError] = useState<string>('');

  // Form State
  const [formData, setFormData] = useState<AddGuardianRequest>({
    name: '',
    phone: '',
    relationship: 'Parent',
    preferred_channel: 'sms',
    consent_given: false,
  });

  const fetchGuardians = async () => {
    setLoading(true);
    try {
      const res = await getGuardians();
      if (res.data.success) {
        setGuardians(res.data.guardians || []);
      }
    } catch (err) {
      console.error('Failed to load guardians:', err);
      toast.error('Failed to fetch guardian records.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchGuardians();
  }, []);

  // Handle Add Guardian Submit
  const handleAddSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.name.trim() || !formData.phone.trim()) {
      toast.error('Please provide guardian name and mobile number.');
      return;
    }
    if (!formData.consent_given) {
      toast.error('You must confirm guardian consent before registering emergency alerts.');
      return;
    }

    setSubmitting(true);
    try {
      const res = await addGuardian(formData);
      if (res.data.success) {
        toast.success(res.data.message);
        setIsAddModalOpen(false);
        // Open OTP verification modal
        setActiveGuardianId(res.data.guardian.id);
        setActiveChallengeId(res.data.challenge_id);
        setVerifyOtpCode('');
        setVerifyError('');
        setIsVerifyModalOpen(true);
        fetchGuardians();
      }
    } catch (err: any) {
      const msg = err.response?.data?.error || 'Failed to add guardian.';
      toast.error(msg);
    } finally {
      setSubmitting(false);
    }
  };

  // Handle Verify Guardian OTP
  const handleVerifySubmit = async () => {
    if (!activeGuardianId || !activeChallengeId || verifyOtpCode.length !== 6) {
      setVerifyError('Please enter the 6-digit verification code.');
      return;
    }

    setSubmitting(true);
    setVerifyError('');
    try {
      const res = await verifyGuardian({
        guardian_id: activeGuardianId,
        challenge_id: activeChallengeId,
        otp: verifyOtpCode,
      });
      if (res.data.success) {
        toast.success(res.data.message);
        setIsVerifyModalOpen(false);
        fetchGuardians();
      }
    } catch (err: any) {
      const msg = err.response?.data?.error || 'Verification failed.';
      setVerifyError(msg);
      toast.error(msg);
    } finally {
      setSubmitting(false);
    }
  };

  // Handle Delete Guardian
  const handleDelete = async (guardianId: number, name: string) => {
    if (!window.confirm(`Are you sure you want to remove '${name}' as your emergency guardian?`)) {
      return;
    }
    try {
      await deleteGuardian(guardianId);
      toast.success(`Removed guardian '${name}'.`);
      setGuardians((prev) => prev.filter((g) => g.id !== guardianId));
    } catch (err) {
      toast.error('Failed to remove guardian.');
    }
  };

  return (
    <div className="page-wrapper container py-8 max-w-5xl mx-auto px-4">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8 pb-6 border-b border-slate-800">
        <div>
          <div className="text-xs font-bold uppercase tracking-widest text-cyan-400 mb-1">
            CRITICAL INCIDENT ASSISTANCE
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">
            Emergency Guardian Notifications
          </h1>
          <p className="text-sm text-slate-400 mt-1 max-w-2xl">
            Designate trusted contacts to receive real-time SMS or WhatsApp alerts whenever you report a cybercrime or if a high-risk financial fraud case requires immediate intervention.
          </p>
        </div>
        <button
          onClick={() => {
            setFormData({ name: '', phone: '', relationship: 'Parent', preferred_channel: 'sms', consent_given: false });
            setIsAddModalOpen(true);
          }}
          className="inline-flex items-center justify-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-slate-950 font-bold text-sm shadow-lg shadow-cyan-500/20 transition-all self-start sm:self-auto"
        >
          <span>+</span>
          <span>Add Guardian</span>
        </button>
      </div>

      {/* Security & Privacy Notice Banner */}
      <div className="mb-8 p-4 bg-slate-900/60 border border-slate-800 rounded-2xl flex items-start gap-3.5 shadow-sm">
        <span className="text-2xl">🛡️</span>
        <div className="text-xs sm:text-sm text-slate-300 space-y-1">
          <p className="font-semibold text-slate-100">ZeroGuard Privacy Guarantee for Guardians</p>
          <p className="text-slate-400">
            Guardian notifications contain <strong>only sanitized case reference IDs and status updates</strong>. ZeroGuard strictly never exposes victim narratives, monetary figures, or attached evidence files over SMS or WhatsApp.
          </p>
        </div>
      </div>

      {/* Guardians List */}
      {loading ? (
        <div className="py-16 text-center">
          <LoadingSpinner label="Loading trusted guardians…" />
        </div>
      ) : guardians.length === 0 ? (
        <div className="text-center py-16 px-4 bg-slate-900/40 rounded-3xl border border-slate-800/80">
          <div className="text-4xl mb-3">🤝</div>
          <h3 className="text-lg font-bold text-slate-200">No Guardians Enrolled</h3>
          <p className="text-xs sm:text-sm text-slate-400 max-w-md mx-auto mt-1 mb-6">
            You haven't added any trusted guardians yet. Add a family member or mentor so they receive emergency alerts during critical Golden Hour fraud incidents.
          </p>
          <button
            onClick={() => setIsAddModalOpen(true)}
            className="px-5 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-cyan-400 font-semibold text-xs sm:text-sm border border-slate-700 transition-colors"
          >
            + Add Your First Guardian
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {guardians.map((g) => (
            <div
              key={g.id}
              className="bg-slate-900/80 border border-slate-800 rounded-2xl p-5 shadow-lg relative flex flex-col justify-between"
            >
              <div>
                <div className="flex items-start justify-between gap-3 mb-2">
                  <div>
                    <h3 className="font-bold text-slate-100 text-base flex items-center gap-2">
                      {g.name}
                      <span className="text-xs font-normal px-2 py-0.5 rounded-md bg-slate-800 text-slate-300 border border-slate-700">
                        {g.relationship}
                      </span>
                    </h3>
                    <div className="text-xs text-slate-400 font-mono mt-0.5 tracking-wider">
                      {g.masked_phone}
                    </div>
                  </div>

                  {/* Verification Status Badge */}
                  {g.opted_out ? (
                    <span className="text-[11px] font-bold px-2.5 py-1 rounded-full bg-red-950/80 text-red-400 border border-red-800">
                      Opted Out
                    </span>
                  ) : g.verified ? (
                    <span className="text-[11px] font-bold px-2.5 py-1 rounded-full bg-emerald-950/80 text-emerald-400 border border-emerald-800 flex items-center gap-1">
                      <span>✓</span> Verified Active
                    </span>
                  ) : (
                    <span className="text-[11px] font-bold px-2.5 py-1 rounded-full bg-amber-950/80 text-amber-400 border border-amber-800">
                      Pending Verification
                    </span>
                  )}
                </div>

                <div className="flex items-center gap-2 text-xs text-slate-400 mt-3 pt-3 border-t border-slate-800/80">
                  <span>Channel:</span>
                  <span className="font-semibold text-slate-200 uppercase flex items-center gap-1">
                    {g.preferred_channel === 'whatsapp' ? '💬 WhatsApp' : '📱 SMS'}
                  </span>
                  {g.consent_given && (
                    <span className="ml-auto text-[11px] text-emerald-400">Consent Logged ✓</span>
                  )}
                </div>
              </div>

              {/* Actions */}
              <div className="mt-4 pt-3 flex items-center justify-between border-t border-slate-800/60">
                {!g.verified && !g.opted_out && (
                  <button
                    onClick={() => {
                      setActiveGuardianId(g.id);
                      setVerifyOtpCode('');
                      setIsVerifyModalOpen(true);
                    }}
                    className="text-xs font-bold text-amber-400 hover:text-amber-300 underline"
                  >
                    Enter Verification OTP →
                  </button>
                )}
                <button
                  onClick={() => handleDelete(g.id, g.name)}
                  className="text-xs text-red-400 hover:text-red-300 hover:underline ml-auto"
                >
                  Remove
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* MODAL 1: ADD GUARDIAN */}
      {isAddModalOpen && (
        <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="w-full max-w-lg bg-slate-900 border border-slate-800 rounded-3xl p-6 sm:p-8 shadow-2xl animate-fade-up">
            <div className="flex items-center justify-between mb-5">
              <h2 className="text-xl font-bold text-white">Add Emergency Guardian</h2>
              <button
                onClick={() => setIsAddModalOpen(false)}
                className="text-slate-400 hover:text-slate-200 text-lg"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleAddSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1.5">
                  Guardian Full Name
                </label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="e.g. Ramesh Sharma"
                  required
                  className="w-full bg-slate-950 border border-slate-700 rounded-xl px-4 py-2.5 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-cyan-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1.5">
                  Relationship
                </label>
                <select
                  value={formData.relationship}
                  onChange={(e) => setFormData({ ...formData, relationship: e.target.value })}
                  className="w-full bg-slate-950 border border-slate-700 rounded-xl px-4 py-2.5 text-sm text-slate-100 focus:outline-none focus:border-cyan-500 cursor-pointer"
                >
                  <option value="Parent">Parent</option>
                  <option value="Guardian">Guardian</option>
                  <option value="Spouse">Spouse</option>
                  <option value="Sibling">Sibling</option>
                  <option value="Close Friend">Close Friend</option>
                  <option value="Other Family Member">Other Family Member</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1.5">
                  Guardian Mobile Number
                </label>
                <PhoneInput
                  value={formData.phone}
                  onChange={(full) => setFormData({ ...formData, phone: full })}
                  required
                />
              </div>

              <ChannelToggle
                selectedChannel={formData.preferred_channel || 'sms'}
                onChange={(ch: OTPChannel) => setFormData({ ...formData, preferred_channel: ch })}
              />

              {/* Consent Checkbox */}
              <div className="pt-2">
                <label className="flex items-start gap-3 cursor-pointer select-none">
                  <input
                    type="checkbox"
                    checked={formData.consent_given}
                    onChange={(e) => setFormData({ ...formData, consent_given: e.target.checked })}
                    className="mt-1 w-4 h-4 rounded border-slate-700 bg-slate-950 text-cyan-500 focus:ring-cyan-500/20"
                  />
                  <span className="text-xs text-slate-300 leading-relaxed">
                    I confirm that I have informed this guardian and obtained their consent to receive high-risk incident alerts and case updates.
                  </span>
                </label>
              </div>

              <div className="flex items-center gap-3 pt-4">
                <button
                  type="button"
                  onClick={() => setIsAddModalOpen(false)}
                  className="flex-1 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 font-semibold text-sm transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting || !formData.consent_given}
                  className="flex-1 py-2.5 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-slate-950 font-bold text-sm shadow-lg shadow-cyan-500/20 transition-all disabled:opacity-50"
                >
                  {submitting ? 'Sending OTP…' : 'Save & Send OTP'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL 2: VERIFY GUARDIAN OTP */}
      {isVerifyModalOpen && (
        <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="w-full max-w-md bg-slate-900 border border-slate-800 rounded-3xl p-6 sm:p-8 shadow-2xl animate-fade-up">
            <div className="text-center mb-6">
              <div className="text-3xl mb-2">📲</div>
              <h2 className="text-xl font-bold text-white">Verify Guardian Number</h2>
              <p className="text-xs sm:text-sm text-slate-400 mt-1">
                Enter the 6-digit verification code sent to the guardian's mobile number.
              </p>
            </div>

            {verifyError && (
              <div className="mb-4 p-3 bg-red-950/50 border border-red-800 rounded-xl text-red-200 text-xs">
                ⚠️ {verifyError}
              </div>
            )}

            <div className="mb-6">
              <OtpInput
                length={6}
                value={verifyOtpCode}
                onChange={setVerifyOtpCode}
                onComplete={() => handleVerifySubmit()}
                autoFocus
              />
            </div>

            <div className="flex items-center gap-3">
              <button
                type="button"
                onClick={() => setIsVerifyModalOpen(false)}
                className="flex-1 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 font-semibold text-sm transition-colors"
              >
                Later
              </button>
              <button
                type="button"
                onClick={handleVerifySubmit}
                disabled={submitting || verifyOtpCode.length !== 6}
                className="flex-1 py-2.5 rounded-xl bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-400 hover:to-teal-500 text-slate-950 font-bold text-sm shadow-lg shadow-emerald-500/20 transition-all disabled:opacity-50"
              >
                {submitting ? 'Verifying…' : 'Verify Guardian'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default GuardianSettings;
