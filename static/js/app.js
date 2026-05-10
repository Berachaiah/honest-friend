// The Honest Friend — Frontend JS

// Global persona state
let CURRENT_REVIEWS = [];
let CURRENT_PERSONA = null;

// ── Typing animation utility ──
async function typeText(element, text, speed = 18) {
  element.classList.add('typing-cursor');
  let i = 0;
  return new Promise(resolve => {
    const interval = setInterval(() => {
      element.textContent += text[i];
      i++;
      if (i >= text.length) {
        clearInterval(interval);
        element.classList.remove('typing-cursor');
        resolve();
      }
    }, speed);
  });
}

async function typeHTML(containerId, html, delay = 0) {
  await new Promise(r => setTimeout(r, delay));
  const el = document.getElementById(containerId);
  if (el) el.innerHTML = html;
}

// ── Parse review input ──
function parseReviewInput(raw) {
  const lines = raw.trim().split('\n').filter(l => l.trim());
  return lines.map(line => {
    const parts = line.split('|');
    if (parts.length >= 2) {
      const stars = parseInt(parts[0].trim()) || 3;
      const text = parts.slice(1).join('|').trim();
      return { stars, text, user_id: 'user' };
    }
    return { stars: 3, text: line.trim(), user_id: 'user' };
  });
}

// ── Build persona card HTML ──
function buildPersonaCardHTML(pd, reasoning) {
  const ratingStyles = { generous: '🟢 Generous', balanced: '🟡 Balanced', critical: '🔴 Critical' };
  const verbosityStyles = { brief: '✏️ Brief', moderate: '📝 Moderate', detailed: '📖 Detailed' };
  const sentimentIcons = { positive: '😊', neutral: '😐', negative: '😤' };
  const priceIcons = { high: '💰💰💰', medium: '💰💰', low: '💰' };

  const priceMeterWidth = pd.price_sensitivity === 'high' ? 90 : pd.price_sensitivity === 'medium' ? 55 : 20;
  const ratingMeterWidth = Math.round((pd.avg_rating / 5) * 100);
  const verbosityMeterWidth = pd.verbosity === 'detailed' ? 90 : pd.verbosity === 'moderate' ? 55 : 20;

  const categoriesHTML = pd.top_categories.length > 0
    ? pd.top_categories.map(c => `<span class="persona-tag">${c}</span>`).join('')
    : '<span class="persona-tag">Varied</span>';

  return `
    <div class="persona-card-header">
      <span>🧠</span>
      <h4>Your Behavioural Persona — Built from ${pd.review_count} Reviews</h4>
    </div>
    <div class="persona-card-body">
      <div class="persona-stat">
        <span class="persona-stat-label">Rating Style</span>
        <span class="persona-stat-value">${ratingStyles[pd.rating_style] || pd.rating_style}</span>
        <div class="persona-meter">
          <div class="persona-meter-fill meter-green" style="width:${ratingMeterWidth}%"></div>
        </div>
        <span style="font-size:0.78rem;color:var(--grey)">Avg ${pd.avg_rating}/5.0 · Std ${pd.rating_std}</span>
      </div>

      <div class="persona-stat">
        <span class="persona-stat-label">Price Sensitivity</span>
        <span class="persona-stat-value">${priceIcons[pd.price_sensitivity]} ${pd.price_sensitivity.charAt(0).toUpperCase() + pd.price_sensitivity.slice(1)}</span>
        <div class="persona-meter">
          <div class="persona-meter-fill meter-gold" style="width:${priceMeterWidth}%"></div>
        </div>
      </div>

      <div class="persona-stat">
        <span class="persona-stat-label">Writing Style</span>
        <span class="persona-stat-value">${verbosityStyles[pd.verbosity] || pd.verbosity}</span>
        <div class="persona-meter">
          <div class="persona-meter-fill meter-navy" style="width:${verbosityMeterWidth}%"></div>
        </div>
      </div>

      <div class="persona-stat">
        <span class="persona-stat-label">Emotional Tone</span>
        <span class="persona-stat-value">${sentimentIcons[pd.sentiment_bias] || ''} ${pd.sentiment_bias.charAt(0).toUpperCase() + pd.sentiment_bias.slice(1)}</span>
        <span style="font-size:0.78rem;color:var(--grey)">${pd.consistency} rater</span>
      </div>

      <div class="persona-stat" style="grid-column: 1 / -1">
        <span class="persona-stat-label">Frequently Reviews</span>
        <div style="margin-top:4px">${categoriesHTML}</div>
      </div>
    </div>
    <div class="persona-card-footer">
      🤖 Agent summary: "${reasoning || 'Persona extracted. Both tasks below will use this profile.'}"
    </div>
  `;
}

// ── STEP 1: Build persona ──
async function buildPersona() {
  const raw = document.getElementById('userReviewsInput').value;
  const personaCard = document.getElementById('personaCard');

  if (!raw.trim()) { alert('Please enter at least one review.'); return; }

  CURRENT_REVIEWS = parseReviewInput(raw);
  personaCard.className = 'persona-card';
  personaCard.innerHTML = `
    <div class="persona-card-header">
      <span>⏳</span>
      <h4>Analysing ${CURRENT_REVIEWS.length} reviews...</h4>
    </div>
  `;

  try {
    const res = await fetch('/api/task-b/recommend/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        reviews: CURRENT_REVIEWS,
        context: { mood: 'building persona', budget: 'any', location: 'any' }
      })
    });
    const data = await res.json();

    if (data.persona_display) {
      CURRENT_PERSONA = data.persona_display;
      personaCard.innerHTML = buildPersonaCardHTML(
        data.persona_display,
        data.result?.reasoning_chain
      );
    } else {
      personaCard.innerHTML = `
        <div class="persona-card-header">
          <span>✅</span>
          <h4>Persona Ready — ${CURRENT_REVIEWS.length} reviews loaded</h4>
        </div>
      `;
    }
  } catch (e) {
    personaCard.innerHTML = `
      <div class="persona-card-header">
        <span>✅</span>
        <h4>Persona Ready — ${CURRENT_REVIEWS.length} reviews loaded</h4>
      </div>
    `;
  }
}

// ── TASK A: Review Generation with typing + confidence retry ──
async function submitReviewRequest() {
  const name = document.getElementById('productName').value.trim();
  const category = document.getElementById('productCategory').value.trim();
  const desc = document.getElementById('productDesc').value.trim();
  const price = document.getElementById('productPrice').value.trim();
  const resultBox = document.getElementById('reviewResult');

  if (!name) { alert('Please enter a product name.'); return; }

  const reviews = CURRENT_REVIEWS.length > 0 ? CURRENT_REVIEWS : getDemoReviews();

  resultBox.className = 'result-box';
  resultBox.innerHTML = '<p class="loading">⏳ Analysing your persona and generating review...</p>';

  try {
    const res = await fetch('/api/task-a/generate/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        reviews,
        product: { name, category, description: desc, avg_price: price }
      })
    });
    const data = await res.json();

    if (data.success) {
      let r = data.result;
      let retryNotice = '';

      // Confidence retry — if score below threshold, retry once
      if (r.confidence && !r.confidence.passed) {
        resultBox.innerHTML = '<p class="loading">⚠️ First attempt below quality threshold — regenerating with refined instructions...</p>';

        const retryRes = await fetch('/api/task-a/generate/', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            reviews,
            product: { name, category, description: desc, avg_price: price },
            retry: true
          })
        });
        const retryData = await retryRes.json();
        if (retryData.success) {
          r = retryData.result;
          retryNotice = `<div class="retry-notice">🔄 Agent self-evaluated and regenerated this review for higher quality. Flags: ${data.result.confidence?.flags?.join(', ') || 'quality threshold not met'}</div>`;
        }
      }

      // Build result HTML
      resultBox.innerHTML = `
        ${retryNotice}
        <div class="result-rating">⭐ ${r.rating} / 5.0</div>
        <p class="result-naija" id="naija-desc"></p>
        <div class="result-section">
          <h4>Simulated Review</h4>
          <p id="review-text"></p>
        </div>
        <div class="result-section">
          <h4>Agent's Reasoning</h4>
          <p id="reasoning-text"></p>
        </div>
        <div class="result-section">
          <h4>Confidence</h4>
          <p>Score: ${r.confidence?.score ?? 'N/A'} ${r.confidence?.passed ? '✅' : '⚠️'}</p>
        </div>
      `;

      // Type out the text fields
      await typeText(document.getElementById('naija-desc'), `"${r.naija_descriptor}"`, 30);
      await typeText(document.getElementById('review-text'), r.review, 15);
      await typeText(document.getElementById('reasoning-text'), r.reasoning_chain || 'N/A', 12);

    } else {
      resultBox.innerHTML = `<p style="color:red">Error: ${data.error}</p>`;
    }
  } catch (e) {
    resultBox.innerHTML = `<p style="color:red">Request failed: ${e.message}</p>`;
  }
}

// ── TASK B: Recommendation with typing ──
async function submitRecommendRequest() {
  const mood = document.getElementById('mood').value.trim();
  const budget = document.getElementById('budget').value.trim();
  const location = document.getElementById('location').value.trim();
  const resultBox = document.getElementById('recommendResult');

  const reviews = CURRENT_REVIEWS.length > 0 ? CURRENT_REVIEWS : getDemoReviews();

  resultBox.className = 'result-box';
  resultBox.innerHTML = '<p class="loading">⏳ Building your persona and finding recommendations...</p>';

  try {
    const res = await fetch('/api/task-b/recommend/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ reviews, context: { mood, budget, location } })
    });
    const data = await res.json();

    if (data.success) {
      const r = data.result;

      // Build skeleton first
      resultBox.innerHTML = `
        <div class="result-section">
          <h4>Top Recommendations</h4>
          <ol style="padding-left:1.2rem" id="recs-list"></ol>
        </div>
        <p id="verdict-text" style="margin-top:1rem;font-weight:700;color:var(--green)"></p>
        <div class="result-section">
          <h4>Agent's Reasoning</h4>
          <p id="rec-reasoning"></p>
        </div>
        ${r.filtered_explanation ? `
        <div class="result-section">
          <h4>Filtered Out</h4>
          <ul style="padding-left:1.2rem" id="filtered-list"></ul>
        </div>` : ''}
      `;

      // Type recommendations one by one
      const recsList = document.getElementById('recs-list');
      for (const rec of (r.recommendations || [])) {
        const cleaned = rec.replace(/^\d+\.\s*/, '').replace(/^\[\d+\]\s*/, '');
        const li = document.createElement('li');
        li.style.marginBottom = '0.75rem';
        recsList.appendChild(li);
        await typeText(li, cleaned, 10);
      }

      // Type verdict
      if (r.verdict) {
        await typeText(document.getElementById('verdict-text'), r.verdict, 20);
      }

      // Type reasoning
      await typeText(document.getElementById('rec-reasoning'), r.reasoning_chain || 'N/A', 10);

      // Type filtered out
      if (r.filtered_explanation) {
        const filteredList = document.getElementById('filtered-list');
        const items = r.filtered_explanation
          .split('\n')
          .filter(item => item.trim());
        for (const item of items) {
          const li = document.createElement('li');
          li.style.marginBottom = '0.5rem';
          filteredList.appendChild(li);
          await typeText(li, item.replace(/^-\s*/, '').trim(), 8);
        }
      }

    } else {
      resultBox.innerHTML = `<p style="color:red">Error: ${data.error}</p>`;
    }
  } catch (e) {
    resultBox.innerHTML = `<p style="color:red">Request failed: ${e.message}</p>`;
  }
}
// ── Comparison Lab ──
async function runComparison() {
  const rawA = document.getElementById('personaAReviews').value;
  const rawB = document.getElementById('personaBReviews').value;
  const name = document.getElementById('compareProductName').value.trim();
  const category = document.getElementById('compareProductCategory').value.trim();
  const desc = document.getElementById('compareProductDesc').value.trim();
  const price = document.getElementById('compareProductPrice').value.trim();

  if (!rawA.trim() || !rawB.trim()) { alert('Please fill in both persona review boxes.'); return; }
  if (!name) { alert('Please enter a product name.'); return; }

  const reviewsA = parseReviewInput(rawA);
  const reviewsB = parseReviewInput(rawB);
  const product = { name, category, description: desc, avg_price: price };

  const compareResults = document.getElementById('compareResults');
  compareResults.className = 'compare-results';

  const oldDelta = document.getElementById('deltaBanner');
  if (oldDelta) oldDelta.remove();

  // Also clear any previous typed content
  document.getElementById('compareBodyA').innerHTML = '<p class="loading">⏳ Generating for Persona A...</p>';
  document.getElementById('compareBodyB').innerHTML = '<p class="loading">⏳ Generating for Persona B...</p>';
  // Fire both requests in parallel
  let dataA = null, dataB = null;
  try {
    const [resA, resB] = await Promise.all([
      fetch('/api/task-a/generate/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ reviews: reviewsA, product })
      }),
      fetch('/api/task-a/generate/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ reviews: reviewsB, product })
      })
    ]);
    [dataA, dataB] = await Promise.all([resA.json(), resB.json()]);
  } catch (e) {
    document.getElementById('compareBodyA').innerHTML = `<p style="color:red">Request failed: ${e.message}</p>`;
    document.getElementById('compareBodyB').innerHTML = `<p style="color:red">Request failed: ${e.message}</p>`;
    return;
  }

  // Render both skeletons BEFORE typing — this ensures all IDs exist in the DOM
  if (dataA && dataA.success) {
    const r = dataA.result;
    document.getElementById('compareBodyA').innerHTML = `
      <div class="compare-rating">⭐ ${r.rating} / 5.0</div>
      <div class="compare-naija">"${r.naija_descriptor || ''}"</div>
      <div class="compare-review-text" id="compare-review-a"></div>
      <div class="compare-reasoning">
        <strong>Agent Reasoning</strong>
        <span id="compare-reasoning-a"></span>
      </div>
    `;
  } else {
    document.getElementById('compareBodyA').innerHTML = `<p style="color:red">Error: ${dataA?.error || 'Unknown error'}</p>`;
  }

  if (dataB && dataB.success) {
    const r = dataB.result;
    document.getElementById('compareBodyB').innerHTML = `
      <div class="compare-rating">⭐ ${r.rating} / 5.0</div>
      <div class="compare-naija">"${r.naija_descriptor || ''}"</div>
      <div class="compare-review-text" id="compare-review-b"></div>
      <div class="compare-reasoning">
        <strong>Agent Reasoning</strong>
        <span id="compare-reasoning-b"></span>
      </div>
    `;
  } else {
    document.getElementById('compareBodyB').innerHTML = `<p style="color:red">Error: ${dataB?.error || 'Unknown error'}</p>`;
  }

  // NOW type — all DOM elements are guaranteed to exist
  if (dataA && dataA.success) {
    const r = dataA.result;
    const reviewEl = document.getElementById('compare-review-a');
    const reasoningEl = document.getElementById('compare-reasoning-a');
    if (reviewEl) await typeText(reviewEl, r.review || '', 12);
    if (reasoningEl) await typeText(reasoningEl, r.reasoning_chain || 'N/A', 8);
  }

  if (dataB && dataB.success) {
    const r = dataB.result;
    const reviewEl = document.getElementById('compare-review-b');
    const reasoningEl = document.getElementById('compare-reasoning-b');
    if (reviewEl) await typeText(reviewEl, r.review || '', 12);
    if (reasoningEl) await typeText(reasoningEl, r.reasoning_chain || 'N/A', 8);
  }

  // Delta banner
  if (dataA?.success && dataB?.success) {
    const ratingA = dataA.result.rating;
    const ratingB = dataB.result.rating;
    const delta = Math.abs(ratingA - ratingB).toFixed(1);
    const higher = ratingA >= ratingB ? 'Persona A' : 'Persona B';
    const lower = ratingA >= ratingB ? 'Persona B' : 'Persona A';

    const banner = document.createElement('div');
    banner.id = 'deltaBanner';
    banner.className = 'delta-banner';
    banner.innerHTML = `
      <span class="delta-number">${delta} ⭐ difference</span>
      <p class="delta-sub">${higher} rated it ${Math.max(ratingA, ratingB)}/5 &nbsp;·&nbsp; ${lower} rated it ${Math.min(ratingA, ratingB)}/5</p>
      <span class="delta-tag">Same product. Different personas. That's behavioural fidelity.</span>
    `;
    compareResults.appendChild(banner);
  }
}
// ── Demo fallback reviews ──
function getDemoReviews() {
  return [
    { stars: 4, text: "Solid spot, service was decent. Prices a bit steep but worth it.", user_id: "demo" },
    { stars: 5, text: "Best jollof rice I've had outside my mama's kitchen. Will definitely return.", user_id: "demo" },
    { stars: 2, text: "Waited 45 minutes for food. Not acceptable. The taste was average at best.", user_id: "demo" },
    { stars: 4, text: "Good atmosphere, fast service. Price is fair for the quality.", user_id: "demo" },
    { stars: 3, text: "Okay experience. Nothing spectacular, nothing terrible.", user_id: "demo" },
  ];
}
// ── Cold Start ──
let COLD_START_STRICTNESS = 3;
let COLD_START_PRIORITIES = [];

function toggleColdStart() {
  const form = document.getElementById('cold-start-form');
  const icon = document.getElementById('cold-start-toggle-icon');
  const analyseBtn = document.getElementById('analyse-btn');
  const textarea = document.getElementById('userReviewsInput');

  if (form.classList.contains('hidden')) {
    form.classList.remove('hidden');
    icon.textContent = '▼';
    textarea.disabled = true;
    textarea.style.opacity = '0.4';
    analyseBtn.style.display = 'none';
  } else {
    form.classList.add('hidden');
    icon.textContent = '▶';
    textarea.disabled = false;
    textarea.style.opacity = '1';
    analyseBtn.style.display = '';
  }
}

function selectStrictness(val) {
  COLD_START_STRICTNESS = val;
  document.querySelectorAll('.scale-btn').forEach((btn, i) => {
    btn.classList.toggle('active', i + 1 === val);
  });
}

function togglePriority(btn, value) {
  btn.classList.toggle('active');
  if (btn.classList.contains('active')) {
    COLD_START_PRIORITIES.push(value);
  } else {
    COLD_START_PRIORITIES = COLD_START_PRIORITIES.filter(p => p !== value);
  }
}

async function submitColdStart() {
  const loves  = document.getElementById('cold-loves').value.trim();
  const hates  = document.getElementById('cold-hates').value.trim();
  const budget = document.getElementById('cold-budget').value.trim();
  const personaCard = document.getElementById('personaCard');

  if (!loves || !hates) {
    alert('Please fill in what you love and hate.');
    return;
  }

  personaCard.className = 'persona-card';
  personaCard.innerHTML = `
    <div class="persona-card-header">
      <span>⏳</span>
      <h4>Building your persona from questionnaire...</h4>
    </div>
  `;

  const answers = {
    rating_strictness: COLD_START_STRICTNESS,
    priorities: COLD_START_PRIORITIES,
    loves: loves.split(',').map(s => s.trim()).filter(Boolean),
    hates: hates.split(',').map(s => s.trim()).filter(Boolean),
    price_budget: budget,
  };

  try {
    const res = await fetch('/api/task-a/cold-start/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ answers })
    });
    const data = await res.json();

    if (data.success) {
      // Set global persona so Task A and Task B work normally
      CURRENT_PERSONA = data.persona_display;
      // Build synthetic reviews array so downstream agents have something to work with
      CURRENT_REVIEWS = [
        { stars: data.persona_display.avg_rating, text: `Things I love: ${loves}. Things I hate: ${hates}. Priorities: ${COLD_START_PRIORITIES.join(', ')}.`, user_id: 'cold_start' }
      ];

      personaCard.innerHTML = buildPersonaCardHTML(
        data.persona_display,
        `Cold-start persona built from your answers. Rating strictness: ${COLD_START_STRICTNESS}/5.`
      );

      // Add cold-start badge to the card header
      const header = personaCard.querySelector('.persona-card-header h4');
      if (header) {
        header.innerHTML += '<span class="cold-start-badge">✨ Cold Start</span>';
      }

      // Close the form
      toggleColdStart();

    } else {
      personaCard.innerHTML = `<div class="persona-card-header"><span>❌</span><h4>Error: ${data.error}</h4></div>`;
    }
  } catch (e) {
    personaCard.innerHTML = `<div class="persona-card-header"><span>❌</span><h4>Request failed: ${e.message}</h4></div>`;
  }
}
