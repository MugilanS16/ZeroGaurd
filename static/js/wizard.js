// ZeroGuard AI Wizard Interactive Engine
document.addEventListener('DOMContentLoaded', () => {
  
  // -------------------------------------------------------------
  // 1. Debounced Real-Time AI Quick-Classification (Step 1)
  // -------------------------------------------------------------
  const descInput = document.getElementById('raw_description');
  const liveTriagePanel = document.getElementById('live-triage-panel');
  const liveCategoryBadge = document.getElementById('live-category-badge');
  const liveRiskBadge = document.getElementById('live-risk-badge');
  const liveConfidenceText = document.getElementById('live-confidence-text');
  const liveSummaryText = document.getElementById('live-summary-text');
  
  let debounceTimer = null;

  if (descInput && liveTriagePanel) {
    descInput.addEventListener('input', () => {
      clearTimeout(debounceTimer);
      const text = descInput.value.trim();

      if (text.length < 15) {
        liveCategoryBadge.textContent = 'Awaiting Details...';
        liveRiskBadge.textContent = 'Pending';
        liveRiskBadge.className = 'badge badge-low';
        liveConfidenceText.textContent = '';
        liveSummaryText.textContent = 'Type at least 15 characters to trigger instant AI classification.';
        return;
      }

      liveSummaryText.textContent = 'Analyzing threat patterns & risk indicators...';

      debounceTimer = setTimeout(() => {
        fetch('/api/ai-quick-classify', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ text: text })
        })
        .then(res => res.json())
        .then(data => {
          if (data && data.crime_type) {
            liveCategoryBadge.textContent = data.crime_type;
            liveRiskBadge.textContent = data.risk_level + ' Risk (' + data.risk_score + '/100)';
            
            // Risk Badge classes
            liveRiskBadge.className = 'badge ' + (
              data.risk_level === 'Critical' ? 'badge-critical' :
              data.risk_level === 'High' ? 'badge-high' :
              data.risk_level === 'Medium' ? 'badge-medium' : 'badge-low'
            );

            if (data.confidence) {
              liveConfidenceText.textContent = Math.round(data.confidence * 100) + '% Match';
            }
            liveSummaryText.textContent = data.summary || 'Offense pattern analyzed.';
          }
        })
        .catch(err => {
          console.warn('Live triage error:', err);
        });
      }, 550);
    });
  }

  // -------------------------------------------------------------
  // 2. Real-Time AI Polish & Formalization (Step 1)
  // -------------------------------------------------------------
  const polishBtn = document.getElementById('btn-ai-polish');
  const formalDescInput = document.getElementById('formal_description');
  const polishFeedback = document.getElementById('ai-polish-feedback');
  const langSelect = document.getElementById('language-select');

  if (polishBtn && descInput) {
    let originalRawText = '';

    polishBtn.addEventListener('click', () => {
      const text = descInput.value.trim();
      if (text.length < 15) {
        alert('Please write at least a few sentences describing the incident first.');
        return;
      }

      originalRawText = text;
      polishBtn.disabled = true;
      polishBtn.innerHTML = `
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="spin" style="animation: rotate 1s linear infinite;">
          <line x1="12" y1="2" x2="12" y2="6"></line><line x1="12" y1="18" x2="12" y2="22"></line>
        </svg>
        <span>Polishing with AI...</span>
      `;

      const selectedLang = langSelect ? langSelect.value : 'en';

      fetch('/api/ai-enhance-report', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: text, language: selectedLang })
      })
      .then(res => res.json())
      .then(data => {
        polishBtn.disabled = false;
        polishBtn.innerHTML = `
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="20 6 9 17 4 12"></polyline>
          </svg>
          <span>Polished & Structured!</span>
        `;

        if (data.formal_description) {
          if (formalDescInput) {
            formalDescInput.value = data.formal_description;
          } else {
            descInput.value = data.formal_description;
          }

          if (polishFeedback) {
            polishFeedback.style.display = 'block';
            polishFeedback.innerHTML = `
              <div style="font-size: 0.85rem; color: var(--accent-green); margin-top: 0.5rem;">
                ✓ Formatted into formal legal complaint draft.
                ${data.key_facts ? '<strong>Key Facts Identified:</strong> ' + data.key_facts.join(' • ') : ''}
              </div>
            `;
          }
        }
      })
      .catch(err => {
        polishBtn.disabled = false;
        polishBtn.innerHTML = `<span>Polish with AI</span>`;
        alert('AI service currently busy. Using your original text.');
      });
    });
  }

  // -------------------------------------------------------------
  // 3. Multi-File Evidence Uploader with Previews & Labels (Step 3)
  // -------------------------------------------------------------
  const dropzone = document.getElementById('evidence-dropzone');
  const fileInput = document.getElementById('evidence-file-input');
  const previewList = document.getElementById('file-preview-list');

  if (dropzone && fileInput && previewList) {
    dropzone.addEventListener('click', () => fileInput.click());

    dropzone.addEventListener('dragover', (e) => {
      e.preventDefault();
      dropzone.classList.add('dragover');
    });

    dropzone.addEventListener('dragleave', () => {
      dropzone.classList.remove('dragover');
    });

    dropzone.addEventListener('drop', (e) => {
      e.preventDefault();
      dropzone.classList.remove('dragover');
      if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
        fileInput.files = e.dataTransfer.files;
        renderFilePreviews(fileInput.files);
      }
    });

    fileInput.addEventListener('change', () => {
      renderFilePreviews(fileInput.files);
    });

    function renderFilePreviews(files) {
      previewList.innerHTML = '';
      if (!files || files.length === 0) return;

      Array.from(files).forEach((file, idx) => {
        const item = document.createElement('div');
        item.className = 'file-preview-item animate-fade-in';

        const isImage = file.type.startsWith('image/');
        const sizeKb = Math.round(file.size / 1024);
        const sizeText = sizeKb > 1024 ? (sizeKb / 1024).toFixed(1) + ' MB' : sizeKb + ' KB';

        let thumbHtml = isImage 
          ? `<img src="${URL.createObjectURL(file)}" class="file-thumb" alt="Preview">`
          : `<div class="file-thumb" style="display:flex;align-items:center;justify-content:center;font-weight:bold;color:var(--primary);font-size:0.75rem;">FILE</div>`;

        item.innerHTML = `
          <div style="display: flex; align-items: center; gap: 0.75rem; overflow: hidden; flex: 1;">
            ${thumbHtml}
            <div style="overflow: hidden;">
              <div style="font-weight: 600; font-size: 0.88rem; text-overflow: ellipsis; white-space: nowrap; overflow: hidden;" title="${file.name}">
                ${file.name}
              </div>
              <div style="font-size: 0.78rem; color: var(--text-muted);">${sizeText} &bull; Validated</div>
            </div>
          </div>

          <div style="display: flex; align-items: center; gap: 0.5rem;">
            <select name="evidence_categories" class="form-control" style="font-size: 0.82rem; padding: 0.35rem 0.6rem; width: auto;">
              <option value="Screenshot" ${file.name.toLowerCase().includes('screen') ? 'selected' : ''}>Screenshot</option>
              <option value="Bank Statement" ${file.name.toLowerCase().includes('bank') || file.name.toLowerCase().includes('passbook') ? 'selected' : ''}>Bank Statement</option>
              <option value="Call Recording" ${file.type.startsWith('audio') ? 'selected' : ''}>Call Recording</option>
              <option value="Document" ${file.name.endsWith('.pdf') ? 'selected' : ''}>Document</option>
              <option value="Chat Log">Chat Log</option>
            </select>
          </div>
        `;

        previewList.appendChild(item);
      });
    }
  }

});
