/**
 * ZeroGuard AI - Animated Running Text Background
 * Continuous scrolling hacker terminal text wallpaper.
 */
(function () {
  'use strict';

  // =========================================================================
  // 1. PHRASE LIST (Edit phrases here)
  // =========================================================================
  const PHRASES = [
    "Report it. Preserve the evidence. Protect yourself.",
    "Never share your OTP with anyone.",
    "Dial 1930 within the golden hour.",
    "Fake links steal UPI credentials.",
    "Screenshots are evidence - do not delete them.",
    "Block the number. Save the chat. File the complaint.",
    "Banks will never ask for your PIN.",
    "Deepfake blackmail is a crime - you are not alone.",
    "Verify before you pay.",
    "Every report helps stop the next scam.",
    "Investment groups promising double returns are fraud.",
    "Evidence sealed with SHA-256.",
    "Check the sender. Check the link. Check twice."
  ];

  // =========================================================================
  // 2. CONFIGURATION (Edit speed range, font sizes, row counts, and colors here)
  // =========================================================================
  const CONFIG = {
    // Speed range per row (in seconds per full loop)
    minSpeed: 40,
    maxSpeed: 120,

    // Font size range (in pixels)
    minFontSize: 13,
    maxFontSize: 26,

    // Row density
    desktopRows: 35,
    mobileRows: 15,

    // Color palette with matching opacities
    colors: [
      { color: '#78ff96', opacity: 0.65 }, // Bright matrix green
      { color: '#28d25a', opacity: 0.45 }, // Medium cyber green
      { color: '#148c3c', opacity: 0.30 }, // Dim background green
      { color: '#10b981', opacity: 0.40 }  // Emerald accent
    ],

    // Font family variety
    fonts: [
      "'Courier New', Courier, monospace",
      "'Inter', system-ui, -apple-system, sans-serif",
      "Consolas, 'Liberation Mono', Menlo, monospace",
      "'Outfit', sans-serif",
      "ui-monospace, SFMono-Regular, monospace"
    ]
  };

  function getRandomInt(min, max) {
    return Math.floor(Math.random() * (max - min + 1)) + min;
  }

  function getRandomItem(arr) {
    return arr[Math.floor(Math.random() * arr.length)];
  }

  function initRunningTextBg() {
    if (document.getElementById('runningTextBgContainer')) return;

    // Create container
    const container = document.createElement('div');
    container.id = 'runningTextBgContainer';
    container.className = 'running-text-bg-container';
    container.setAttribute('aria-hidden', 'true');

    const wrapper = document.createElement('div');
    wrapper.className = 'running-text-bg-wrapper';

    const isMobile = window.innerWidth < 768;
    const rowCount = isMobile ? CONFIG.mobileRows : CONFIG.desktopRows;

    for (let i = 0; i < rowCount; i++) {
      const row = document.createElement('div');
      const isMoveLeft = i % 2 === 0;
      row.className = `running-text-row ${isMoveLeft ? 'move-left' : 'move-right'}`;

      const speed = getRandomInt(CONFIG.minSpeed, CONFIG.maxSpeed);
      row.style.setProperty('--row-duration', `${speed}s`);

      const fontSize = getRandomInt(CONFIG.minFontSize, CONFIG.maxFontSize);
      const font = getRandomItem(CONFIG.fonts);
      const colorScheme = getRandomItem(CONFIG.colors);

      row.style.fontSize = `${fontSize}px`;
      row.style.fontFamily = font;
      row.style.color = colorScheme.color;
      row.style.opacity = colorScheme.opacity;

      // Construct phrase chain
      let rowText = '';
      const phraseRepeats = 8;
      for (let p = 0; p < phraseRepeats; p++) {
        const phrase = PHRASES[(i * 3 + p) % PHRASES.length];
        rowText += phrase + '    •    ';
      }

      // Two identical track spans for continuous 0% -> -50% translateX looping
      const trackA = document.createElement('span');
      trackA.className = 'running-text-track';
      trackA.textContent = rowText;

      const trackB = document.createElement('span');
      trackB.className = 'running-text-track';
      trackB.textContent = rowText;

      row.appendChild(trackA);
      row.appendChild(trackB);
      wrapper.appendChild(row);
    }

    container.appendChild(wrapper);

    // Overlay element
    const overlay = document.createElement('div');
    overlay.className = 'running-text-overlay';

    document.body.prepend(overlay);
    document.body.prepend(container);

    // Stop / pause animations when tab is hidden to save GPU & battery
    document.addEventListener('visibilitychange', () => {
      if (document.hidden) {
        container.classList.add('paused');
      } else {
        container.classList.remove('paused');
      }
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initRunningTextBg);
  } else {
    initRunningTextBg();
  }
})();
