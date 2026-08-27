// ZeroGuard AI Chatbot Controller
document.addEventListener('DOMContentLoaded', () => {
  const chatMessages = document.getElementById('chat-messages');
  const chatInput = document.getElementById('chat-input');
  const sendBtn = document.getElementById('chat-send-btn');
  const suggestionsContainer = document.getElementById('chat-suggestions');
  const clearBtn = document.getElementById('chat-clear-btn');

  let conversationHistory = [];

  function scrollToBottom() {
    if (chatMessages) {
      chatMessages.scrollTop = chatMessages.scrollHeight;
    }
  }

  function appendMessage(role, htmlContent) {
    const bubble = document.createElement('div');
    bubble.className = `chat-bubble ${role}`;

    const avatar = document.createElement('div');
    avatar.className = `chat-avatar ${role === 'ai' ? 'ai-avatar' : 'user-avatar'}`;
    avatar.innerHTML = role === 'ai' 
      ? `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon></svg>`
      : `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>`;

    const content = document.createElement('div');
    content.className = 'chat-content';
    content.innerHTML = htmlContent;

    bubble.appendChild(avatar);
    bubble.appendChild(content);
    chatMessages.appendChild(bubble);
    scrollToBottom();
    return bubble;
  }

  function appendTypingIndicator() {
    const indicator = document.createElement('div');
    indicator.className = 'chat-bubble ai typing-indicator-bubble';
    indicator.innerHTML = `
      <div class="chat-avatar ai-avatar">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon></svg>
      </div>
      <div class="chat-content typing-indicator">
        <div class="typing-dot"></div>
        <div class="typing-dot"></div>
        <div class="typing-dot"></div>
      </div>
    `;
    chatMessages.appendChild(indicator);
    scrollToBottom();
    return indicator;
  }

  function renderSuggestions(suggestions) {
    if (!suggestionsContainer) return;
    suggestionsContainer.innerHTML = '';
    
    (suggestions || []).forEach(text => {
      const chip = document.createElement('button');
      chip.type = 'button';
      chip.className = 'chip-btn';
      chip.textContent = text;
      chip.addEventListener('click', () => {
        if (chatInput) {
          chatInput.value = text;
          sendMessage();
        }
      });
      suggestionsContainer.appendChild(chip);
    });
  }

  function sendMessage() {
    if (!chatInput) return;
    const msg = chatInput.value.trim();
    if (!msg) return;

    // Append user message
    appendMessage('user', escapeHtml(msg));
    conversationHistory.push({ role: 'user', text: msg });
    chatInput.value = '';
    chatInput.focus();

    // Show typing indicator
    const typingElem = appendTypingIndicator();

    if (sendBtn) sendBtn.disabled = true;

    fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message: msg,
        history: conversationHistory
      })
    })
    .then(res => res.json())
    .then(data => {
      typingElem.remove();
      if (sendBtn) sendBtn.disabled = false;

      if (data && data.response) {
        let aiHtml = `<div>${data.response}</div>`;
        if (data.source) {
          aiHtml += `<div style="font-size: 0.72rem; color: var(--text-muted); margin-top: 0.5rem; border-top: 1px solid var(--border-subtle); padding-top: 0.35rem;">Assistance via ${data.source}</div>`;
        }
        appendMessage('ai', aiHtml);
        conversationHistory.push({ role: 'model', text: data.response });

        if (data.suggestions && data.suggestions.length > 0) {
          renderSuggestions(data.suggestions);
        }
      }
    })
    .catch(err => {
      typingElem.remove();
      if (sendBtn) sendBtn.disabled = false;
      appendMessage('ai', '⚠️ Unable to connect to assistant service. Please check your network or try again.');
    });
  }

  function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  if (sendBtn) {
    sendBtn.addEventListener('click', sendMessage);
  }

  if (chatInput) {
    chatInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        e.preventDefault();
        sendMessage();
      }
    });
  }

  if (clearBtn) {
    clearBtn.addEventListener('click', () => {
      if (chatMessages) {
        chatMessages.innerHTML = '';
        conversationHistory = [];
        appendMessage('ai', `<strong>Hello! I am ZeroGuard AI Assistant.</strong><br/>How can I assist you with cybercrime reporting, 1930 helpline guidance, or account security today?`);
        renderSuggestions([
          'How do I report UPI fraud?',
          'What should I do for Sextortion blackmail?',
          'What is the 1930 helpline?',
          'How to file an official complaint?'
        ]);
      }
    });
  }

  // Initial welcome message
  if (chatMessages && chatMessages.children.length === 0) {
    appendMessage('ai', `<strong>Hello! I am ZeroGuard AI Assistant.</strong><br/>I can help you understand cybercrime laws (IT Act), explain report wizard steps, provide emergency containment steps, and guide evidence preservation.<br/><br/>How can I help you today?`);
    renderSuggestions([
      'How do I report UPI fraud?',
      'What should I do for Sextortion blackmail?',
      'What is the 1930 helpline?',
      'How to file an official complaint?'
    ]);
  }
});
