// src/context/AuthContext.jsx
// Global auth state: JWT in localStorage + in-memory user object
import React, { createContext, useState, useEffect, useCallback } from 'react';
import { loginUser, registerUser, logoutUser, getMe } from '../api/auth';

export const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);       // { id, name, email, role }
  const [token, setToken] = useState(() => localStorage.getItem('access_token'));
  const [loading, setLoading] = useState(true); // resolves on first mount

  // Hydrate user from token on mount
  useEffect(() => {
    if (token) {
      getMe()
        .then((res) => setUser(res.data.user))
        .catch(() => {
          localStorage.removeItem('access_token');
          setToken(null);
        })
        .finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, [token]);

  const login = useCallback(async (email, password) => {
    const res = await loginUser(email, password);
    const { access_token, user: userData } = res.data;
    localStorage.setItem('access_token', access_token);
    setToken(access_token);
    setUser(userData);
    return userData;
  }, []);

  const register = useCallback(async (fullname, email, phone, password) => {
    const res = await registerUser(fullname, email, phone, password);
    const { access_token, user: userData } = res.data;
    localStorage.setItem('access_token', access_token);
    setToken(access_token);
    setUser(userData);
    return userData;
  }, []);

  const logout = useCallback(async () => {
    try { await logoutUser(); } catch (_) { /* ignore */ }
    localStorage.removeItem('access_token');
    setToken(null);
    setUser(null);
  }, []);

  const isAdmin = user?.role === 'admin';
  const isAuthenticated = !!user;

  return (
    <AuthContext.Provider value={{ user, token, loading, isAuthenticated, isAdmin, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}
