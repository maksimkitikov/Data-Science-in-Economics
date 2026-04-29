/* Beyond GDP - interactive Plotly charts.
   Loads JSON and renders every chart with a shared palette. */

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


function loadJSON(path) {
  const key = path.replace(/^.*data\//, "").replace(/\.json$/, "");
  return window.SITE_DATA[key];
}


// Section 1: Top/Bottom ranking
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
}


// Section 2: GDP vs Ladder scatter
async function drawGdpScatter() {
  const countries = await loadJSON('data/countries.json');
  const smooth = loadJSON('data/gdp_smoother.json');
  const pts = countries.filter(c => c.gdp_ppp && c.ladder);
  const highlight = ['FIN', 'DNK', 'USA', 'CRI', 'BRA', 'IND', 'ZWE', 'AFG', 'NOR'];

  const layout = {
    ...BASE_LAYOUT,
    height: 480,
    margin: { l: 64, r: 32, t: 24, b: 64 },
    xaxis: {
      ...BASE_LAYOUT.xaxis, type: 'log',
      title: { text: 'GDP per capita, PPP - log scale (US$, World Bank 2022)', font: { size: 12, color: PALETTE.slate }, standoff: 14 }
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
      x: smooth.map(p => p.gdp_ppp),
      y: smooth.map(p => p.ladder),
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


// Section 3: Decomposition
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


// Section 4: OLS table
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
        cell.textContent = '-';
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


// Section 5: Causal forest
async function drawCausalForest() {
  const cate = await loadJSON('data/cate.json');
  const headline = await loadJSON('data/cate_headline.json');

  const ate = headline.ate;
  const ateValueEl = document.getElementById('ate-value');
  const ateCiEl = document.getElementById('ate-ci');
  if (ateValueEl) ateValueEl.textContent = (ate >= 0 ? '+' : '-') + Math.abs(ate).toFixed(3);
  if (ateCiEl) {
    ateCiEl.textContent =
      `[${headline.ate_ci[0].toFixed(3)}, ${headline.ate_ci[1].toFixed(3)}]`;
  }

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
        text: `<b>ATE = ${(ate >= 0 ? '+' : '-') + Math.abs(ate).toFixed(3)}</b>`,
        showarrow: false,
        xanchor: 'center', yanchor: 'bottom',
        font: { color: PALETTE.gold, size: 12, family: 'Inter, sans-serif' },
        bgcolor: 'rgba(255,255,255,0.0)',
      }],
    }, BASE_CONFIG);
  register('cate-hist');
}




// Resize charts when the window changes width.
function wireResize() {
  let t = null;
  window.addEventListener('resize', () => {
    clearTimeout(t);
    t = setTimeout(() => {
      CHART_REGISTRY.forEach(id => {
        const el = document.getElementById(id);
        if (el && window.Plotly) Plotly.Plots.resize(el);
      });
    }, 120);
  }, { passive: true });
}


window.addEventListener('DOMContentLoaded', async () => {
  wireResize();
  const tasks = [
    ['rank',         drawRankings],
    ['gdp',          drawGdpScatter],
    ['decomp',       drawDecomposition],
    ['ols',          drawOlsTable],
    ['cf',           drawCausalForest],
  ];
  for (const [name, fn] of tasks) {
    try { await fn(); } catch (e) { console.error(name, e); }
  }
});
