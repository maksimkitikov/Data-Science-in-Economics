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
  margin: { l: 64, r: 32, t: 40, b: 56 },
  autosize: true,
  hovermode: 'closest',
  xaxis: { gridcolor: '#eef2f7', zerolinecolor: '#e2e8f0', linecolor: '#cbd5e1', tickfont: { size: 12 }, automargin: true },
  yaxis: { gridcolor: '#eef2f7', zerolinecolor: '#e2e8f0', linecolor: '#cbd5e1', tickfont: { size: 12 }, automargin: true },
  hoverlabel: {
    bgcolor: PALETTE.navy,
    bordercolor: PALETTE.navy,
    font: { color: PALETTE.white, family: 'Inter, sans-serif', size: 12 },
    align: 'left',
  },
  colorway: [PALETTE.teal, PALETTE.gold, PALETTE.coral, PALETTE.green, PALETTE.slate],
  transition: { duration: 350, easing: 'cubic-in-out' },
};

const BASE_CONFIG = {
  responsive: true,
  displaylogo: false,
  scrollZoom: false,
  modeBarButtonsToRemove: ['lasso2d', 'select2d', 'autoScale2d', 'toggleSpikelines', 'hoverClosestCartesian', 'hoverCompareCartesian'],
  toImageButtonOptions: { format: 'png', filename: 'beyond-gdp', scale: 2 },
};

const CHART_REGISTRY = [];
function register(id) { CHART_REGISTRY.push(id); }


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

  const buildLayout = () => {
    const stack = window.innerWidth < 700;
    const rows = stack ? 2 : 1;
    const cols = stack ? 1 : 2;
    return {
      ...BASE_LAYOUT,
      grid: { rows, columns: cols, pattern: 'independent', xgap: 0.18, ygap: stack ? 0.28 : 0.15 },
      height: stack ? 760 : 580,
      showlegend: false,
      annotations: [
        { text: '<b>Top 10 (WHR 2023)</b>',    x: 0, xref: 'x domain',  y: 1.07, yref: 'y domain',  showarrow: false, font: { size: 14, color: PALETTE.navy }, xanchor: 'left' },
        { text: '<b>Bottom 10 (WHR 2023)</b>', x: 0, xref: 'x2 domain', y: 1.07, yref: 'y2 domain', showarrow: false, font: { size: 14, color: PALETTE.navy }, xanchor: 'left' },
      ],
      xaxis:  { ...BASE_LAYOUT.xaxis, range: [0, 8.6], title: { text: 'Ladder score', font: { size: 12, color: PALETTE.slate }, standoff: 12 } },
      xaxis2: { ...BASE_LAYOUT.xaxis, range: [0, 4.7], title: { text: 'Ladder score', font: { size: 12, color: PALETTE.slate }, standoff: 12 }, anchor: 'y2' },
      yaxis:  { ...BASE_LAYOUT.yaxis, automargin: true, ticklabelposition: 'outside' },
      yaxis2: { ...BASE_LAYOUT.yaxis, automargin: true, anchor: 'x2', ticklabelposition: 'outside' },
      margin: { l: 12, r: 36, t: 56, b: 60 },
    };
  };

  const traces = [
    {
      type: 'bar', orientation: 'h',
      x: top.map(c => c.ladder),
      y: top.map(c => c.name),
      text: top.map(c => c.ladder.toFixed(2)),
      textposition: 'outside',
      cliponaxis: false,
      textfont: { color: PALETTE.navy, size: 11 },
      marker: { color: PALETTE.navy, line: { color: PALETTE.navy, width: 1 } },
      hovertemplate: '<b>%{y}</b><br>Ladder: %{x:.3f}<extra></extra>',
    },
    {
      type: 'bar', orientation: 'h',
      x: bot.map(c => c.ladder),
      y: bot.map(c => c.name),
      text: bot.map(c => c.ladder.toFixed(2)),
      textposition: 'outside',
      cliponaxis: false,
      textfont: { color: PALETTE.navy, size: 11 },
      marker: { color: PALETTE.gold, line: { color: PALETTE.gold, width: 1 } },
      xaxis: 'x2', yaxis: 'y2',
      hovertemplate: '<b>%{y}</b><br>Ladder: %{x:.3f}<extra></extra>',
    },
  ];

  await Plotly.newPlot('rank-chart', traces, buildLayout(), BASE_CONFIG);
  register('rank-chart');

  // Re-build (not just resize) when crossing the breakpoint
  let wasStacked = window.innerWidth < 700;
  window.addEventListener('resize', () => {
    const isStacked = window.innerWidth < 700;
    if (isStacked !== wasStacked) {
      wasStacked = isStacked;
      Plotly.relayout('rank-chart', buildLayout());
    }
  }, { passive: true });
}


/* ---------- Section 2: GDP vs Ladder scatter ------------------------ */
async function drawGdpScatter() {
  const countries = await loadJSON('data/countries.json');
  const pts = countries.filter(c => c.gdp_ppp && c.ladder);

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
    margin: { l: 64, r: 32, t: 24, b: 64 },
    xaxis: {
      ...BASE_LAYOUT.xaxis, type: 'log',
      title: { text: 'GDP per capita, PPP — log scale (US$, World Bank 2022)', font: { size: 12, color: PALETTE.slate }, standoff: 14 }
    },
    yaxis: {
      ...BASE_LAYOUT.yaxis,
      title: { text: 'Ladder score (WHR 2023)', font: { size: 12, color: PALETTE.slate }, standoff: 8 }
    },
    legend: {
      x: 0.02, y: 0.98,
      bgcolor: 'rgba(255,255,255,0.9)',
      bordercolor: '#cbd5e1', borderwidth: 1,
      font: { size: 11 },
    },
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

  layout.annotations = pts
    .filter(c => highlight.includes(c.code))
    .map(c => ({
      x: c.gdp_ppp, y: c.ladder, text: c.code,
      showarrow: false,
      xanchor: 'left', yanchor: 'bottom',
      xshift: 7, yshift: 5,
      font: { size: 11, color: PALETTE.navy, family: 'Inter, sans-serif', weight: 600 },
    }));

  await Plotly.newPlot('gdp-chart', traces, layout, BASE_CONFIG);
  register('gdp-chart');
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
    height: 600,
    margin: { l: 130, r: 32, t: 40, b: 70 },
    xaxis: {
      ...BASE_LAYOUT.xaxis,
      title: { text: 'Contribution to Ladder score (deviation from sample mean)', font: { size: 12, color: PALETTE.slate }, standoff: 14 }
    },
    yaxis: { ...BASE_LAYOUT.yaxis, automargin: true },
    legend: {
      orientation: 'h',
      x: 0.5, xanchor: 'center',
      y: -0.18, yanchor: 'top',
      bgcolor: 'rgba(255,255,255,0.95)',
      font: { size: 11 },
    },
  };

  await Plotly.newPlot('decomp-chart', traces, layout, BASE_CONFIG);
  register('decomp-chart');
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
    head.scope = 'row';
    head.textContent = niceLabels[t];
    row.appendChild(head);

    ['m1', 'm2', 'm3', 'm4', 'm5', 'm6'].forEach(m => {
      const cell = document.createElement('td');
      const v = idx[t]?.[m];
      if (v) {
        cell.classList.add('coef');
        const stars =
          v.p < 0.01 ? '***' :
          v.p < 0.05 ? '**'  :
          v.p < 0.10 ? '*'   : '';
        const num = document.createElement('span');
        num.textContent = v.coef.toFixed(3);
        cell.appendChild(num);
        if (stars) {
          const s = document.createElement('span');
          s.className = 'stars';
          s.setAttribute('aria-label', `significant at p < ${stars.length === 3 ? '0.01' : stars.length === 2 ? '0.05' : '0.10'}`);
          s.textContent = stars;
          cell.appendChild(s);
        }
        cell.title = `coef = ${v.coef.toFixed(4)}, p = ${v.p.toFixed(4)}`;
      } else {
        cell.classList.add('muted');
        cell.textContent = '—';
      }
      row.appendChild(cell);
    });
    tbody.appendChild(row);
  });

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

  const ate = headline.ate;
  const ateValueEl = document.getElementById('ate-value');
  const ateCiEl    = document.getElementById('ate-ci');
  if (ateValueEl) ateValueEl.textContent = (ate >= 0 ? '+' : '−') + Math.abs(ate).toFixed(3);
  if (ateCiEl)    ateCiEl.textContent =
    `[${headline.ate_ci[0].toFixed(3)}, ${headline.ate_ci[1].toFixed(3)}]`;

  // CATE histogram — keep ATE annotation OUTSIDE the plot area (above)
  // so it never overlaps the bars themselves.
  const cateValues = cate.map(d => d.cate);
  await Plotly.newPlot('cate-hist',
    [{
      type: 'histogram', x: cateValues,
      xbins: { size: 0.015 },
      marker: { color: PALETTE.teal, opacity: 0.85, line: { color: PALETTE.white, width: 1 } },
      hovertemplate: 'CATE: %{x:.3f}<br>Countries: %{y}<extra></extra>',
      name: 'CATE',
    }],
    { ...BASE_LAYOUT, height: 380,
      margin: { l: 60, r: 28, t: 64, b: 60 },
      title: { text: '<b>Distribution of CATEs</b>', x: 0, xanchor: 'left', y: 0.98, font: { size: 14, color: PALETTE.navy } },
      xaxis: { ...BASE_LAYOUT.xaxis, title: { text: 'CATE: Ladder gain from above-median GDP', font: { size: 12, color: PALETTE.slate }, standoff: 12 } },
      yaxis: { ...BASE_LAYOUT.yaxis, title: { text: 'Number of countries', font: { size: 12, color: PALETTE.slate }, standoff: 8 } },
      shapes: [{
        type: 'line', x0: ate, x1: ate, y0: 0, y1: 1, yref: 'paper',
        line: { color: PALETTE.gold, width: 2, dash: 'dash' },
      }],
      annotations: [{
        x: ate, y: 1.04, yref: 'paper',
        text: `<b>ATE = ${(ate >= 0 ? '+' : '−') + Math.abs(ate).toFixed(3)}</b>`,
        showarrow: false,
        xanchor: 'center', yanchor: 'bottom',
        font: { color: PALETTE.gold, size: 12, family: 'Inter, sans-serif' },
        bgcolor: 'rgba(255,255,255,0.0)',
      }],
    }, BASE_CONFIG);
  register('cate-hist');

  // CATE vs GDP — keep the ATE reference dashed line, label it once at the right edge
  const labels = ['IND', 'CRI', 'BRA', 'FIN', 'NOR', 'USA'];
  await Plotly.newPlot('cate-vs-gdp',
    [{ type: 'scatter', mode: 'markers',
       x: cate.map(d => d.gdp_ppp),
       y: cate.map(d => d.cate),
       text: cate.map(d => `<b>${d.name}</b> (${d.code})`),
       hovertemplate: '%{text}<br>GDP/capita PPP: $%{x:,.0f}<br>CATE: %{y:+.3f}<extra></extra>',
       marker: { color: PALETTE.teal, size: 9, opacity: 0.7, line: { color: PALETTE.white, width: 1 } },
       name: 'Country',
     }],
    { ...BASE_LAYOUT, height: 380,
      margin: { l: 60, r: 32, t: 64, b: 60 },
      title: { text: '<b>CATE versus GDP per capita</b>', x: 0, xanchor: 'left', y: 0.98, font: { size: 14, color: PALETTE.navy } },
      xaxis: { ...BASE_LAYOUT.xaxis, type: 'log', title: { text: 'GDP per capita, PPP (log axis, US$)', font: { size: 12, color: PALETTE.slate }, standoff: 12 } },
      yaxis: { ...BASE_LAYOUT.yaxis, title: { text: 'Estimated CATE', font: { size: 12, color: PALETTE.slate }, standoff: 8 } },
      shapes: [{ type: 'line', x0: 0, x1: 1, xref: 'paper', y0: ate, y1: ate,
                 line: { color: PALETTE.gold, width: 1.5, dash: 'dash' } }],
      annotations: [
        ...cate.filter(d => labels.includes(d.code)).map(d => ({
          x: d.gdp_ppp, y: d.cate, text: d.code, showarrow: false,
          xanchor: 'left', xshift: 7, yshift: 3,
          font: { size: 10, color: PALETTE.navy, weight: 600 },
        })),
        { x: 1, xref: 'paper', y: ate, text: `ATE`, showarrow: false,
          xanchor: 'right', yanchor: 'bottom', xshift: -4, yshift: 2,
          font: { color: PALETTE.gold, size: 11, weight: 600 } },
      ],
    }, BASE_CONFIG);
  register('cate-vs-gdp');

  // Feature importance — keep value labels INSIDE the bar so they never run
  // off the plot area on narrow screens. Pad x-axis right side a hair.
  const sorted = [...imp].sort((a, b) => a.importance - b.importance);
  const xMax = Math.max(...sorted.map(d => d.importance)) * 1.18;
  await Plotly.newPlot('cf-importance',
    [{ type: 'bar', orientation: 'h',
       x: sorted.map(d => d.importance),
       y: sorted.map(d => d.feature),
       marker: { color: PALETTE.teal, line: { color: PALETTE.teal, width: 1 } },
       text: sorted.map(d => d.importance.toFixed(3)),
       textposition: 'outside',
       cliponaxis: false,
       textfont: { color: PALETTE.navy, size: 11 },
       hovertemplate: '<b>%{y}</b><br>Importance: %{x:.3f}<extra></extra>',
       name: 'Importance',
     }],
    { ...BASE_LAYOUT, height: 340,
      margin: { l: 150, r: 60, t: 30, b: 56 },
      xaxis: {
        ...BASE_LAYOUT.xaxis,
        range: [0, xMax],
        title: { text: 'Split-importance', font: { size: 12, color: PALETTE.slate }, standoff: 12 }
      },
      yaxis: { ...BASE_LAYOUT.yaxis, automargin: true },
    }, BASE_CONFIG);
  register('cf-importance');
}


/* ---------- Section 6: Chapters + time series ----------------------- */
async function drawChaptersAndTs() {
  const ch = await loadJSON('data/chapters.json');

  // Chapters chart — secondary axis on the right needs extra right margin
  // so its title "Mean reading time (min)" never gets clipped.
  await Plotly.newPlot('chapters-chart',
    [
      { type: 'bar', x: ch.map(d => d.year), y: ch.map(d => d.n_chapters),
        name: 'Chapters per edition',
        marker: { color: PALETTE.teal, opacity: 0.85 },
        hovertemplate: '%{x}<br>Chapters: %{y}<extra></extra>' },
      { type: 'scatter', mode: 'lines+markers',
        x: ch.map(d => d.year), y: ch.map(d => d.mean_read_min),
        name: 'Mean reading time (min)',
        line: { color: PALETTE.gold, width: 3, shape: 'spline' },
        marker: { color: PALETTE.gold, size: 9, line: { color: PALETTE.white, width: 1 } },
        yaxis: 'y2',
        hovertemplate: '%{x}<br>Mean read: %{y:.1f} min<extra></extra>' },
    ],
    { ...BASE_LAYOUT, height: 400,
      margin: { l: 64, r: 84, t: 30, b: 64 },
      legend: {
        orientation: 'h',
        x: 0.5, xanchor: 'center',
        y: 1.12, yanchor: 'bottom',
        bgcolor: 'rgba(255,255,255,0.0)',
        font: { size: 11 },
      },
      xaxis: { ...BASE_LAYOUT.xaxis, dtick: 1, title: { text: 'WHR edition year', font: { size: 12, color: PALETTE.slate }, standoff: 12 } },
      yaxis: {
        ...BASE_LAYOUT.yaxis,
        title: { text: 'Chapters per edition', font: { size: 12, color: PALETTE.teal }, standoff: 8 },
        tickfont: { color: PALETTE.teal },
      },
      yaxis2: {
        overlaying: 'y', side: 'right',
        title: { text: 'Mean reading time (min)', font: { size: 12, color: PALETTE.gold }, standoff: 12 },
        tickfont: { color: PALETTE.gold },
        gridcolor: 'transparent',
        automargin: true,
      },
    }, BASE_CONFIG);
  register('chapters-chart');

  const ts = await loadJSON('data/timeseries.json');
  const palette10 = [PALETTE.teal, PALETTE.gold, PALETTE.coral, PALETTE.green,
                     '#9333ea', '#ec4899', PALETTE.navy, PALETTE.slate];
  const traces = Object.entries(ts).map(([country, rows], i) => ({
    type: 'scatter', mode: 'lines+markers',
    name: country,
    x: rows.map(r => r.year),
    y: rows.map(r => r.ladder),
    line: { color: palette10[i % palette10.length], width: 2, shape: 'spline' },
    marker: { size: 7, color: palette10[i % palette10.length], line: { color: PALETTE.white, width: 1 } },
    hovertemplate: `<b>${country}</b><br>%{x}: %{y:.2f}<extra></extra>`,
  }));

  await Plotly.newPlot('ts-chart', traces,
    { ...BASE_LAYOUT, height: 460,
      margin: { l: 60, r: 32, t: 30, b: 100 },
      legend: {
        orientation: 'h',
        x: 0.5, xanchor: 'center',
        y: -0.22, yanchor: 'top',
        font: { size: 11 },
      },
      xaxis: { ...BASE_LAYOUT.xaxis, dtick: 1, title: { text: 'WHR edition year', font: { size: 12, color: PALETTE.slate }, standoff: 12 } },
      yaxis: { ...BASE_LAYOUT.yaxis, title: { text: 'Ladder score', font: { size: 12, color: PALETTE.slate }, standoff: 8 } },
    }, BASE_CONFIG);
  register('ts-chart');
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
    const sorted = [...countries].sort((a, b) => b.ladder - a.ladder);
    const top = sorted[0];
    const bot = sorted[sorted.length - 1];

    const trigger = () => {
      animateNumber(document.getElementById('stat-top'), top.ladder, 1);
      animateNumber(document.getElementById('stat-bot'), bot.ladder, 1);
      animateNumber(document.getElementById('stat-n'),   sorted.length, 0);
    };

    const heroStats = document.querySelector('.hero-stats');
    if (!heroStats || !('IntersectionObserver' in window)) {
      trigger();
      return;
    }
    const obs = new IntersectionObserver((entries, o) => {
      entries.forEach(e => {
        if (e.isIntersecting) {
          trigger();
          o.disconnect();
        }
      });
    }, { threshold: 0.4 });
    obs.observe(heroStats);
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


/* ---------- Scroll progress + topbar shadow + back-to-top ------------ */
function wireScrollUI() {
  const bar       = document.querySelector('.scroll-progress > span');
  const topbar    = document.querySelector('.topbar');
  const toTop     = document.querySelector('.to-top');
  const navLinks  = Array.from(document.querySelectorAll('.topbar nav a[href^="#"]'));
  const sections  = navLinks
    .map(a => document.querySelector(a.getAttribute('href')))
    .filter(Boolean);

  let ticking = false;

  const update = () => {
    const doc    = document.documentElement;
    const scroll = window.scrollY || doc.scrollTop;
    const max    = (doc.scrollHeight - doc.clientHeight) || 1;
    const pct    = Math.max(0, Math.min(1, scroll / max));

    if (bar) bar.style.width = (pct * 100) + '%';
    if (topbar) topbar.classList.toggle('scrolled', scroll > 4);
    if (toTop)  toTop.classList.toggle('show', scroll > 480);

    // Active-section highlight
    if (sections.length) {
      const probe = scroll + 96;
      let activeIdx = -1;
      for (let i = 0; i < sections.length; i++) {
        if (sections[i].offsetTop <= probe) activeIdx = i;
      }
      navLinks.forEach((a, i) => a.classList.toggle('active', i === activeIdx));
    }
    ticking = false;
  };

  const onScroll = () => {
    if (!ticking) {
      window.requestAnimationFrame(update);
      ticking = true;
    }
  };

  window.addEventListener('scroll', onScroll, { passive: true });
  window.addEventListener('resize', onScroll, { passive: true });
  update();

  if (toTop) {
    toTop.addEventListener('click', () => {
      window.scrollTo({ top: 0, behavior: 'smooth' });
    });
  }
}


/* ---------- Scroll reveal ------------------------------------------- */
function wireReveal() {
  const els = document.querySelectorAll('[data-reveal]');
  if (!els.length) return;

  if (!('IntersectionObserver' in window)) {
    els.forEach(el => el.classList.add('in-view'));
    return;
  }

  const obs = new IntersectionObserver((entries) => {
    entries.forEach(e => {
      if (e.isIntersecting) {
        e.target.classList.add('in-view');
        obs.unobserve(e.target);
      }
    });
  }, { threshold: 0.12, rootMargin: '0px 0px -40px 0px' });

  els.forEach(el => obs.observe(el));
}


/* ---------- Resize handler for Plotly ------------------------------- */
function wireResize() {
  let resizeTimer = null;
  const resize = () => {
    CHART_REGISTRY.forEach(id => {
      const el = document.getElementById(id);
      if (el && window.Plotly) {
        try { Plotly.Plots.resize(el); } catch (_) { /* noop */ }
      }
    });
  };
  window.addEventListener('resize', () => {
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(resize, 120);
  }, { passive: true });
}


/* ---------- Boot ---------------------------------------------------- */
window.addEventListener('DOMContentLoaded', async () => {
  wireNav();
  wireScrollUI();
  wireReveal();
  wireResize();
  fillStats();

  // Render charts. We don't await each one in series elsewhere — just collect
  // errors so a single failure cannot block the rest.
  const tasks = [
    ['rank',     drawRankings],
    ['gdp',      drawGdpScatter],
    ['decomp',   drawDecomposition],
    ['ols',      drawOlsTable],
    ['cf',       drawCausalForest],
    ['chapters', drawChaptersAndTs],
  ];
  for (const [name, fn] of tasks) {
    try { await fn(); } catch (e) { console.error(name, e); }
  }
});
