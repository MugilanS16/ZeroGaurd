// ZeroGuard AI - "Am I a Victim?" Quick Self-Check Interactive Engine
document.addEventListener('DOMContentLoaded', () => {
  const quizSection = document.getElementById('victim-quiz-section');
  if (!quizSection) return;

  const introView = document.getElementById('quiz-intro-view');
  const activeView = document.getElementById('quiz-active-view');
  const resultView = document.getElementById('quiz-result-view');

  const btnStart = document.getElementById('quiz-btn-start');
  const btnRestart = document.getElementById('quiz-btn-restart');
  const btnYes = document.getElementById('quiz-btn-yes');
  const btnNo = document.getElementById('quiz-btn-no');
  const btnPrev = document.getElementById('quiz-btn-prev');

  const stepIndicator = document.getElementById('quiz-step-indicator');
  const progressBar = document.getElementById('quiz-progress-bar');
  const questionNumber = document.getElementById('quiz-question-number');
  const questionText = document.getElementById('quiz-question-text');
  const questionCategory = document.getElementById('quiz-question-category');
  const questionIcon = document.getElementById('quiz-question-icon');

  const resultBadge = document.getElementById('quiz-result-badge');
  const resultHeading = document.getElementById('quiz-result-heading');
  const resultDesc = document.getElementById('quiz-result-desc');
  const resultCategoriesContainer = document.getElementById('quiz-result-categories');
  const resultActionsContainer = document.getElementById('quiz-result-actions');

  const questions = [
    {
      id: 1,
      tag: "Impersonation & Phishing",
      icon: "🎣",
      text: "Did you receive an unexpected message, call, or link claiming to be from a bank, company, or government agency?",
      categoryMatch: {
        title: "Phishing & Impersonation Scam",
        icon: "🎣",
        desc: "Fake bank alerts, cloned links, or fraudulent authority calls."
      }
    },
    {
      id: 2,
      tag: "Credential & Identity Security",
      icon: "🔐",
      text: "Were you asked to share an OTP, password, PIN, or banking details?",
      categoryMatch: {
        title: "Credential Harvesting / Identity Theft",
        icon: "🔐",
        desc: "Unauthorized capture of OTPs, netbanking passwords, or KYC data."
      }
    },
    {
      id: 3,
      tag: "Financial Security",
      icon: "💳",
      text: "Did you lose money, or was money transferred from your account without your permission?",
      categoryMatch: {
        title: "Financial Loss & Payment Fraud",
        icon: "💳",
        desc: "Unauthorized UPI debits, payment link scams, or card compromises."
      }
    },
    {
      id: 4,
      tag: "Safety & Online Harassment",
      icon: "⚠️",
      text: "Has someone threatened you, harassed you, or shared/threatened to share your private photos or information online?",
      categoryMatch: {
        title: "Cyber Harassment, Doxxing or Sextortion",
        icon: "⚠️",
        desc: "Online extortion, photo morphing, abusive messages, or blackmail."
      }
    },
    {
      id: 5,
      tag: "Account Integrity",
      icon: "📱",
      text: "Has someone gained unauthorized access to your email, social media, or online accounts?",
      categoryMatch: {
        title: "Account Takeover & Hacking",
        icon: "📱",
        desc: "Compromised Instagram, WhatsApp, email, or digital cloud accounts."
      }
    }
  ];

  let currentQuestionIndex = 0;
  let userAnswers = []; // true for Yes, false for No

  // 1. Start Quiz
  if (btnStart) {
    btnStart.addEventListener('click', () => {
      currentQuestionIndex = 0;
      userAnswers = [];
      introView.style.display = 'none';
      resultView.style.display = 'none';
      activeView.style.display = 'block';
      renderQuestion(0);
      quizSection.scrollIntoView({ behavior: 'smooth', block: 'center' });
    });
  }

  // 2. Restart / Retake Quiz
  function restartQuiz() {
    currentQuestionIndex = 0;
    userAnswers = [];
    resultView.style.display = 'none';
    introView.style.display = 'block';
    activeView.style.display = 'none';
    quizSection.scrollIntoView({ behavior: 'smooth', block: 'center' });
  }

  if (btnRestart) {
    btnRestart.addEventListener('click', restartQuiz);
  }

  // 3. Render Question with smooth animation
  function renderQuestion(index) {
    const q = questions[index];
    if (!q) return;

    // Update Progress
    const total = questions.length;
    const progressPercent = Math.round(((index + 1) / total) * 100);
    stepIndicator.textContent = `Question ${index + 1} of ${total}`;
    progressBar.style.width = `${progressPercent}%`;

    // Update Question Content with Fade Animation
    const container = document.getElementById('quiz-question-box');
    container.classList.remove('quiz-fade-in');
    void container.offsetWidth; // trigger reflow
    container.classList.add('quiz-fade-in');

    questionNumber.textContent = `0${index + 1}`;
    questionCategory.textContent = q.tag;
    questionIcon.textContent = q.icon;
    questionText.textContent = q.text;

    // Previous Button Visibility
    if (index > 0) {
      btnPrev.style.display = 'inline-flex';
    } else {
      btnPrev.style.display = 'none';
    }
  }

  // 4. Handle Answer
  function handleAnswer(isYes) {
    userAnswers[currentQuestionIndex] = isYes;
    
    if (currentQuestionIndex < questions.length - 1) {
      currentQuestionIndex++;
      renderQuestion(currentQuestionIndex);
    } else {
      // Quiz Complete -> Render Results
      showResults();
    }
  }

  if (btnYes) {
    btnYes.addEventListener('click', () => handleAnswer(true));
  }

  if (btnNo) {
    btnNo.addEventListener('click', () => handleAnswer(false));
  }

  if (btnPrev) {
    btnPrev.addEventListener('click', () => {
      if (currentQuestionIndex > 0) {
        currentQuestionIndex--;
        renderQuestion(currentQuestionIndex);
      }
    });
  }

  // 5. Evaluate Results & Categories
  function showResults() {
    activeView.style.display = 'none';
    resultView.style.display = 'block';
    resultView.classList.remove('quiz-fade-in');
    void resultView.offsetWidth;
    resultView.classList.add('quiz-fade-in');

    const yesCount = userAnswers.filter(ans => ans === true).length;
    const matchedCategories = [];

    // Map specific questions to categories
    if (userAnswers[0] || userAnswers[1]) {
      matchedCategories.push({
        title: "Phishing & Impersonation Scam",
        icon: "🎣",
        desc: "Deceptive messages, fake bank links, or social engineering to capture OTPs/passwords."
      });
    }
    if (userAnswers[2]) {
      matchedCategories.push({
        title: "Financial Loss & Payment Fraud",
        icon: "💳",
        desc: "Unauthorized UPI debits, merchant QR scams, card skimming, or fraudulent wire transfers."
      });
    }
    if (userAnswers[3]) {
      matchedCategories.push({
        title: "Cyber Harassment, Doxxing & Sextortion",
        icon: "⚠️",
        desc: "Online blackmail, non-consensual image distribution, threats, or aggressive cyberstalking."
      });
    }
    if (userAnswers[4]) {
      matchedCategories.push({
        title: "Unauthorized Account Takeover & Hacking",
        icon: "📱",
        desc: "Compromised social media (Instagram, WhatsApp), email hijacking, or session theft."
      });
    }

    const reportUrl = quizSection.getAttribute('data-report-url') || '/report';
    const chatbotUrl = quizSection.getAttribute('data-chatbot-url') || '/chatbot';

    if (yesCount === 0) {
      // ZERO YES ANSWERS
      resultBadge.className = 'badge badge-success';
      resultBadge.textContent = '🛡️ Low Cybercrime Indicators';
      resultHeading.textContent = "Based on your answers, this doesn't appear to be a cybercrime";
      resultDesc.textContent = "None of the primary cyber offense patterns were detected based on your answers. However, if you are still concerned or noticed suspicious activity, our AI Assistant can help clarify your situation, or you can still file a report to be safe.";

      resultCategoriesContainer.innerHTML = `
        <div style="background: var(--bg-surface); border: 1px solid var(--border-subtle); border-radius: var(--radius-md); padding: 1rem 1.25rem; font-size: 0.9rem; color: var(--text-muted); display: flex; align-items: center; gap: 0.75rem;">
          <span style="font-size: 1.5rem;">💡</span>
          <div>
            <strong>Stay Vigilant:</strong> If you never shared passwords, OTPs, or money, your accounts remain secure. You can review safety tips or ask our AI assistant for specific advice.
          </div>
        </div>
      `;

      resultActionsContainer.innerHTML = `
        <div class="flex items-center justify-center gap-3 flex-wrap" style="margin-top: 1.5rem;">
          <a href="${chatbotUrl}" class="btn btn-ai btn-lg">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
            </svg>
            <span>Ask AI Assistant</span>
          </a>
          <a href="${reportUrl}" class="btn btn-outline btn-lg">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
            </svg>
            <span>File a Report Anyway</span>
          </a>
          <button type="button" class="btn btn-outline btn-lg" id="quiz-btn-retake">
            <span>🔄 Retake Quiz</span>
          </button>
        </div>
      `;
    } else {
      // 1+ YES ANSWERS
      resultBadge.className = 'badge badge-critical';
      resultBadge.textContent = '🚨 Reportable Cyber Offense Detected';
      resultHeading.textContent = 'Based on your answers, this may be a reportable cybercrime incident.';
      resultDesc.textContent = `You flagged ${yesCount} critical risk indicator${yesCount > 1 ? 's' : ''}. Prompt reporting within the initial Golden Hour significantly maximizes recovery chances and legal protection.`;

      let categoriesHtml = `
        <div style="font-size: 0.88rem; font-weight: 700; color: var(--text-main); margin-bottom: 0.75rem; text-transform: uppercase; letter-spacing: 0.5px;">
          Likely Applicable Threat Categories:
        </div>
        <div class="grid grid-2 gap-3" style="margin-bottom: 1.25rem;">
      `;

      matchedCategories.forEach(cat => {
        categoriesHtml += `
          <div class="card" style="padding: 0.85rem 1rem; display: flex; align-items: flex-start; gap: 0.75rem; background: var(--bg-surface); border: 1px solid var(--border-subtle); border-left: 3px solid var(--primary); text-align: left;">
            <span style="font-size: 1.4rem; flex-shrink: 0; line-height: 1;">${cat.icon}</span>
            <div>
              <div style="font-weight: 700; font-size: 0.92rem; color: var(--text-main);">${cat.title}</div>
              <div style="font-size: 0.8rem; color: var(--text-muted); margin-top: 0.2rem; line-height: 1.35;">${cat.desc}</div>
            </div>
          </div>
        `;
      });

      categoriesHtml += `</div>`;
      resultCategoriesContainer.innerHTML = categoriesHtml;

      resultActionsContainer.innerHTML = `
        <div class="flex items-center justify-center gap-3 flex-wrap" style="margin-top: 1.5rem;">
          <a href="${reportUrl}" class="btn btn-primary btn-lg" style="box-shadow: 0 0 20px rgba(59, 130, 246, 0.4);">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
            </svg>
            <span>File a Complaint Now &rarr;</span>
          </a>
          <a href="${chatbotUrl}" class="btn btn-ai btn-lg">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
            </svg>
            <span>Ask AI Assistant</span>
          </a>
          <button type="button" class="btn btn-outline btn-lg" id="quiz-btn-retake">
            <span>🔄 Retake Quiz</span>
          </button>
        </div>
      `;
    }

    const retakeBtn = document.getElementById('quiz-btn-retake');
    if (retakeBtn) {
      retakeBtn.addEventListener('click', restartQuiz);
    }
  }

});
