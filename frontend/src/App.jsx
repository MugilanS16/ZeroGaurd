// src/App.jsx
// Root: routing, global providers, persistent components
import React, { Suspense, lazy } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';

import { AuthProvider } from './context/AuthContext';
import Navbar from './components/Navbar';
import Footer from './components/Footer';
import ProtectedRoute from './components/ProtectedRoute';
import LoadingSpinner from './components/LoadingSpinner';
import ErrorBoundary from './components/ErrorBoundary';

// Lazy-load pages for code-splitting
const Home           = lazy(() => import('./pages/Home'));
const Login          = lazy(() => import('./pages/Login'));
const Register       = lazy(() => import('./pages/Register'));
const ReportForm     = lazy(() => import('./pages/ReportForm'));
const UserDashboard  = lazy(() => import('./pages/UserDashboard'));
const AdminDashboard = lazy(() => import('./pages/AdminDashboard'));
const ReportDetail   = lazy(() => import('./pages/ReportDetail'));
const Awareness      = lazy(() => import('./pages/Awareness'));
const Emergency      = lazy(() => import('./pages/Emergency'));
const NotFound       = lazy(() => import('./pages/NotFound'));

// Chatbot widget (loaded lazily, rendered for all authenticated users)
const ChatbotWidget  = lazy(() => import('./components/ChatbotWidget'));

function App() {
  return (
    <Router>
      <ErrorBoundary>
        <AuthProvider>
          {/* Background mesh */}
          <div className="mesh-bg" aria-hidden="true" />

          {/* Global toast notifications */}
          <Toaster
            position="top-right"
            toastOptions={{
              style: {
                background: 'var(--bg-card)',
                color: 'var(--text-primary)',
                border: '1px solid var(--border-subtle)',
                fontSize: '0.9rem',
                fontFamily: 'var(--font-sans)',
              },
              success: { iconTheme: { primary: 'var(--severity-low)', secondary: '#fff' } },
              error:   { iconTheme: { primary: 'var(--severity-critical)', secondary: '#fff' } },
            }}
          />

          <Navbar />

          <main id="main-content">
            <Suspense fallback={<LoadingSpinner fullPage label="Loading page…" />}>
              <Routes>
                {/* Public routes */}
                <Route path="/"          element={<Home />} />
                <Route path="/login"     element={<Login />} />
                <Route path="/register"  element={<Register />} />
                <Route path="/awareness" element={<Awareness />} />
                <Route path="/emergency" element={<Emergency />} />
                <Route path="/chatbot"   element={<Awareness />} />

                {/* Protected: authenticated citizens */}
                <Route
                  path="/report"
                  element={
                    <ProtectedRoute>
                      <ReportForm />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/dashboard"
                  element={
                    <ProtectedRoute>
                      <UserDashboard />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/reports/:id"
                  element={
                    <ProtectedRoute>
                      <ReportDetail />
                    </ProtectedRoute>
                  }
                />

                {/* Admin-only command & control */}
                <Route
                  path="/admin"
                  element={
                    <ProtectedRoute adminOnly>
                      <AdminDashboard />
                    </ProtectedRoute>
                  }
                />

                {/* 404 */}
                <Route path="*" element={<NotFound />} />
              </Routes>
            </Suspense>
          </main>

          {/* Persistent AI chatbot widget */}
          <Suspense fallback={null}>
            <ChatbotWidget />
          </Suspense>

          <Footer />
        </AuthProvider>
      </ErrorBoundary>
    </Router>
  );
}

export default App;
