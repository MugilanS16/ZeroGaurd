// src/components/ErrorBoundary.jsx
import React from 'react';
import { Link } from 'react-router-dom';

export default class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('Uncaught error in React tree:', error, errorInfo);
  }

  handleReload = () => {
    window.location.reload();
  };

  render() {
    if (this.state.hasError) {
      return (
        <div className="page-wrapper container" style={{ textAlign: 'center', padding: '5rem 1rem' }}>
          <div style={{ fontSize: '4rem', marginBottom: '1rem' }}>⚠️</div>
          <h2 style={{ fontSize: '1.75rem', marginBottom: '0.5rem' }}>Something went wrong</h2>
          <p style={{ color: 'var(--text-secondary)', maxWidth: '480px', margin: '0 auto 2rem' }}>
            An unexpected error occurred in this view. Don't worry, your data and authentication state are safe.
          </p>
          <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center' }}>
            <button onClick={this.handleReload} className="btn btn-primary">
              🔄 Reload Application
            </button>
            <Link to="/" className="btn btn-secondary">
              Go to Home
            </Link>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
