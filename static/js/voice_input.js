// ZeroGuard AI Web Speech Voice Input Module
document.addEventListener('DOMContentLoaded', () => {
  const micBtn = document.getElementById('btn-voice-input');
  const micBtnText = document.getElementById('voice-btn-text');
  const descInput = document.getElementById('raw_description');
  const listeningIndicator = document.getElementById('voice-listening-indicator');
  const voiceLangSelect = document.getElementById('voice-lang-select');
  const mainLangSelect = document.getElementById('language-select');
  const voiceStatusMsg = document.getElementById('voice-status-msg');

  if (!micBtn || !descInput) return;

  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

  if (!SpeechRecognition) {
    console.error('[Voice Input Error] Neither SpeechRecognition nor webkitSpeechRecognition is supported in this browser.');
    if (voiceStatusMsg) {
      voiceStatusMsg.style.display = 'block';
      voiceStatusMsg.innerHTML = '<span style="color: var(--text-muted); font-size: 0.82rem;">ℹ️ Voice input is not supported in this browser — try Chrome, Edge, or Brave.</span>';
    }
    micBtn.disabled = true;
    micBtn.style.opacity = '0.5';
    micBtn.title = 'Voice input not supported in this browser';
    return;
  }

  let recognition = null;
  let isListening = false;
  let manualStop = false;
  let accumulatedText = '';

  try {
    recognition = new SpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = true;
    console.log('[Voice Input Init] SpeechRecognition / webkitSpeechRecognition initialized successfully.');
  } catch (err) {
    console.error('[Voice Input Init Error] Failed to instantiate SpeechRecognition:', err);
    return;
  }

  // Helper: Detect if host is secure or localhost for Web Speech API
  function isLocalhostOrSecure() {
    if (window.isSecureContext === false) return false;
    if (location.protocol === 'https:') return true;
    if (location.hostname === 'localhost') return true;
    return false; // 127.0.0.1 or raw IP addresses under http: are often blocked by browsers for microphone Web Speech API
  }

  // Sync main language dropdown with voice language dropdown
  if (mainLangSelect && voiceLangSelect) {
    mainLangSelect.addEventListener('change', () => {
      const val = mainLangSelect.value;
      if (val === 'en') voiceLangSelect.value = 'en-IN';
      else if (val === 'hi') voiceLangSelect.value = 'hi-IN';
      else if (val === 'ta') voiceLangSelect.value = 'ta-IN';
      else if (val === 'te') voiceLangSelect.value = 'te-IN';
    });
  }

  function getSelectedLanguage() {
    return voiceLangSelect ? voiceLangSelect.value : 'en-IN';
  }

  function setStatusMessage(msg, isError = false) {
    if (!voiceStatusMsg) return;
    voiceStatusMsg.style.display = 'block';
    if (isError) {
      voiceStatusMsg.style.borderColor = 'rgba(239, 68, 68, 0.4)';
      voiceStatusMsg.style.background = 'rgba(239, 68, 68, 0.1)';
      voiceStatusMsg.innerHTML = `<span style="color: var(--danger); font-weight: 600;">⚠️ ${msg}</span>`;
    } else {
      voiceStatusMsg.style.borderColor = 'var(--border-subtle)';
      voiceStatusMsg.style.background = 'var(--bg-surface-subtle)';
      voiceStatusMsg.innerHTML = `<span>${msg}</span>`;
    }
  }

  recognition.onstart = () => {
    console.log('[Voice Input Event] SpeechRecognition onstart triggered.');
    isListening = true;
    manualStop = false;
    micBtn.classList.add('active');
    if (micBtnText) micBtnText.textContent = 'Stop Listening';
    if (listeningIndicator) listeningIndicator.style.display = 'inline-flex';

    // Store existing text to append seamlessly
    accumulatedText = descInput.value;
    if (accumulatedText && !accumulatedText.endsWith(' ') && !accumulatedText.endsWith('\n')) {
      accumulatedText += ' ';
    }

    const langLabel = voiceLangSelect ? voiceLangSelect.options[voiceLangSelect.selectedIndex].text : 'English';
    setStatusMessage(`🎤 <strong>Listening (${langLabel})...</strong> Speak your complaint clearly into your microphone.`);
  };

  recognition.onresult = (event) => {
    let interimTranscript = '';
    let finalTranscript = '';

    for (let i = event.resultIndex; i < event.results.length; ++i) {
      const transcript = event.results[i][0].transcript;
      if (event.results[i].isFinal) {
        finalTranscript += transcript + ' ';
      } else {
        interimTranscript += transcript;
      }
    }

    if (finalTranscript) {
      accumulatedText += finalTranscript;
      console.log('[Voice Input Result] Final transcript:', finalTranscript);
    }

    descInput.value = accumulatedText + interimTranscript;

    // Trigger input event to update Live AI Triage Panel dynamically
    descInput.dispatchEvent(new Event('input', { bubbles: true }));
  };

  recognition.onerror = (event) => {
    console.error('[Voice Input SpeechRecognition Error]', event.error, event);
    
    if (event.error === 'not-allowed' || event.error === 'permission-denied' || event.error === 'service-not-allowed') {
      if (location.hostname === '127.0.0.1') {
        setStatusMessage('🔒 Web Speech API requires accessing the site via <a href="http://localhost:5000/report" style="color: var(--primary); font-weight:700; text-decoration:underline;">http://localhost:5000</a> instead of 127.0.0.1.', true);
      } else if (!isLocalhostOrSecure()) {
        setStatusMessage('🔒 Voice input requires a secure connection — please access this site via <strong>http://localhost:5000</strong> or HTTPS.', true);
      } else {
        setStatusMessage('Microphone access denied — please click the lock/camera icon in your address bar and ensure Microphone is set to "Allow".', true);
      }
    } else if (event.error === 'no-speech') {
      setStatusMessage('No speech detected. Please click the mic button and try speaking again.', true);
    } else if (event.error === 'network') {
      if (location.hostname === '127.0.0.1') {
        setStatusMessage('🔒 Web Speech network service requires <a href="http://localhost:5000/report" style="color: var(--primary); font-weight:700; text-decoration:underline;">http://localhost:5000</a>. Please switch to localhost:5000.', true);
      } else {
        setStatusMessage('Network connection issue with speech service. Chrome Speech API requires active internet access.', true);
      }
    } else if (event.error === 'audio-capture') {
      setStatusMessage('No audio capture hardware found. Please check your microphone connection.', true);
    } else {
      setStatusMessage(`Speech recognition error (${event.error}). Try switching to <a href="http://localhost:5000/report">localhost:5000</a> or type directly.`, true);
    }
    stopListening();
  };

  recognition.onend = () => {
    console.log('[Voice Input Event] SpeechRecognition onend triggered.');
    stopListening();
  };

  async function startListening() {
    if (isListening) return;

    if (location.hostname === '127.0.0.1') {
      console.warn('[Voice Input] Warning: Site loaded over 127.0.0.1. Web Speech API browser permissions require http://localhost:5000');
    }

    setStatusMessage('⏳ Verifying microphone permissions...');

    // 1. Pre-flight microphone permission check via getUserMedia
    if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        // Immediately release media stream tracks after permission verification
        stream.getTracks().forEach(track => track.stop());
        console.log('[Voice Input] Pre-flight getUserMedia success: Microphone permission granted.');
      } catch (err) {
        console.error('[Voice Input Pre-Flight Error]', err.name, err.message, err);
        
        let errorMsg = '';
        if (err.name === 'NotAllowedError' || err.name === 'PermissionDeniedError') {
          if (location.hostname === '127.0.0.1') {
            errorMsg = '🔒 Microphone blocked on 127.0.0.1. Please switch to <a href="http://localhost:5000/report" style="color: var(--primary); font-weight:700; text-decoration:underline;">http://localhost:5000</a> for speech permissions.';
          } else {
            errorMsg = 'Microphone permission denied by browser. Click the lock icon in your address bar and set Microphone to "Allow".';
          }
        } else if (err.name === 'NotFoundError' || err.name === 'DevicesNotFoundError') {
          errorMsg = 'No microphone device found. Please connect a microphone or headset and try again.';
        } else if (err.name === 'NotReadableError' || err.name === 'TrackStartError') {
          errorMsg = 'Microphone is currently in use by another application (e.g. Teams, Zoom, Discord). Please close other apps.';
        } else if (err.name === 'SecurityError') {
          errorMsg = '🔒 Voice input requires a secure connection — please access this site via http://localhost:5000 or HTTPS.';
        } else {
          errorMsg = `Microphone error (${err.name}: ${err.message}). Please check your audio settings.`;
        }

        setStatusMessage(errorMsg, true);
        return;
      }
    } else {
      console.warn('[Voice Input] navigator.mediaDevices.getUserMedia not supported in this browser context.');
    }

    // 2. Start SpeechRecognition
    try {
      recognition.lang = getSelectedLanguage();
      console.log('[Voice Input] Starting SpeechRecognition with language:', recognition.lang);
      recognition.start();
    } catch (e) {
      console.error('[Voice Input SpeechRecognition Start Error]', e);
      if (location.hostname === '127.0.0.1') {
        setStatusMessage('🔒 Voice input requires accessing via <a href="http://localhost:5000/report" style="color: var(--primary); font-weight:700; text-decoration:underline;">http://localhost:5000</a> instead of 127.0.0.1.', true);
      } else {
        setStatusMessage(`Could not start speech recognition (${e.message || e}). Please try again or type directly.`, true);
      }
    }
  }

  function stopListening() {
    isListening = false;
    manualStop = true;
    try {
      recognition.stop();
    } catch (e) {}
    
    micBtn.classList.remove('active');
    if (micBtnText) micBtnText.textContent = 'Voice Input';
    if (listeningIndicator) listeningIndicator.style.display = 'none';
  }

  micBtn.addEventListener('click', () => {
    if (isListening) {
      stopListening();
      setStatusMessage('✅ Voice recording stopped. You can edit your narrative or click <strong>Polish with AI</strong>.');
    } else {
      startListening();
    }
  });

  // Default initial help text
  if (location.hostname === '127.0.0.1') {
    setStatusMessage('🎤 <strong>Voice Input Tip:</strong> Web Speech API works best on <a href="http://localhost:5000/report" style="color: var(--primary); font-weight:700; text-decoration:underline;">http://localhost:5000</a> (click to switch if mic is blocked).');
  } else {
    setStatusMessage('🎤 <strong>Voice Input:</strong> Click the mic, select your language, and speak your complaint — we\'ll convert it to text automatically.');
  }
});
