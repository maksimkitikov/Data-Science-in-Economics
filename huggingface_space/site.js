/* =========================================================
   Beyond GDP -- interactive visualisations
   Loads JSON data and renders Plotly charts. Keeps a single
   shared layout / palette so every chart looks coherent.
   ========================================================= */

const PALETTE = {
  navy:   "#1a2332",
  gold:   "#f5b400",
  teal:   "#2563eb",
  coral:  "#ef4444",
  green:  "#10b981",
  slate:  "#64748b",
  paper:  "#fbf9f4",
  white:  "#ffffff",
};

const BASE_LAYOUT = {
  font: { family: 'Inter, -apple-system, sans-serif', size: 13, color: PALETTE.navy },
  paper_bgcolor: PALETTE.white,
  plot_bgcolor:  PALETTE.white,
  margin: { l: 60, r: 24, t: 40, b: 50 },
  xaxis: { gridcolor: '#eef2f7', zerolinecolor: '#e2e8f0', linecolor: '#cbd5e1', tickfont: { size: 12 } },
  yaxis: { gridcolor: '#eef2f7', zerolinecolor: '#e2e8f0', linecolor: '#cbd5e1', tickfont: { size: 12 } },
  hoverlabel: { bgcolor: PALETTE.navy, bordercolor: PALETTE.navy,
                font: { color: PALETTE.white, family: 'Inter, sans-serif', size: 12 } },
  colorway: [PALETTE.teal, PALETTE.gold, PALETTE.coral, PALETTE.green, PALETTE.slate],
};

const BASE_CONFIG = {
  responsive: true,
  displaylogo: false,
  modeBarButtonsToRemove: ['lasso2d', 'select2d', 'autoScale2d', 'toggleSpikelines'],
};


/* ---------- Data loaders --------------------------------------------
   We prefer the in-memory bundle (window.SITE_DATA) so the site works
   even when opened from the file system. We fall back to fetch() so the
   data files in docs/data/ remain useful as a separate API.            */
async function loadJSON(path) {
  const key = path.replace(/^.*data\//, "").replace(/\.json$/, "");
  if (window.SITE_DATA && window.SITE_DATA[key] !== undefined) {
    return window.SITE_DATA[key];
  }
  const r = await fetch(path);
  if (!r.ok) throw new Error(`Failed to load ${path}`);
  return r.json();
}


/* ---------- Section 1: Top/Bottom ranking --------------------------- */
async function drawRankings() {
  const countries = await loadJSON('data/countries.json');
  const sorted = [...countries].sort((a, b) => b.ladder - a.ladder);
  const top = sorted.slice(0, 10).reverse();
  const bot = sorted.slice(-10);

  const layout = {
    ...BASE_LAYOUT,
    grid: { rows: 1, columns: 2, pattern: 'independent', ygap: 0.15 },
    height: 540,
    showlegend: false,
    annotations: [
      { text: '<b>Top 10 (WHR 2023)</b>', x: 0, xref: 'x domain', y: 1.06, yref: 'y domain', showarrow: false, font: { size: 14, color: PALETTE.navy }, xanchor: 'left' },
      { text: '<b>Bottom 10 (WHR 2023)</b>', x: 0, xref: 'x2 domain', y: 1.06, yref: 'y2 domain', showarrow: false, font: { size: 14, color: PALETTE.navy }, xanchor: 'left' },
    ],
    xaxis:  { ...BASE_LAYOUT.xaxis, range: [0, 8.2], title: { text: 'Ladder score', font: { size: 12, color: PALETTE.slate } } },
    xaxis2: { ...BASE_LAYOUT.xaxis, range: [0, 4.4], title: { text: 'Ladder score', font: { size: 12, color: PALETTE.slate } }, anchor: 'y2' },
    yaxis:  { ...BASE_LAYOUT.yaxis, automargin: true, ticklabelposition: 'outside' },
    yaxis2: { ...BASE_LAYOUT.yaxis, automargin: true, anchor: 'x2', ticklabelposition: 'outside' },
    margin: { l: 110, r: 80, t: 40, b: 50 },
  };

  const traces = [
    {
      type: 'bar', orientation: 'h',
      x: top.map(c => c.ladder),
      y: top.map(c => c.name),
      text: top.map(c => c.ladder.toFixed(2)),
      textposition: 'outside',
      textfont: { color: PALETTE.navy, size: 11 },
      marker: { color: PALETTE.navy },
      hovertemplate: '<b>%{y}</b><br>Ladder: %{x:.3f}<extra></extra>',
    },
    {
      type: 'bar', orientation: 'h',
      x: bot.map(c => c.ladder),
      y: bot.map(c => c.name),
      text: bot.map(c => c.ladder.toFixed(2)),
      textposition: 'outside',
      textfont: { color: PALETTE.navy, size: 11 },
      marker: { color: PALETTE.gold },
      xaxis: 'x2', yaxis: 'y2',
      hovertemplate: '<b>%{y}</b><br>Ladder: %{x:.3f}<extra></extra>',
    },
  ];

  Plotly.newPlot('rank-chart', traces, layout, BASE_CONFIG);
}


/* ---------- Section 2: GDP vs Ladder scatter ------------------------ */
async function drawGdpScatter() {
  const countries = await loadJSON('data/countries.json');
  const pts = countries.filter(c => c.gdp_ppp && c.ladder);

  // Fit a LOWESS-like rolling window in JS for the smoother
  const sorted = [...pts].sort((a, b) => a.gdp_ppp - b.gdp_ppp);
  const win = Math.max(15, Math.round(sorted.length * 0.35));
  const smooth = sorted.map((_, i) => {
    const lo = Math.max(0, i - Math.floor(win / 2));
    const hi = Math.min(sorted.length, lo + win);
    const slice = sorted.slice(lo, hi);
    const meanX = slice.reduce((s, p) => s + p.gdp_ppp, 0) / slice.length;
    const meanY = slice.reduce((s, p) => s + p.ladder,  0) / slice.length;
    return { x: meanX, y: meanY };
  });

  const highlight = ['FIN', 'DNK', 'USA', 'CRI', 'BRA', 'IND', 'ZWE', 'AFG', 'NOR'];

  const layout = {
    ...BASE_LAYOUT,
    height: 480,
    xaxis: { ...BASE_LAYOUT.xaxis, type: 'log', title: { text: 'GDP per capita, PPP — log scale (US$, World Bank 2022)', font: { size: 12, color: PALETTE.slate } } },
    yaxis: { ...BASE_LAYOUT.yaxis, title: { text: 'Ladder score (WHR 2023)', font: { size: 12, color: PALETTE.slate } } },
    legend: { x: 0.02, y: 0.98, bgcolor: 'rgba(255,255,255,0.85)', bordercolor: '#cbd5e1', borderwidth: 1 },
  };

  const traces = [
    {
      type: 'scatter', mode: 'markers',
      x: pts.map(c => c.gdp_ppp),
      y: pts.map(c => c.ladder),
      text: pts.map(c => `<b>${c.name}</b> (${c.code})`),
      hovertemplate: '%{text}<br>GDP/capita PPP: $%{x:,.0f}<br>Ladder: %{y:.2f}<extra></extra>',
      marker: { color: PALETTE.teal, size: 9, opacity: 0.7, line: { color: PALETTE.white, width: 1 } },
      name: 'Country',
    },
    {
      type: 'scatter', mode: 'lines',
      x: smooth.map(p => p.x),
      y: smooth.map(p => p.y),
      line: { color: PALETTE.navy, width: 3, shape: 'spline' },
      hoverinfo: 'skip',
      name: 'LOWESS smoother',
    },
  ];

  // Annotation labels for highlighted countries
  layout.annotations = pts
    .filter(c => highlight.includes(c.code))
    .map(c => ({
      x: c.gdp_ppp, y: c.ladder, text: c.code,
      showarrow: false,
      xanchor: 'left', yanchor: 'bottom',
      xshift: 6, yshift: 4,
      font: { size: 11, color: PALETTE.navy, family: 'Inter, sans-serif' },
    }));

  Plotly.newPlot('gdp-chart', traces, layout, BASE_CONFIG);
}


/* ---------- Section 3: Decomposition --------------------------------- */
async function drawDecomposition() {
  const data = await loadJSON('data/decomposition.json');
  const colors = [PALETTE.navy, PALETTE.teal, '#7faaff', PALETTE.gold, PALETTE.coral, PALETTE.slate];

  const countries = data.rows.map(r => r.country).reverse();
  const traces = data.vars.map((v, i) => ({
    type: 'bar', orientation: 'h',
    name: data.labels[i],
    x: data.rows.map(r => r[v]).reverse(),
    y: countries,
    marker: { color: colors[i] },
    hovertemplate: '<b>%{y}</b><br>' + data.labels[i] + ': %{x:+.3f}<extra></extra>',
  }));

  const layout = {
    ...BASE_LAYOUT,
    barmode: 'relative',
    height: 580,
    margin: { l: 130, r: 130, t: 30, b: 50 },
    xaxis: { ...BASE_LAYOUT.xaxis, title: { text: 'Contribution to Ladder score (deviation from sample mean)', font: { size: 12, color: PALETTE.slate } } },
    yaxis: { ...BASE_LAYOUT.yaxis, automargin: true },
    legend: { orientation: 'v', x: 1.01, y: 1, bgcolor: 'rgba(255,255,255,0.95)', font: { size: 11 } },
  };

  Plotly.newPlot('decomp-chart', traces, layout, BASE_CONFIG);
}


/* ---------- Section 4: OLS table ------------------------------------ */
async function drawOlsTable() {
  const reg = await loadJSON('data/regressions.json');
  const orderedTerms = ['log_gdp', 'log_gdp_wb', 'social_support', 'life_exp_healthy', 'freedom', 'corruption'];
  const niceLabels = {
    log_gdp:          'Log GDP per capita (WHR)',
    log_gdp_wb:       'Log GDP per capita PPP (WB)',
    social_support:   'Social support',
    life_exp_healthy: 'Healthy life expectancy',
    freedom:          'Freedom',
    corruption:       'Corruption (perceptions)',
  };

  // Build a {term: {model: coef}} index
  const idx = {};
  reg.forEach(r => {
    if (!idx[r.term]) idx[r.term] = {};
    idx[r.term][r.model] = { coef: r.coef, p: r.p };
  });

  const tbody = document.querySelector('#ols-table tbody');
  tbody.innerHTML = '';
  orderedTerms.forEach(t => {
    const row = document.createElement('tr');
    const head = document.createElement('th');
    head.textContent = niceLabels[t];
    row.appendChild(head);

    ['m1', 'm2', 'm3', 'm4', 'm5', 'm6'].forEach(m => {
      const cell = document.createElement('td');
      const v = idx[t]?.[m];
      if (v) {
        const stars = v.p < 0.01 ? '***' : v.p < 0.05 ? '**' : v.p < 0.10 ? '*' : '';
        cell.innerHTML = `${v.coef.toFixed(3)}<sup>${stars}</sup>`;
      } else {
        cell.textContent = '—';
        cell.style.color = '#cbd5e1';
      }
      row.appendChild(cell);
    });
    tbody.appendChild(row);
  });

  // R² and N rows: take the first record per model
  const fits = {};
  reg.forEach(r => {
    if (!fits[r.model]) fits[r.model] = { r2: r.r2, n: r.n };
  });
  ['m1', 'm2', 'm3', 'm4', 'm5', 'm6'].forEach((m, i) => {
    document.getElementById('ols-r2-' + (i + 1)).textContent = fits[m].r2.toFixed(3);
    document.getElementById('ols-n-' + (i + 1)).textContent  = fits[m].n;
  });
}


/* ---------- Section 5: Causal forest -------------------------------- */
async function drawCausalForest() {
  const cate     = await loadJSON('data/cate.json');
  const headline = await loadJSON('data/cate_headline.json');
  const imp      = await loadJSON('data/cf_importance.json');

  // Banner
  const ate = headline.ate;
  document.getElementById('ate-value').textContent = (ate >= 0 ? '+' : '') + ate.toFixed(3);
  document.getElementById('ate-ci').textContent =
    `[${headline.ate_ci[0].toFixed(3)}, ${headline.ate_ci[1].toFixed(3)}]`;

  // CATE histogram
  Plotly.newPlot('cate-hist',
    [{ type: 'histogram', x: cate.map(d => d.cate),
       xbins: { size: 0.015 },
       marker: { color: PALETTE.teal, opacity: 0.85, line: { color: PALETTE.white, width: 1 } },
       hovertemplate: 'CATE: %{x:.3f}<br>Countries: %{y}<extra></extra>' }],
    { ...BASE_LAYOUT, height: 360,
      title: { text: '<b>Distribution of CATEs</b>', x: 0, font: { size: 14, color: PALETTE.navy } },
      xaxis: { ...BASE_LAYOUT.xaxis, title: 'CATE: Ladder gain from above-median GDP' },
      yaxis: { ...BASE_LAYOUT.yaxis, title: 'Number of countries' },
      shapes: [{ type: 'line', x0: ate, x1: ate, y0: 0, y1: 1, yref: 'paper',
                 line: { color: PALETTE.gold, width: 2, dash: 'dash' } }],
      annotations: [{ x: ate, y: 1, yref: 'paper', text: `ATE = ${ate.toFixed(3)}`,
                      showarrow: false, xanchor: 'left', xshift: 6, yshift: -6,
                      font: { color: PALETTE.gold, size: 12 }, bgcolor: 'rgba(0,0,0,0)' }],
    }, BASE_CONFIG);

  // CATE vs GDP
  const labels = ['IND', 'CRI', 'BRA', 'FIN', 'NOR', 'USA'];
  Plotly.newPlot('cate-vs-gdp',
    [{ type: 'scatter', mode: 'markers',
       x: cate.map(d => d.gdp_ppp),
       y: cate.map(d => d.cate),
       text: cate.map(d => `<b>${d.name}</b> (${d.code})`),
       hovertemplate: '%{text}<br>GDP/capita PPP: $%{x:,.0f}<br>CATE: %{y:+.3f}<extra></extra>',
       marker: { color: PALETTE.teal, size: 9, opacity: 0.7, line: { color: PALETTE.white, width: 1 } } }],
    { ...BASE_LAYOUT, height: 360,
      title: { text: '<b>CATE versus GDP per capita</b>', x: 0, font: { size: 14, color: PALETTE.navy } },
      xaxis: { ...BASE_LAYOUT.xaxis, type: 'log', title: 'GDP per capita, PPP (log axis, US$)' },
      yaxis: { ...BASE_LAYOUT.yaxis, title: 'Estimated CATE' },
      shapes: [{ type: 'line', x0: 0, x1: 1, xref: 'paper', y0: ate, y1: ate,
                 line: { color: PALETTE.gold, width: 1.5, dash: 'dash' } }],
      annotations: cate.filter(d => labels.includes(d.code)).map(d => ({
        x: d.gdp_ppp, y: d.cate, text: d.code, showarrow: false,
        xanchor: 'left', xshift: 6, yshift: 2,
        font: { size: 10, color: PALETTE.navy } })),
    }, BASE_CONFIG);

  // Feature importance
  const sorted = [...imp].sort((a, b) => a.importance - b.importance);
  Plotly.newPlot('cf-importance',
    [{ type: 'bar', orientation: 'h',
       x: sorted.map(d => d.importance),
       y: sorted.map(d => d.feature),
       marker: { color: PALETTE.teal },
       text: sorted.map(d => d.importance.toFixed(3)),
       textposition: 'outside',
       textfont: { color: PALETTE.navy, size: 11 },
       hovertemplate: '<b>%{y}</b><br>Importance: %{x:.3f}<extra></extra>' }],
    { ...BASE_LAYOUT, height: 320,
      margin: { l: 140, r: 60, t: 30, b: 40 },
      xaxis: { ...BASE_LAYOUT.xaxis, title: 'Split-importance' },
      yaxis: { ...BASE_LAYOUT.yaxis, automargin: true },
    }, BASE_CONFIG);
}


/* ---------- Section 6: Chapters + time series ----------------------- */
async function drawChaptersAndTs() {
  const ch = await loadJSON('data/chapters.json');

  Plotly.newPlot('chapters-chart',
    [
      { type: 'bar', x: ch.map(d => d.year), y: ch.map(d => d.n_chapters),
        name: 'Chapters per edition',
        marker: { color: PALETTE.teal, opacity: 0.85 },
        hovertemplate: '%{x}<br>Chapters: %{y}<extra></extra>' },
      { type: 'scatter', mode: 'lines+markers',
        x: ch.map(d => d.year), y: ch.map(d => d.mean_read_min),
        name: 'Mean reading time (min)',
        line: { color: PALETTE.gold, width: 3 },
        marker: { color: PALETTE.gold, size: 9 },
        yaxis: 'y2',
        hovertemplate: '%{x}<br>Mean read: %{y:.1f} min<extra></extra>' },
    ],
    { ...BASE_LAYOUT, height: 380,
      legend: { x: 0.02, y: 0.98, bgcolor: 'rgba(255,255,255,0.85)' },
      xaxis: { ...BASE_LAYOUT.xaxis, dtick: 1, title: 'WHR edition year' },
      yaxis: { ...BASE_LAYOUT.yaxis, title: { text: 'Chapters per edition', font: { color: PALETTE.teal } }, tickfont: { color: PALETTE.teal } },
      yaxis2: { overlaying: 'y', side: 'right', title: { text: 'Mean reading time (min)', font: { color: PALETTE.gold } }, tickfont: { color: PALETTE.gold }, gridcolor: 'transparent' },
    }, BASE_CONFIG);

  const ts = await loadJSON('data/timeseries.json');
  const palette10 = [PALETTE.teal, PALETTE.gold, PALETTE.coral, PALETTE.green,
                     '#9333ea', '#ec4899', PALETTE.navy, PALETTE.slate];
  const traces = Object.entries(ts).map(([country, rows], i) => ({
    type: 'scatter', mode: 'lines+markers',
    name: country,
    x: rows.map(r => r.year),
    y: rows.map(r => r.ladder),
    line: { color: palette10[i % palette10.length], width: 2 },
    marker: { size: 7, color: palette10[i % palette10.length] },
    hovertemplate: `<b>${country}</b><br>%{x}: %{y:.2f}<extra></extra>`,
  }));

  Plotly.newPlot('ts-chart', traces,
    { ...BASE_LAYOUT, height: 420,
      legend: { orientation: 'h', y: -0.18 },
      xaxis: { ...BASE_LAYOUT.xaxis, dtick: 1, title: 'WHR edition year' },
      yaxis: { ...BASE_LAYOUT.yaxis, title: 'Ladder score' },
    }, BASE_CONFIG);
}


/* ---------- Hero animated counters ----------------------------------- */
function animateNumber(el, end, decimals = 0, suffix = '') {
  if (!el) return;
  const start = 0;
  const dur = 1100;
  const t0 = performance.now();
  function tick(now) {
    const t = Math.min(1, (now - t0) / dur);
    const eased = 1 - Math.pow(1 - t, 3);
    const v = start + (end - start) * eased;
    el.textContent = (decimals > 0 ? v.toFixed(decimals) : Math.round(v).toLocaleString()) + suffix;
    if (t < 1) requestAnimationFrame(tick);
  }
  requestAnimationFrame(tick);
}

async function fillStats() {
  try {
    const countries = await loadJSON('data/countries.json');
    const top = countries[0];
    const bot = countries[countries.length - 1];
    animateNumber(document.getElementById('stat-top'), top.ladder, 1);
    animateNumber(document.getElementById('stat-bot'), bot.ladder, 1);
    animateNumber(document.getElementById('stat-n'),   countries.length, 0);
  } catch (e) { /* leave the static fallbacks */ }
}


/* ---------- Mobile nav toggle --------------------------------------- */
function wireNav() {
  const bar = document.querySelector('.topbar');
  const btn = document.querySelector('.nav-toggle');
  if (!btn || !bar) return;
  btn.addEventListener('click', () => {
    const open = bar.classList.toggle('open');
    btn.setAttribute('aria-expanded', open ? 'true' : 'false');
  });
  bar.querySelectorAll('nav a').forEach(a => a.addEventListener('click', () => {
    bar.classList.remove('open');
    btn.setAttribute('aria-expanded', 'false');
  }));
}


/* ---------- Boot ---------------------------------------------------- */
window.addEventListener('DOMContentLoaded', async () => {
  wireNav();
  fillStats();
  try { await drawRankings(); }       catch (e) { console.error('rank',     e); }
  try { await drawGdpScatter(); }     catch (e) { console.error('gdp',      e); }
  try { await drawDecomposition(); }  catch (e) { console.error('decomp',   e); }
  try { await drawOlsTable(); }       catch (e) { console.error('ols',      e); }
  try { await drawCausalForest(); }   catch (e) { console.error('cf',       e); }
  try { await drawChaptersAndTs(); }  catch (e) { console.error('chapters', e); }
});
