// ZeroGuard AI Chatbot Controller
document.addEventListener('DOMContentLoaded', () => {
  const chatMessages = document.getElementById('chat-messages');
  const chatInput = document.getElementById('chat-input');
  const sendBtn = document.getElementById('chat-send-btn');
  const suggestionsContainer = document.getElementById('chat-suggestions');
  const clearBtn = document.getElementById('chat-clear-btn');
  const langSelect = document.getElementById('chat-lang-select');

  let conversationHistory = [];
  let currentLanguage = localStorage.getItem('chat_language') || 'en';

  const DEFAULT_CHIPS_BY_LANG = {
    en: [
      'How do I report UPI fraud?',
      'What should I do for Sextortion blackmail?',
      'What is the 1930 helpline?',
      'How to file an official complaint?'
    ],
    hi: [
      'यूपीआई धोखाधड़ी की रिपोर्ट कैसे करें?',
      'सेक्सटॉर्शन और ब्लैकमेल में क्या करें?',
      '1930 हेल्पलाइन क्या है?',
      'आधिकारिक शिकायत कैसे दर्ज करें?'
    ],
    ta: [
      'யுபிஐ மோசடியைப் புகார் செய்வது எப்படி?',
      'செக்ஸ்டார்ஷன் மிரட்டலுக்கு என்ன செய்ய வேண்டும்?',
      '1930 உதவி எண் என்றால் என்ன?',
      'அதிகாரப்பூர்வ புகாரை அளிப்பது எப்படி?'
    ],
    te: [
      'యుపిఐ మోసాన్ని ఎలా నివేదించాలి?',
      'సెక్స్‌టార్షన్ బ్లాక్‌మెయిల్‌కు ఏమి చేయాలి?',
      '1930 హెల్ప్‌లైన్ అంటే ఏమిటి?',
      'అధికారిక ఫిర్యాదును ఎలా నమోదు చేయాలి?'
    ]
  };

  const WELCOME_MSGS_BY_LANG = {
    en: '<strong>Hello! I am ZeroGuard AI Assistant.</strong><br/>I can help you understand cybercrime laws (IT Act), explain report wizard steps, provide emergency containment steps, and guide evidence preservation.<br/><br/>How can I help you today?',
    hi: '<strong>नमस्ते! मैं ZeroGuard AI सहायक हूँ।</strong><br/>मैं साइबर अपराध कानूनों (IT Act), आपातकालीन सुरक्षा कदमों, और शिकायत दर्ज करने की प्रक्रिया में आपकी मदद कर सकता हूँ।<br/><br/>आज मैं आपकी क्या सहायता कर सकता हूँ?',
    ta: '<strong>வணக்கம்! நான் ZeroGuard AI உதவியாளன்.</strong><br/>சைபர் குற்றச் சட்டங்கள் (IT Act), அவசரப் பாதுகாப்பு முறைகள் மற்றும் புகார் பதிவு செய்யும் வழிகாட்டலை நான் உங்களுக்கு வழங்க முடியும்.<br/><br/>இன்று நான் உங்களுக்கு எவ்வாறு உதவட்டும்?',
    te: '<strong>నమస్కారం! నేను ZeroGuard AI సహాయకుడిని.</strong><br/>సైబర్ నేరాల చట్టాలు (IT Act), అత్యవసర భద్రతా చర్యలు మరియు ఫిర్యాదు నమోదు చేయడంలో నేను మీకు సహాయం చేయగలను.<br/><br/>ఈ రోజు నేను మీకు ఎలా సహాయపడగలను?'
  };

  let isManualOverride = false;

  if (langSelect) {
    langSelect.value = currentLanguage;
    langSelect.addEventListener('change', () => {
      currentLanguage = langSelect.value;
      isManualOverride = true;
      localStorage.setItem('chat_language', currentLanguage);
      renderSuggestions(DEFAULT_CHIPS_BY_LANG[currentLanguage] || DEFAULT_CHIPS_BY_LANG.en);
    });
  }

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
    const typingText = currentLanguage === 'hi' ? 'ZeroGuard AI सहायक उत्तर लिख रहा है...' 
      : (currentLanguage === 'ta' ? 'ZeroGuard AI பதிலளிக்கிறது...' 
      : (currentLanguage === 'te' ? 'ZeroGuard AI సమాధానం ఇస్తోంది...' : 'ZeroGuard AI Assistant is typing...'));

    indicator.innerHTML = `
      <div class="chat-avatar ai-avatar">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon></svg>
      </div>
      <div class="chat-content typing-indicator">
        <span style="font-size: 0.85rem; font-weight: 500; color: var(--text-muted); margin-right: 4px;">${typingText}</span>
        <div class="typing-dots-group">
          <div class="typing-dot"></div>
          <div class="typing-dot"></div>
          <div class="typing-dot"></div>
        </div>
      </div>
    `;
    chatMessages.appendChild(indicator);
    scrollToBottom();
    return indicator;
  }

  function renderSuggestions(suggestions) {
    if (!suggestionsContainer) return;
    suggestionsContainer.innerHTML = '';
    
    (suggestions || DEFAULT_CHIPS_BY_LANG[currentLanguage] || DEFAULT_CHIPS_BY_LANG.en).forEach(text => {
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
        history: conversationHistory,
        language: currentLanguage,
        is_manual_override: isManualOverride
      })
    })
    .then(res => {
      if (!res.ok) {
        throw new Error(`HTTP error! status: ${res.status}`);
      }
      return res.json();
    })
    .then(data => {
      typingElem.remove();
      if (sendBtn) sendBtn.disabled = false;

      // Sync dropdown UI and language state with script-detected language
      if (data && data.detected_language) {
        currentLanguage = data.detected_language;
        localStorage.setItem('chat_language', currentLanguage);
        if (langSelect) {
          langSelect.value = currentLanguage;
        }
        isManualOverride = false;
      }

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
      console.error('Chatbot error:', err);
      typingElem.remove();
      if (sendBtn) sendBtn.disabled = false;
      appendMessage('ai', `I'm having trouble responding right now. In the meantime, you can call <strong>1930</strong> for urgent help, or try one of the quick questions below.`);
      renderSuggestions(DEFAULT_CHIPS_BY_LANG[currentLanguage] || DEFAULT_CHIPS_BY_LANG.en);
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
        appendMessage('ai', WELCOME_MSGS_BY_LANG[currentLanguage] || WELCOME_MSGS_BY_LANG.en);
        renderSuggestions(DEFAULT_CHIPS_BY_LANG[currentLanguage] || DEFAULT_CHIPS_BY_LANG.en);
      }
    });
  }

  // Initial welcome message
  if (chatMessages && chatMessages.children.length === 0) {
    appendMessage('ai', WELCOME_MSGS_BY_LANG[currentLanguage] || WELCOME_MSGS_BY_LANG.en);
    renderSuggestions(DEFAULT_CHIPS_BY_LANG[currentLanguage] || DEFAULT_CHIPS_BY_LANG.en);
  }
});

