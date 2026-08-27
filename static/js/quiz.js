// Interactive Cybersecurity Awareness Quiz Engine
const QUIZ_QUESTIONS = [
  {
    id: 1,
    title: "Scenario 1: Urgent Banking SMS",
    type: "SMS Phishing",
    message: "SMS from AD-SBIBNK: 'Dear Customer, your SBI Netbanking account is suspended today due to non-updated PAN Card. Click http://sbi-kyc-verify.online immediately to avoid permanent deactivation.'",
    isScam: true,
    explanation: "🚨 <strong>THIS IS A PHISHING SCAM!</strong> Banks never send SMS links ending in unofficial domains (.online, .site, .biz) demanding urgent PAN or credential verification. Official bank domains always end in official institutional addresses like <code>onlinesbi.sbi</code>.",
    tip: "Never click links in SMS regarding KYC/PAN updates. Always log in directly via the official bank app."
  },
  {
    id: 2,
    title: "Scenario 2: OLX QR Code Payment",
    type: "UPI Fraud",
    message: "A buyer on OLX agrees to purchase your old sofa and sends a QR code: 'I have sent an advance payment of Rs 8,000. Please scan this QR code and enter your UPI PIN to receive the money.'",
    isScam: true,
    explanation: "🚨 <strong>THIS IS A UPI SCAM!</strong> Entering your UPI PIN will ALWAYS DEBIT money from your bank account. You NEVER need to enter a UPI PIN or scan a QR code to receive money.",
    tip: "Remember: UPI PIN is ONLY for transferring money out, never for receiving money."
  },
  {
    id: 3,
    title: "Scenario 3: Part-Time Telegram Task Job",
    type: "Job / Task Scam",
    message: "A recruiter on Telegram messages: 'Earn Rs 2,500 to Rs 5,000 daily by simply rating 10 YouTube videos. Deposit Rs 500 first to activate VIP Merchant tier.'",
    isScam: true,
    explanation: "🚨 <strong>THIS IS A PREPAID TASK SCAM!</strong> Fraud syndicates pay small initial rewards to lure you into depositing larger amounts (Rs 20k to 1 Lakh+) for fake VIP levels before blocking withdrawals.",
    tip: "Legitimate employment NEVER requires upfront deposit fees to work."
  },
  {
    id: 4,
    title: "Scenario 4: Customer Care Remote Help",
    type: "Remote Access Scam",
    message: "You searched 'Food Delivery Refund Helpline' on Google and called the top number. The support agent tells you: 'Download AnyDesk or RustDesk from the Play Store and share the 9-digit code so we can process your refund.'",
    isScam: true,
    explanation: "🚨 <strong>THIS IS A DANGEROUS REMOTE ACCESS SCAM!</strong> Fraudsters buy Google sponsored ads to place fake helpline numbers at the top of search results. Sharing a remote desktop code grants full access to view OTPs and drain bank accounts.",
    tip: "Official customer support teams NEVER ask customers to install AnyDesk or TeamViewer."
  },
  {
    id: 5,
    title: "Scenario 5: WhatsApp Video Call Threat",
    type: "Sextortion Trap",
    message: "An unknown number initiates a WhatsApp video call. An explicit video is displayed for a few seconds before disconnecting. Minutes later, you receive a morphed recording with threats to send it to all your contacts unless Rs 50,000 is transferred immediately.",
    isScam: true,
    explanation: "🚨 <strong>THIS IS A SEXTORTION EXTORTION SCHEME!</strong> Paying will not stop extortionists. Preserve evidence, do not transfer any funds, lock your social profiles, use StopNCII.org, and file a complaint immediately.",
    tip: "Never transfer money to blackmailers. Report to Cyber-Cell and helpline 1930 immediately."
  },
  {
    id: 6,
    title: "Scenario 6: Email Attachment from Colleague",
    type: "Malware / Ransomware",
    message: "You receive an unexpected email claiming to be an urgent company bonus announcement with an attached file named <code>Annual_Bonus_List_2026.pdf.exe</code>.",
    isScam: true,
    explanation: "🚨 <strong>THIS IS A MALWARE EXECUTABLE!</strong> Files with double extensions (like <code>.pdf.exe</code>) disguise malicious executable programs that infect devices with ransomware.",
    tip: "Always check file extensions. Never execute <code>.exe</code>, <code>.scr</code>, or <code>.bat</code> files received in emails."
  }
];

document.addEventListener('DOMContentLoaded', () => {
  const quizContainer = document.getElementById('quiz-questions-container');
  const scoreCard = document.getElementById('quiz-score-card');
  const scoreNum = document.getElementById('score-number');
  const scoreBadge = document.getElementById('score-badge');
  const resetBtn = document.getElementById('reset-quiz-btn');

  let userAnswers = {};

  function renderQuiz() {
    if (!quizContainer) return;
    quizContainer.innerHTML = '';
    userAnswers = {};
    if (scoreCard) scoreCard.style.display = 'none';

    QUIZ_QUESTIONS.forEach((q, idx) => {
      const card = document.createElement('div');
      card.className = 'card animate-fade-in';
      card.style.marginBottom = '1.5rem';
      card.id = `quiz-card-${q.id}`;

      card.innerHTML = `
        <div class="flex justify-between items-center flex-wrap gap-2" style="margin-bottom: 0.75rem;">
          <h3 style="font-size: 1.1rem; margin: 0;">${q.title}</h3>
          <span class="badge badge-medium">${q.type}</span>
        </div>

        <div style="background: var(--bg-surface-subtle); border-left: 4px solid var(--primary); padding: 1rem; border-radius: var(--radius-sm); font-size: 0.95rem; margin-bottom: 1.25rem; font-style: italic;">
          "${q.message}"
        </div>

        <div style="font-weight: 600; font-size: 0.9rem; margin-bottom: 0.75rem;">
          Is this message a FRAUD / SCAM or LEGITIMATE?
        </div>

        <div class="flex gap-3" id="quiz-actions-${q.id}">
          <button type="button" class="btn btn-danger" style="flex: 1;" onclick="handleAnswer(${q.id}, true)">
            🚨 Flag as SCAM / FRAUD
          </button>
          <button type="button" class="btn btn-outline" style="flex: 1;" onclick="handleAnswer(${q.id}, false)">
            ✓ Looks Legitimate / Safe
          </button>
        </div>

        <div id="quiz-feedback-${q.id}" style="display: none; margin-top: 1.25rem; padding: 1rem; border-radius: var(--radius-md); font-size: 0.9rem; line-height: 1.5;"></div>
      `;

      quizContainer.appendChild(card);
    });
  }

  window.handleAnswer = function(questionId, selectedScam) {
    const q = QUIZ_QUESTIONS.find(item => item.id === questionId);
    if (!q) return;

    userAnswers[questionId] = (selectedScam === q.isScam);
    const feedbackBox = document.getElementById(`quiz-feedback-${questionId}`);
    const actionsBox = document.getElementById(`quiz-actions-${questionId}`);

    if (actionsBox) {
      actionsBox.style.pointerEvents = 'none';
      actionsBox.style.opacity = '0.7';
    }

    if (feedbackBox) {
      feedbackBox.style.display = 'block';
      const isCorrect = userAnswers[questionId];

      if (isCorrect) {
        feedbackBox.style.background = 'var(--accent-green-light)';
        feedbackBox.style.border = '1px solid var(--accent-green)';
        feedbackBox.style.color = 'var(--accent-green)';
        feedbackBox.innerHTML = `
          <div style="font-weight: 700; margin-bottom: 0.35rem;">✓ Correct! You spotted the threat.</div>
          <div style="color: var(--text-main); font-size: 0.88rem;">${q.explanation}</div>
          <div style="margin-top: 0.5rem; font-size: 0.82rem; font-weight: 600;">💡 Cyber Safety Rule: ${q.tip}</div>
        `;
      } else {
        feedbackBox.style.background = 'var(--danger-light)';
        feedbackBox.style.border = '1px solid var(--danger)';
        feedbackBox.style.color = 'var(--danger)';
        feedbackBox.innerHTML = `
          <div style="font-weight: 700; margin-bottom: 0.35rem;">✗ Watch out! This is a dangerous trap.</div>
          <div style="color: var(--text-main); font-size: 0.88rem;">${q.explanation}</div>
          <div style="margin-top: 0.5rem; font-size: 0.82rem; font-weight: 600;">💡 Cyber Safety Rule: ${q.tip}</div>
        `;
      }
    }

    // Check if all answered
    if (Object.keys(userAnswers).length === QUIZ_QUESTIONS.length) {
      calculateScore();
    }
  };

  function calculateScore() {
    let correctCount = 0;
    Object.values(userAnswers).forEach(val => {
      if (val) correctCount++;
    });

    if (scoreCard && scoreNum && scoreBadge) {
      scoreCard.style.display = 'block';
      scoreNum.textContent = `${correctCount} / ${QUIZ_QUESTIONS.length}`;

      if (correctCount === QUIZ_QUESTIONS.length) {
        scoreBadge.textContent = '🛡️ Cyber Vigilant Sentinel (Top 1% Score)';
        scoreBadge.className = 'badge badge-success';
      } else if (correctCount >= 4) {
        scoreBadge.textContent = '🔍 Cyber Aware Citizen (Good Threat Perception)';
        scoreBadge.className = 'badge badge-medium';
      } else {
        scoreBadge.textContent = '⚠️ High Vulnerability Risk (Review Prevention Guides)';
        scoreBadge.className = 'badge badge-critical';
      }

      scoreCard.scrollIntoView({ behavior: 'smooth' });
    }
  }

  if (resetBtn) {
    resetBtn.addEventListener('click', renderQuiz);
  }

  renderQuiz();
});
