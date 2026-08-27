// src/components/ChatbotWidget.jsx
import React, { useState, useRef, useEffect } from 'react';
import { useAuth } from '../hooks/useAuth';
import { sendChatMessage } from '../api/aiCrime';
import './ChatbotWidget.css';

const QUICK_PROMPTS = [
  '📞 Helpline numbers',
  '🏦 How to freeze bank account',
  '📸 Evidence to collect',
  '📝 Steps to file a complaint',
];

export default function ChatbotWidget() {
  const { isAuthenticated } = useAuth();

  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      text: "👋 Hello! I am your **CrimeShield AI Safety Assistant**.\n\nDescribe any suspicious activity or cyber incident, and I will guide you through immediate recovery and evidence preservation steps.",
    },
  ]);
  const [input, setInput] = useState('');
  const [crimeType, setCrimeType] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  const messagesEndRef = useRef(null);

  // Auto scroll to bottom of chat
  useEffect(() => {
    if (isOpen) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, isOpen]);

  // Don't render for unauthenticated visitors
  if (!isAuthenticated) return null;

  const handleSend = async (textToSend) => {
    const message = (textToSend || input).trim();
    if (!message || isLoading) return;

    // Add user message to UI
    const updatedHistory = [...messages, { role: 'user', text: message }];
    setMessages(updatedHistory);
    setInput('');
    setIsLoading(true);

    try {
      // Backend expects: { message, history: [{role, text}], crime_type }
      const res = await sendChatMessage(message, messages);
      const data = res.data;

      if (data.crime_type) {
        setCrimeType(data.crime_type);
      }

      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          text: data.reply || 'I am processing your query. Please stand by.',
          crimeType: data.crime_type,
          risk: data.risk,
        },
      ]);
    } catch (err) {
      console.error('Chat error:', err);
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          text: "⚠️ I'm having trouble connecting to the AI service. If this is an emergency, please call **1930** immediately.",
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleReset = () => {
    setCrimeType(null);
    setMessages([
      {
        role: 'assistant',
        text: "🔄 Incident reset. Describe a new situation, and I'll classify it and provide fresh safety guidance.",
      },
    ]);
  };

  // Simple formatter for **bold** and bullet lines
  const renderFormattedText = (text) => {
    if (!text) return null;
    const lines = text.split('\n');
    return lines.map((line, idx) => {
      // Replace **bold** with <strong>
      const parts = line.split(/(\*\*.*?\*\*)/g);
      const formattedParts = parts.map((part, pIdx) => {
        if (part.startsWith('**') && part.endsWith('**')) {
          return <strong key={pIdx}>{part.slice(2, -2)}</strong>;
        }
        return part;
      });

      return (
        <React.Fragment key={idx}>
          {formattedParts}
          {idx < lines.length - 1 && <br />}
        </React.Fragment>
      );
    });
  };

  return (
    <div className="chatbot-root" aria-label="AI Safety Chatbot">
      {/* Expanded Chat Window */}
      {isOpen && (
        <div className="chat-window card animate-fade-up">
          {/* Header */}
          <div className="chat-header">
            <div className="chat-header-info">
              <div className="chat-avatar">🛡️</div>
              <div>
                <h4>CrimeShield AI Assistant</h4>
                <span className="chat-status">
                  <span className="pulse-dot" /> 24×7 Active
                  {crimeType && <span className="chat-crime-tag"> • {crimeType}</span>}
                </span>
              </div>
            </div>

            <div className="chat-header-actions">
              <button
                className="chat-btn-icon"
                onClick={handleReset}
                title="Reset conversation"
                aria-label="Reset conversation"
              >
                🔄
              </button>
              <button
                className="chat-btn-icon"
                onClick={() => setIsOpen(false)}
                title="Minimize chat"
                aria-label="Minimize chat"
              >
                ✕
              </button>
            </div>
          </div>

          {/* Messages Body */}
          <div className="chat-body">
            {messages.map((msg, index) => (
              <div
                key={index}
                className={`chat-msg ${msg.role === 'user' ? 'msg-user' : 'msg-assistant'}`}
              >
                {msg.role === 'assistant' && (
                  <div className="msg-avatar" aria-hidden="true">🤖</div>
                )}
                <div className="msg-bubble">
                  {renderFormattedText(msg.text)}
                </div>
              </div>
            ))}

            {isLoading && (
              <div className="chat-msg msg-assistant">
                <div className="msg-avatar" aria-hidden="true">🤖</div>
                <div className="msg-bubble msg-typing">
                  <span className="dot" />
                  <span className="dot" />
                  <span className="dot" />
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Quick Prompts */}
          <div className="quick-prompts">
            {QUICK_PROMPTS.map((prompt) => (
              <button
                key={prompt}
                className="quick-prompt-btn"
                onClick={() => handleSend(prompt)}
                disabled={isLoading}
              >
                {prompt}
              </button>
            ))}
          </div>

          {/* Input Footer */}
          <div className="chat-footer">
            <input
              type="text"
              className="chat-input"
              placeholder="Ask a question or describe an issue…"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              disabled={isLoading}
            />
            <button
              className="chat-send-btn"
              onClick={() => handleSend()}
              disabled={isLoading || !input.trim()}
              aria-label="Send message"
            >
              ➤
            </button>
          </div>
        </div>
      )}

      {/* Floating Toggle Button */}
      <button
        id="chatbot-toggle-btn"
        className={`chat-floating-btn ${isOpen ? 'active' : ''}`}
        onClick={() => setIsOpen((prev) => !prev)}
        aria-label={isOpen ? 'Close AI Chat' : 'Open CrimeShield AI Assistant'}
        aria-expanded={isOpen}
      >
        <span className="chat-floating-icon">{isOpen ? '✕' : '💬'}</span>
        {!isOpen && <span className="chat-floating-label">AI Assistant</span>}
        {!isOpen && <span className="chat-floating-badge pulse-dot" />}
      </button>
    </div>
  );
}
