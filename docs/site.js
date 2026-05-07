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
  const imp = await loadJSON('data/cf_importance.json');

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


// Section 6: Chapters + time series
async function drawChaptersAndTs() {
  const ch = await loadJSON('data/chapters.json');
  const chaptersByYear = loadJSON('data/chapters_by_year.json') || {};

  function trunc(s, n) { return s.length > n ? s.slice(0, n - 1) + '…' : s; }
  function previewFor(year) {
    const list = chaptersByYear[year] || [];
    if (!list.length) return '';
    const lines = list.slice(0, 3).map(c => '• ' + trunc(c.title, 60));
    if (list.length > 3) lines.push(`<i>+ ${list.length - 3} more</i>`);
    return lines.join('<br>');
  }

  const barX = ch.map(d => d.year);
  const barY = ch.map(d => d.n_chapters);
  const barCustom = barX.map(previewFor);

  await Plotly.newPlot('chapters-chart',
    [
      { type: 'bar', x: barX, y: barY,
        name: 'Chapters per edition',
        marker: { color: PALETTE.teal, opacity: 0.85 },
        customdata: barCustom,
        hovertemplate:
          '<b>WHR %{x}</b> &nbsp;|&nbsp; %{y} chapters<br>' +
          '<span style="font-size:11px">%{customdata}</span><extra></extra>' },
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
      hoverlabel: { ...BASE_LAYOUT.hoverlabel, align: 'left' },
    }, BASE_CONFIG);
  register('chapters-chart');

  const ts = await loadJSON('data/timeseries.json');
  const palette10 = [PALETTE.teal, PALETTE.gold, PALETTE.coral, PALETTE.green,
                     '#9333ea', '#ec4899', PALETTE.navy, PALETTE.slate];
  const countries = Object.keys(ts);

  const allYears = [...new Set(
    Object.values(ts).flatMap(rows => rows.map(r => r.year))
  )].sort((a, b) => a - b);
  // Pin the y-range so the axis doesn't bounce as the animation builds.
  const allLadders = Object.values(ts).flatMap(rows => rows.map(r => r.ladder));
  const yLo = Math.floor(Math.min(...allLadders) * 10) / 10 - 0.2;
  const yHi = Math.ceil(Math.max(...allLadders) * 10) / 10 + 0.2;

  function tracesUpTo(year) {
    return countries.map((country, i) => {
      const rows = ts[country].filter(r => r.year <= year);
      return {
        type: 'scatter', mode: 'lines+markers',
        name: country,
        x: rows.map(r => r.year),
        y: rows.map(r => r.ladder),
        line: { color: palette10[i % palette10.length], width: 2, shape: 'spline' },
        marker: { size: 7, color: palette10[i % palette10.length], line: { color: PALETTE.white, width: 1 } },
        hovertemplate: `<b>${country}</b><br>%{x}: %{y:.2f}<extra></extra>`,
      };
    });
  }

  // Show full picture by default; frames build it year-by-year on Play.
  const initial = tracesUpTo(allYears[allYears.length - 1]);
  const frames = allYears.map(y => ({ name: String(y), data: tracesUpTo(y) }));

  const animOpts = {
    mode: 'immediate',
    transition: { duration: 450, easing: 'cubic-in-out' },
    frame: { duration: 850, redraw: false },
  };

  const sliderSteps = allYears.map(y => ({
    label: String(y),
    method: 'animate',
    args: [[String(y)], { ...animOpts, frame: { duration: 350, redraw: false } }],
  }));

  const tsLayout = {
    ...BASE_LAYOUT, height: 500,
    margin: { l: 60, r: 32, t: 90, b: 130 },
    legend: {
      orientation: 'h',
      x: 0.5, xanchor: 'center',
      y: -0.28, yanchor: 'top',
      font: { size: 11 },
    },
    xaxis: {
      ...BASE_LAYOUT.xaxis,
      dtick: 1,
      range: [allYears[0] - 0.25, allYears[allYears.length - 1] + 0.25],
      title: { text: 'WHR edition year', font: { size: 12, color: PALETTE.slate }, standoff: 12 },
    },
    yaxis: {
      ...BASE_LAYOUT.yaxis,
      range: [yLo, yHi],
      title: { text: 'Ladder score', font: { size: 12, color: PALETTE.slate }, standoff: 8 },
    },
    updatemenus: [{
      type: 'buttons',
      direction: 'left',
      x: 0,
      xanchor: 'left',
      y: 1.16,
      yanchor: 'top',
      pad: { r: 8, t: 4, b: 4, l: 4 },
      showactive: false,
      bgcolor: PALETTE.white,
      bordercolor: '#cbd5e1',
      borderwidth: 1,
      font: { size: 12, color: PALETTE.navy },
      buttons: [
        {
          label: '▶  Play',
          method: 'animate',
          args: [allYears.map(String), { ...animOpts, fromcurrent: false }],
        },
        {
          label: '❚❚  Pause',
          method: 'animate',
          args: [[null], {
            mode: 'immediate',
            transition: { duration: 0 },
            frame: { duration: 0, redraw: false },
          }],
        },
      ],
    }],
    sliders: [{
      active: allYears.length - 1,
      x: 0.16,
      xanchor: 'left',
      y: 1.18,
      yanchor: 'top',
      len: 0.82,
      pad: { t: 0, b: 0 },
      currentvalue: {
        prefix: 'Year: ',
        font: { size: 12, color: PALETTE.navy },
        xanchor: 'right',
        offset: 8,
      },
      ticklen: 4,
      tickcolor: '#cbd5e1',
      bgcolor: '#eef2f7',
      activebgcolor: PALETTE.gold,
      bordercolor: 'transparent',
      font: { size: 11 },
      steps: sliderSteps,
    }],
  };

  await Plotly.newPlot('ts-chart', initial, tsLayout, BASE_CONFIG);
  await Plotly.addFrames('ts-chart', frames);
  register('ts-chart');
}


async function fillSensitivityTable() {
  const tbody = document.querySelector('#sensitivity-table tbody');
  const s = loadJSON('data/ate_sensitivity.json');
  if (!tbody || !s) return;
  const fmtUSD = v => '$' + Math.round(v).toLocaleString('en-US');
  const sign = v => (v >= 0 ? '+' : '') + Number(v).toFixed(3);
  const row = (k) => {
    const r = s[k];
    return `<tr><td>${r.label}</td><td>${fmtUSD(r.cutoff_usd)}</td><td><strong>${sign(r.ate)}</strong></td><td>[${sign(r.ci[0])}, ${sign(r.ci[1])}]</td></tr>`;
  };
  tbody.innerHTML = row('headline') + row('robust');
}


// Country explorer: type a name, see all indicators for that country.
async function wireCountryExplorer() {
  const input = document.getElementById('country-input');
  const card = document.getElementById('country-card');
  const random = document.getElementById('country-random');
  const suggestions = document.getElementById('country-suggestions');
  if (!input || !card || !suggestions) return;

  const countries = loadJSON('data/countries.json');
  const cateMap = {};
  (loadJSON('data/cate.json') || []).forEach(r => { cateMap[r.code] = r; });
  const ranking = [...countries].sort((a, b) => b.ladder - a.ladder);
  const rankByCode = new Map(ranking.map((c, i) => [c.code, i + 1]));

  const fmtNum = (v, d = 2) => v == null || Number.isNaN(v) ? '-' : v.toFixed(d);
  const fmtUsd = v => v == null ? '-' : '$' + Math.round(v).toLocaleString('en-US');
  const fmtSign = (v, d = 3) => v == null ? '-' : (v >= 0 ? '+' : '') + v.toFixed(d);

  function renderCard(c) {
    const rank = rankByCode.get(c.code) || '-';
    const ct = cateMap[c.code];
    const cateBlock = ct
      ? `<div><span class="cc-label">CATE (causal forest)</span><span class="cc-val">${fmtSign(ct.cate)} <span class="cc-ci">[${fmtSign(ct.ci_lo)}, ${fmtSign(ct.ci_hi)}]</span></span></div>`
      : '';
    card.innerHTML = `
      <div class="cc-head">
        <div class="cc-id"><span class="cc-flag">${c.code}</span><h3>${c.name}</h3></div>
        <span class="cc-rank">Rank <strong>${rank}</strong> / ${countries.length}</span>
      </div>
      <div class="cc-grid">
        <div><span class="cc-label">Ladder score</span><span class="cc-val">${fmtNum(c.ladder)}</span></div>
        <div><span class="cc-label">GDP per capita PPP</span><span class="cc-val">${fmtUsd(c.gdp_ppp)}</span></div>
        <div><span class="cc-label">Healthy life exp.</span><span class="cc-val">${fmtNum(c.life_exp_healthy, 1)} yrs</span></div>
        <div><span class="cc-label">Social support</span><span class="cc-val">${fmtNum(c.social_support)}</span></div>
        <div><span class="cc-label">Freedom</span><span class="cc-val">${fmtNum(c.freedom)}</span></div>
        <div><span class="cc-label">Corruption (perceptions)</span><span class="cc-val">${fmtNum(c.corruption)}</span></div>
        <div><span class="cc-label">Internet (%)</span><span class="cc-val">${fmtNum(c.internet_pct, 1)}</span></div>
        <div><span class="cc-label">Urban (%)</span><span class="cc-val">${fmtNum(c.urban_pct, 1)}</span></div>
        ${cateBlock}
      </div>`;
  }

  function pickByName(query) {
    const q = query.toLowerCase().trim();
    if (!q) return null;
    return countries.find(x => x.name.toLowerCase() === q)
        || countries.find(x => x.name.toLowerCase().startsWith(q))
        || countries.find(x => x.code.toLowerCase() === q);
  }

  function show(query) {
    if (!query.trim()) {
      card.innerHTML = '<p class="cc-hint">Pick a country above and its profile appears here.</p>';
      return;
    }
    const c = pickByName(query);
    if (!c) {
      card.innerHTML = `<p class="cc-hint">No match for <em>${query}</em> - try a different spelling.</p>`;
      return;
    }
    renderCard(c);
  }

  const sortedNames = [...countries].sort((a, b) => a.name.localeCompare(b.name));
  let activeIdx = -1;

  function closeSuggestions() {
    suggestions.hidden = true;
    suggestions.innerHTML = '';
    activeIdx = -1;
  }

  function buildSuggestions(query) {
    const q = query.toLowerCase().trim();
    if (!q) { closeSuggestions(); return; }
    const startsWith = sortedNames.filter(c => c.name.toLowerCase().startsWith(q));
    const contains = sortedNames.filter(c => !c.name.toLowerCase().startsWith(q)
        && c.name.toLowerCase().includes(q));
    const matches = [...startsWith, ...contains].slice(0, 8);
    if (!matches.length) { closeSuggestions(); return; }
    suggestions.innerHTML = matches.map((c, i) =>
      `<li role="option" data-name="${c.name}" data-code="${c.code}" class="suggestion${i === 0 ? ' active' : ''}">
         <span class="s-flag">${c.code}</span><span>${c.name}</span>
       </li>`
    ).join('');
    suggestions.hidden = false;
    activeIdx = 0;
  }

  function selectSuggestion(li) {
    if (!li) return;
    input.value = li.dataset.name;
    closeSuggestions();
    show(li.dataset.name);
    input.blur();
  }

  input.addEventListener('input', () => {
    buildSuggestions(input.value);
    show(input.value);
  });

  input.addEventListener('keydown', (e) => {
    const items = suggestions.querySelectorAll('.suggestion');
    if (suggestions.hidden || !items.length) {
      if (e.key === 'Enter') show(input.value);
      return;
    }
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      activeIdx = (activeIdx + 1) % items.length;
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      activeIdx = (activeIdx - 1 + items.length) % items.length;
    } else if (e.key === 'Enter') {
      e.preventDefault();
      selectSuggestion(items[activeIdx >= 0 ? activeIdx : 0]);
      return;
    } else if (e.key === 'Escape') {
      closeSuggestions();
      return;
    } else {
      return;
    }
    items.forEach((li, i) => li.classList.toggle('active', i === activeIdx));
  });

  suggestions.addEventListener('mousedown', (e) => {
    const li = e.target.closest('.suggestion');
    if (li) {
      e.preventDefault();
      selectSuggestion(li);
    }
  });

  document.addEventListener('click', (e) => {
    if (!e.target.closest('.search-wrap')) closeSuggestions();
  });

  if (random) {
    random.addEventListener('click', () => {
      const c = countries[Math.floor(Math.random() * countries.length)];
      input.value = c.name;
      closeSuggestions();
      show(c.name);
    });
  }

  input.value = 'Finland';
  show('Finland');
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
    ['explorer',     wireCountryExplorer],
    ['gdp',          drawGdpScatter],
    ['decomp',       drawDecomposition],
    ['ols',          drawOlsTable],
    ['cf',           drawCausalForest],
    ['sensitivity',  fillSensitivityTable],
    ['chapters',     drawChaptersAndTs],
  ];
  for (const [name, fn] of tasks) {
    try { await fn(); } catch (e) { console.error(name, e); }
  }
});
