// src/pages/Register.jsx
import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import toast from 'react-hot-toast';
import LoadingSpinner from '../components/LoadingSpinner';
import './Auth.css';

export default function Register() {
  const { register, isAuthenticated } = useAuth();
  const navigate = useNavigate();

  const [form, setForm] = useState({ fullname: '', email: '', phone: '', password: '', confirm: '' });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  if (isAuthenticated) {
    navigate('/dashboard', { replace: true });
    return null;
  }

  const handleChange = (e) => {
    setForm((p) => ({ ...p, [e.target.name]: e.target.value }));
    setError('');
  };

  const validate = () => {
    if (!form.fullname || !form.email || !form.password) return 'Name, email, and password are required.';
    if (form.password.length < 8)                         return 'Password must be at least 8 characters.';
    if (form.password !== form.confirm)                   return 'Passwords do not match.';
    return null;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const err = validate();
    if (err) { setError(err); return; }

    setLoading(true);
    try {
      await register(form.fullname, form.email, form.phone, form.password);
      toast.success('Account created! Welcome 🎉');
      navigate('/dashboard', { replace: true });
    } catch (err) {
      const msg = err.response?.data?.message || 'Registration failed. Try again.';
      setError(msg);
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-page page-wrapper">
      <div className="auth-container">
        <div className="auth-card card animate-fade-up">
          <div className="auth-header">
            <div className="auth-icon">🛡️</div>
            <h2>Create Account</h2>
            <p>Join CrimeShield AI — protecting you online.</p>
          </div>

          {error && (
            <div className="auth-error" role="alert">⚠️ {error}</div>
          )}

          <form onSubmit={handleSubmit} className="auth-form" noValidate>
            <div className="form-group">
              <label htmlFor="reg-name" className="form-label">Full Name</label>
              <input id="reg-name" name="fullname" type="text" className="form-input"
                placeholder="Ravi Kumar" value={form.fullname} onChange={handleChange}
                required autoComplete="name" autoFocus />
            </div>

            <div className="form-group">
              <label htmlFor="reg-email" className="form-label">Email Address</label>
              <input id="reg-email" name="email" type="email" className="form-input"
                placeholder="you@example.com" value={form.email} onChange={handleChange}
                required autoComplete="email" />
            </div>

            <div className="form-group">
              <label htmlFor="reg-phone" className="form-label">Phone Number <span style={{color:'var(--text-muted)'}}>— optional</span></label>
              <input id="reg-phone" name="phone" type="tel" className="form-input"
                placeholder="+91 98765 43210" value={form.phone} onChange={handleChange}
                autoComplete="tel" />
            </div>

            <div className="form-group">
              <label htmlFor="reg-password" className="form-label">Password</label>
              <input id="reg-password" name="password" type="password" className="form-input"
                placeholder="Min. 8 characters" value={form.password} onChange={handleChange}
                required autoComplete="new-password" />
            </div>

            <div className="form-group">
              <label htmlFor="reg-confirm" className="form-label">Confirm Password</label>
              <input id="reg-confirm" name="confirm" type="password" className="form-input"
                placeholder="Re-enter your password" value={form.confirm} onChange={handleChange}
                required autoComplete="new-password" />
            </div>

            <button
              id="register-submit-btn"
              type="submit"
              className="btn btn-primary btn-lg"
              disabled={loading}
              style={{ width: '100%', justifyContent: 'center' }}
            >
              {loading ? <LoadingSpinner size="sm" /> : null}
              {loading ? 'Creating account…' : 'Create Account'}
            </button>
          </form>

          <p className="auth-footer-text">
            Already have an account? <Link to="/login">Sign in</Link>
          </p>
        </div>
      </div>
    </div>
  );
}
