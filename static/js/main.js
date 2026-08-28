document.addEventListener('DOMContentLoaded', () => {
  // --- Navbar Scroll Effect ---
  const navbar = document.querySelector('.navbar');
  window.addEventListener('scroll', () => {
    if (window.scrollY > 50) {
      navbar.classList.add('scrolled');
    } else {
      navbar.classList.remove('scrolled');
    }
  });

  // --- Mobile Menu Toggle ---
  const hamburger = document.querySelector('.hamburger');
  const mobileMenu = document.querySelector('.mobile-menu');

  if (hamburger && mobileMenu) {
    hamburger.addEventListener('click', () => {
      mobileMenu.classList.toggle('open');
      // Simple hamburger icon animation
      const spans = hamburger.querySelectorAll('span');
      spans[0].style.transform = mobileMenu.classList.contains('open') ? 'rotate(45deg) translate(5px, 5px)' : 'none';
      spans[1].style.opacity = mobileMenu.classList.contains('open') ? '0' : '1';
      spans[2].style.transform = mobileMenu.classList.contains('open') ? 'rotate(-45deg) translate(6px, -6px)' : 'none';
    });
  }

  // --- Back to Top Button ---
  const backToTopBtn = document.getElementById('backToTop');
  window.addEventListener('scroll', () => {
    if (window.scrollY > 500) {
      backToTopBtn.classList.add('visible');
    } else {
      backToTopBtn.classList.remove('visible');
    }
  });

  if (backToTopBtn) {
    backToTopBtn.addEventListener('click', () => {
      window.scrollTo({ top: 0, behavior: 'smooth' });
    });
  }

  // --- Category Search Filter ---
  const searchInput = document.getElementById('categorySearch');
  const categoryCards = document.querySelectorAll('.category-card');

  if (searchInput) {
    searchInput.addEventListener('input', (e) => {
      const term = e.target.value.toLowerCase().trim();
      categoryCards.forEach(card => {
        const name = card.querySelector('.cat-name').textContent.toLowerCase();
        if (name.includes(term)) {
          card.style.display = 'block';
        } else {
          card.style.display = 'none';
        }
      });
    });
  }

  // --- Counter Up Animation for Stats ---
  const statNumbers = document.querySelectorAll('.stat-number');
  const animateStats = () => {
    statNumbers.forEach(stat => {
      const target = parseInt(stat.getAttribute('data-target'), 10);
      let count = 0;
      const speed = target / 50; // speed of counting

      const updateCount = () => {
        count += Math.ceil(speed);
        if (count >= target) {
          stat.textContent = target.toLocaleString() + (stat.textContent.includes('%') ? '%' : '+');
        } else {
          stat.textContent = count.toLocaleString() + (stat.textContent.includes('%') ? '%' : '+');
          setTimeout(updateCount, 30);
        }
      };
      updateCount();
    });
  };

  // Trigger stats animation when visible in viewport
  const statsSection = document.querySelector('.stats-section');
  if (statsSection) {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          animateStats();
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.5 });
    observer.observe(statsSection);
  }

  // --- Interactive Cyber Safety Steps Data ---
  const flowSteps = {
    1: {
      badge: '🎣 Phishing Checklist',
      title: 'Verify Links & Senders',
      desc: '1. Never share banking passwords or credit card PIN numbers on unsolicited links.<br>2. Check for matching domain addresses carefully.<br>3. Report domain to cyber authorities immediately.',
      status: 'Emergency Helpline: Call 1930'
    },
    2: {
      badge: '💸 UPI Fraud Checklist',
      title: 'Block Unauthorized Request PINs',
      desc: '1. Never enter your UPI PIN to receive money.<br>2. Block and report transaction collection requests immediately.<br>3. Report fraud ref to your banking UPI support desk.',
      status: 'Emergency Helpline: Call 1930'
    },
    3: {
      badge: '🏦 Banking Fraud Checklist',
      title: 'Secure Accounts Immediately',
      desc: '1. Contact bank branch to block account & card instantly.<br>2. Write down transaction reference IDs.<br>3. Report the fraud incident within 3 days for zero liability.',
      status: 'Emergency Helpline: Call 1930'
    },
    4: {
      badge: '🔓 Account Recovery Checklist',
      title: 'Social Media Hacking Rules',
      desc: '1. Turn on Two-Factor Authentication (2FA) immediately.<br>2. Terminate all other active device login sessions.<br>3. Revoke unknown apps with access permissions.',
      status: 'Emergency Helpline: Call 1930'
    },
    5: {
      badge: '🦠 Malware/Ransomware Rules',
      title: 'Isolate Impacted Devices',
      desc: '1. Disconnect system from internet/WiFi instantly.<br>2. Never pay ransom demands (it funds criminals).<br>3. Use offline backups to restore system states.',
      status: 'Emergency Helpline: Call 1930'
    },
    6: {
      badge: '👤 Identity Theft Protection',
      title: 'Monitor Stolen Identity Files',
      desc: '1. Change passwords of linked recovery accounts.<br>2. Alert major credit bureaus to enable credit freezes.<br>3. Track card statements for unknown charges.',
      status: 'Emergency Helpline: Call 1930'
    }
  };

  const flowNodes = document.querySelectorAll('.flow-node');
  const previewBox = document.getElementById('flowPreviewBox');

  if (flowNodes.length > 0 && previewBox) {
    flowNodes.forEach(node => {
      node.addEventListener('click', () => {
        // Remove active class from other nodes
        flowNodes.forEach(n => n.classList.remove('active'));
        
        // Add active class to clicked node
        node.classList.add('active');
        
        // Update content
        const stepId = node.getAttribute('data-step');
        const data = flowSteps[stepId];
        
        if (data) {
          previewBox.innerHTML = `
            <div class="preview-phase-badge animate-scale-in">${data.badge}</div>
            <h4 class="preview-phase-title animate-scale-in" style="animation-delay: 0.05s">${data.title}</h4>
            <p class="preview-phase-desc animate-scale-in" style="animation-delay: 0.1s">${data.desc}</p>
            <div class="preview-mock-action animate-scale-in" style="animation-delay: 0.15s">
              <div class="mock-status-row">
                <span class="mock-dot-active"></span>
                <span class="mock-status-text">${data.status}</span>
              </div>
            </div>
          `;
        }
      });
    });

    // Auto rotate flow timeline steps every 4.5 seconds
    let currentStepIndex = 1;
    const autoRotate = setInterval(() => {
      currentStepIndex = (currentStepIndex % 6) + 1;
      const targetNode = document.querySelector(`.flow-node[data-step="${currentStepIndex}"]`);
      if (targetNode) {
        // Remove other actives and apply active class manually to prevent loop triggers if user clicked
        flowNodes.forEach(n => n.classList.remove('active'));
        targetNode.classList.add('active');
        const data = flowSteps[currentStepIndex];
        if (data) {
          previewBox.innerHTML = `
            <div class="preview-phase-badge animate-scale-in">${data.badge}</div>
            <h4 class="preview-phase-title animate-scale-in">${data.title}</h4>
            <p class="preview-phase-desc animate-scale-in">${data.desc}</p>
            <div class="preview-mock-action animate-scale-in">
              <div class="mock-status-row">
                <span class="mock-dot-active"></span>
                <span class="mock-status-text">${data.status}</span>
              </div>
            </div>
          `;
        }
      }
    }, 4500);

    // Stop auto rotation if user clicks a node manually
    flowNodes.forEach(node => {
      node.addEventListener('mousedown', () => {
        clearInterval(autoRotate);
      });
    });
  }

  // --- FAQ Accordion Toggle ---
  const faqHeaders = document.querySelectorAll('.faq-header');
  faqHeaders.forEach(header => {
    header.addEventListener('click', () => {
      const item = header.parentElement;
      const body = item.querySelector('.faq-body');
      const isActive = item.classList.contains('active');
      
      // Close other active items
      document.querySelectorAll('.faq-item.active').forEach(activeItem => {
        if (activeItem !== item) {
          activeItem.classList.remove('active');
          activeItem.querySelector('.faq-body').style.maxHeight = '0';
        }
      });
      
      // Toggle current item
      if (isActive) {
        item.classList.remove('active');
        body.style.maxHeight = '0';
      } else {
        item.classList.add('active');
        body.style.maxHeight = body.scrollHeight + 'px';
      }
    });
  });
});
