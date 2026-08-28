// src/components/Navbar.jsx
import React, { useState } from 'react';
import { Link, NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import toast from 'react-hot-toast';
import './Navbar.css';

export default function Navbar() {
  const { isAuthenticated, user, logout, isAdmin } = useAuth();
  const navigate = useNavigate();
  const [menuOpen, setMenuOpen] = useState(false);

  const handleLogout = async () => {
    await logout();
    toast.success('Logged out successfully');
    navigate('/login');
    setMenuOpen(false);
  };

  const closeMenu = () => setMenuOpen(false);

  const initials = user?.name
    ? user.name.split(' ').map((n) => n[0]).join('').toUpperCase().slice(0, 2)
    : '?';

  return (
    <>
      {/* Emergency Banner */}
      <div className="alert-banner" role="alert">
        🚨 Cyber Emergency? Call <strong>1930</strong> immediately &nbsp;|&nbsp;
        <Link to="/emergency">View all helplines →</Link>
      </div>

      <nav className="navbar" role="navigation" aria-label="Main navigation">
        <div className="nav-inner">
          {/* Logo */}
          <Link to="/" className="nav-logo" aria-label="CrimeShield AI Home" onClick={closeMenu}>
            <div className="nav-logo-icon">
              <img src="/images/logo.jpg" alt="CrimeShield AI Logo" onError={(e) => { e.target.style.display='none'; }} />
            </div>
            <div className="nav-logo-text">
              <h1>CrimeShield AI</h1>
              <span>SECURE PORTAL</span>
            </div>
          </Link>

          {/* Desktop nav links */}
          <div className={`nav-links${menuOpen ? ' open' : ''}`}>
            <NavLink to="/"          className={({isActive}) => 'nav-link' + (isActive ? ' active' : '')} end onClick={closeMenu}>Home</NavLink>
            {isAuthenticated && (
              <NavLink to="/report"   className={({isActive}) => 'nav-link' + (isActive ? ' active' : '')} onClick={closeMenu}>Report Crime</NavLink>
            )}
            <NavLink to="/chatbot"  className={({isActive}) => 'nav-link' + (isActive ? ' active' : '')} onClick={closeMenu}>AI Chat</NavLink>
            <NavLink to="/awareness" className={({isActive}) => 'nav-link' + (isActive ? ' active' : '')} onClick={closeMenu}>Awareness</NavLink>
            <NavLink to="/emergency" className={({isActive}) => 'nav-link' + (isActive ? ' active' : '')} onClick={closeMenu}>Emergency</NavLink>
            {isAuthenticated && (
              <NavLink to="/dashboard" className={({isActive}) => 'nav-link' + (isActive ? ' active' : '')} onClick={closeMenu}>Dashboard</NavLink>
            )}
            {isAdmin && (
              <NavLink to="/admin" className={({isActive}) => 'nav-link' + (isActive ? ' active' : '')} onClick={closeMenu}>Admin</NavLink>
            )}
          </div>

          {/* Actions */}
          <div className="nav-actions">
            <Link to="/emergency" className="nav-emergency" aria-label="Emergency helpline 1930">
              <div className="pulse-dot" aria-hidden="true" />
              1930
            </Link>

            {isAuthenticated ? (
              <div className="nav-user-info">
                <div className="nav-avatar" aria-hidden="true">{initials}</div>
                <span>{user?.name?.split(' ')[0]}</span>
                <button
                  className="nav-logout-btn"
                  onClick={handleLogout}
                  aria-label="Logout"
                  title="Logout"
                >
                  ⏻
                </button>
              </div>
            ) : (
              <>
                <Link to="/login"    className="nav-btn-login"    id="nav-login-btn">Login</Link>
                <Link to="/register" className="nav-btn-register" id="nav-register-btn">Register</Link>
              </>
            )}

            {/* Mobile toggle */}
            <button
              className="nav-toggle"
              onClick={() => setMenuOpen((p) => !p)}
              aria-label="Toggle navigation menu"
              aria-expanded={menuOpen}
            >
              {menuOpen ? '✕' : '☰'}
            </button>
          </div>
        </div>
      </nav>
    </>
  );
}
