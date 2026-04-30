/* F1 Analytics - Main Application JS */
const API = '';
let currentSeason = 2025;
let charts = {};

// ===== NAVIGATION =====
document.querySelectorAll('.nav-link').forEach(link => {
  link.addEventListener('click', e => {
    e.preventDefault();
    const page = link.dataset.page;
    document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));
    link.classList.add('active');
    document.querySelectorAll('.page-section').forEach(s => s.classList.remove('active'));
    document.getElementById('page' + page.charAt(0).toUpperCase() + page.slice(1)).classList.add('active');
    if (page === 'dashboard') loadDashboard();
    if (page === 'analytics') loadAnalyticsSelectors();
    if (page === 'leaderboard') loadLeaderboard();
  });
});

// Mobile menu
document.getElementById('mobileMenuBtn')?.addEventListener('click', () => {
  document.getElementById('mainNav').classList.toggle('open');
});

// Season selector
document.getElementById('seasonSelect')?.addEventListener('change', e => {
  currentSeason = parseInt(e.target.value);
  // Reload data for all pages when season changes
  loadDashboard();
  loadAnalyticsSelectors();
  loadLeaderboard();
});

// ===== DASHBOARD =====
async function loadDashboard() {
  loadDriverStandings();
  loadConstructorStandings();
  loadTeamPerformance();
}

async function fetchJSON(url) {
  try {
    const r = await fetch(API + url);
    if (!r.ok) throw new Error(r.statusText);
    return await r.json();
  } catch (e) {
    console.error('Fetch error:', url, e);
    return null;
  }
}

async function loadDriverStandings() {
  const data = await fetchJSON(`/api/dashboard/driver-standings?season=${currentSeason}`);
  const el = document.getElementById('driverStandings');
  if (!data || !data.length) {
    el.innerHTML = '<p style="color:var(--f1-text-dim);text-align:center;padding:40px">No data available. Run ETL to seed database.</p>';
    return;
  }
  document.getElementById('statDrivers').textContent = data.length;
  const teams = [...new Set(data.map(d => d.team))];
  document.getElementById('statTeams').textContent = teams.length;

  el.innerHTML = data.map(d => `
    <div class="driver-card" style="--tc:${d.team_color}">
      <div style="position:absolute;left:0;top:0;bottom:0;width:3px;background:${d.team_color};border-radius:0 2px 2px 0"></div>
      <span class="driver-flag">${d.country_flag || '🏁'}</span>
      <span class="driver-pos ${d.position<=3?'p'+d.position:''}">${d.position}</span>
      <div class="driver-info">
        <div class="driver-name">${d.full_name || d.abbreviation}</div>
        <div class="driver-team" style="color:${d.team_color}">${d.team}</div>
      </div>
      <div class="driver-points">${d.points}<span class="driver-points-label">PTS</span></div>
    </div>
  `).join('');
}

async function loadConstructorStandings() {
  const data = await fetchJSON(`/api/dashboard/constructor-standings?season=${currentSeason}`);
  const el = document.getElementById('constructorStandings');
  if (!data || !data.length) { el.innerHTML = '<p style="color:var(--f1-text-dim);text-align:center;padding:40px">No data available.</p>'; return; }

  const maxPts = Math.max(...data.map(c => c.points), 1);
  el.innerHTML = data.map(c => `
    <div class="constructor-card">
      <div style="position:absolute;left:0;top:0;bottom:0;width:4px;background:${c.team_color}"></div>
      <span class="constructor-pos">${c.position}</span>
      <div class="constructor-info">
        <div class="constructor-name" style="color:${c.team_color}">${c.name}</div>
        <div class="constructor-drivers">${(c.drivers||[]).map(d=>d.full_name||d.abbreviation).join(' • ')}</div>
      </div>
      <div class="constructor-points">${c.points}<span class="driver-points-label" style="display:block;font-family:Inter;font-weight:400;font-size:.6rem;color:var(--f1-text-dim)">PTS</span></div>
      <div class="constructor-bar" style="width:${(c.points/maxPts)*100}%;background:${c.team_color}"></div>
    </div>
  `).join('');
}

async function loadTeamPerformance() {
  const data = await fetchJSON(`/api/dashboard/team-performance?season=${currentSeason}`);
  if (!data || !data.teams) return;

  const ctx = document.getElementById('teamPerformanceChart');
  if (!ctx) return;
  if (charts.teamPerf) charts.teamPerf.destroy();

  const raceLabels = (data.races || []).map(r => r.length > 15 ? r.substring(0,12)+'...' : r);

  charts.teamPerf = new Chart(ctx, {
    type: 'line',
    data: {
      labels: raceLabels,
      datasets: data.teams.map(t => ({
        label: t.name,
        data: t.points,
        borderColor: t.color,
        backgroundColor: t.color + '20',
        borderWidth: 2,
        pointRadius: 3,
        pointBackgroundColor: t.color,
        tension: 0.3,
        fill: false,
      }))
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { position: 'bottom', labels: { color: '#888', font: { size: 11 }, boxWidth: 12, padding: 16 } },
      },
      scales: {
        x: { ticks: { color: '#666', font: { size: 10 }, maxRotation: 45 }, grid: { color: 'rgba(255,255,255,0.03)' } },
        y: { ticks: { color: '#666' }, grid: { color: 'rgba(255,255,255,0.05)' }, title: { display: true, text: 'Points', color: '#666' } }
      },
      interaction: { mode: 'index', intersect: false }
    }
  });

  // Count races
  const cal = await fetchJSON(`/api/dashboard/race-calendar?season=${currentSeason}`);
  if (cal) document.getElementById('statRaces').textContent = cal.length;
}

// ===== ANALYTICS =====
async function loadAnalyticsSelectors() {
  const races = await fetchJSON(`/api/analytics/races?season=${currentSeason}`);
  const drivers = await fetchJSON(`/api/analytics/drivers?season=${currentSeason}`);
  const raceSel = document.getElementById('analyticsRaceSelect');
  const d1Sel = document.getElementById('analyticsDriver1');
  const d2Sel = document.getElementById('analyticsDriver2');

  if (races) {
    raceSel.innerHTML = races.map(r => `<option value="${r.round}">${r.name}</option>`).join('');
  }
  if (drivers) {
    const opts = drivers.map(d => `<option value="${d.abbreviation}">${d.abbreviation} - ${d.full_name}</option>`).join('');
    d1Sel.innerHTML = opts;
    d2Sel.innerHTML = opts;
    if (drivers.length > 1) d2Sel.selectedIndex = 1;
  }
}

// Analytics tabs
document.querySelectorAll('.tab-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
    document.getElementById('content' + btn.dataset.tab.charAt(0).toUpperCase() + btn.dataset.tab.slice(1)).classList.add('active');
  });
});

// Analyze button
document.getElementById('btnAnalyze')?.addEventListener('click', () => {
  const round = document.getElementById('analyticsRaceSelect').value;
  const d1 = document.getElementById('analyticsDriver1').value;
  const d2 = document.getElementById('analyticsDriver2').value;
  const sess = document.getElementById('analyticsSession').value;
  loadLapTimes(round, d1, d2, sess);
  loadPositions(round);
  loadQualifying(round);
  loadStints(round);
  loadTelemetry(round, d1, d2, sess);
  loadRaceReplay(round);
});

async function loadLapTimes(round, d1, d2, sess) {
  const data = await fetchJSON(`/api/analytics/lap-times?season=${currentSeason}&round=${round}&session=${sess}`);
  if (!data) return;
  const ctx = document.getElementById('lapTimesChart');
  if (charts.lapTimes) charts.lapTimes.destroy();

  const filtered = data.filter(d => [d1, d2].includes(d.driver));
  charts.lapTimes = new Chart(ctx, {
    type: 'line',
    data: {
      datasets: filtered.map(d => ({
        label: `${d.driver} (${d.team})`,
        data: d.laps.filter(l => l.time_ms).map(l => ({ x: l.lap, y: l.time_ms / 1000 })),
        borderColor: d.team_color,
        backgroundColor: d.team_color + '30',
        borderWidth: 1.5, pointRadius: 1.5, tension: 0.1, fill: false,
      }))
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: { legend: { labels: { color: '#888' } } },
      scales: {
        x: { type: 'linear', title: { display: true, text: 'Lap', color: '#666' }, ticks: { color: '#666' }, grid: { color: 'rgba(255,255,255,0.03)' } },
        y: { title: { display: true, text: 'Lap Time (s)', color: '#666' }, ticks: { color: '#666' }, grid: { color: 'rgba(255,255,255,0.05)' } }
      }
    }
  });
}

async function loadPositions(round) {
  const data = await fetchJSON(`/api/analytics/position-changes?season=${currentSeason}&round=${round}`);
  if (!data || !data.drivers) return;
  const ctx = document.getElementById('positionsChart');
  if (charts.positions) charts.positions.destroy();

  charts.positions = new Chart(ctx, {
    type: 'line',
    data: {
      datasets: data.drivers.map(d => {
        const pts = Object.entries(d.positions).map(([l, p]) => ({ x: parseInt(l), y: p })).sort((a,b) => a.x - b.x);
        return {
          label: d.driver, data: pts, borderColor: d.team_color,
          borderWidth: 1.5, pointRadius: 0, tension: 0.1, fill: false,
        };
      })
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: { legend: { labels: { color: '#888', font: { size: 10 } } } },
      scales: {
        x: { type: 'linear', title: { display: true, text: 'Lap', color: '#666' }, ticks: { color: '#666' }, grid: { color: 'rgba(255,255,255,0.03)' } },
        y: { reverse: true, title: { display: true, text: 'Position', color: '#666' }, ticks: { color: '#666', stepSize: 1 }, grid: { color: 'rgba(255,255,255,0.05)' }, min: 1, max: 20 }
      }
    }
  });
}

async function loadQualifying(round) {
  const data = await fetchJSON(`/api/analytics/qualifying?season=${currentSeason}&round=${round}`);
  const el = document.getElementById('qualifyingGrid');
  if (!data || !data.length) { el.innerHTML = '<p style="color:#888;text-align:center;padding:40px">No qualifying data</p>'; return; }

  el.innerHTML = data.map(d => `
    <div class="quali-row">
      <span class="quali-pos" style="color:${d.team_color}">${d.position || '-'}</span>
      <span class="quali-driver">${d.full_name || d.driver}</span>
      <span class="quali-time ${d.q1 ? '' : 'eliminated'}">${d.q1 || '-'}</span>
      <span class="quali-time ${d.q2 ? '' : 'eliminated'}">${d.q2 || '-'}</span>
      <span class="quali-time ${d.q3 ? 'best' : 'eliminated'}">${d.q3 || '-'}</span>
    </div>
  `).join('');
}

async function loadStints(round) {
  const data = await fetchJSON(`/api/analytics/stints?season=${currentSeason}&round=${round}`);
  const el = document.getElementById('stintsViz');
  if (!data || !data.length) { el.innerHTML = '<p style="color:#888;text-align:center;padding:40px">No stint data</p>'; return; }

  const maxLap = Math.max(...data.flatMap(d => d.stints.map(s => s.end_lap)), 1);
  el.innerHTML = data.map(d => {
    const bars = d.stints.map(s => {
      const w = ((s.end_lap - s.start_lap + 1) / maxLap * 100);
      return `<div class="stint-segment compound-${s.compound}" style="width:${w}%">
        ${s.compound?.charAt(0) || '?'}
        <div class="stint-tooltip">${s.compound} | Laps ${s.start_lap}-${s.end_lap} (${s.laps_count})</div>
      </div>`;
    }).join('');
    return `<div class="stint-row">
      <span class="stint-driver" style="color:${d.team_color}">${d.driver}</span>
      <div class="stint-bar-container">${bars}</div>
    </div>`;
  }).join('');
}

async function loadTelemetry(round, d1, d2, sess) {
  const data = await fetchJSON(`/api/analytics/telemetry?season=${currentSeason}&round=${round}&session=${sess}&driver1=${d1}&driver2=${d2}`);
  if (!data || data.error) return;

  const drivers = Object.values(data);
  const makeChart = (canvasId, key, label, chartKey) => {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;
    if (charts[chartKey]) charts[chartKey].destroy();
    // Set explicit canvas dimensions from parent to prevent infinite stretch
    const parent = canvas.parentElement;
    canvas.style.width = '100%';
    canvas.style.height = (parent.clientHeight - 52) + 'px';
    charts[chartKey] = new Chart(canvas, {
      type: 'line',
      data: {
        datasets: drivers.map(d => ({
          label: d.driver, data: d.data.distance.map((dist, i) => ({ x: dist, y: d.data[key][i] })),
          borderColor: d.team_color, borderWidth: 1.5, pointRadius: 0, fill: false,
        }))
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        resizeDelay: 100,
        plugins: { legend: { labels: { color: '#888' } } },
        scales: {
          x: { type: 'linear', title: { display: true, text: 'Distance (m)', color: '#666' }, ticks: { color: '#666' }, grid: { color: 'rgba(255,255,255,0.03)' } },
          y: { title: { display: true, text: label, color: '#666' }, ticks: { color: '#666' }, grid: { color: 'rgba(255,255,255,0.05)' } }
        }
      }
    });
  };
  makeChart('speedChart', 'speed', 'Speed (km/h)', 'speed');
  makeChart('throttleBrakeChart', 'throttle', 'Throttle %', 'throttle');
  makeChart('gearChart', 'gear', 'Gear', 'gear');
  makeChart('rpmChart', 'rpm', 'RPM', 'rpm');
}

// ===== RACE REPLAY =====
let replayData = null, replayCircuit = null, replayFrame = 0, replayPlaying = false, replayTimer = null;

async function loadRaceReplay(round) {
  replayCircuit = await fetchJSON(`/api/analytics/circuit-map?season=${currentSeason}&round=${round}`);
  // Fetch only the LAST lap to ensure fast loading times while avoiding initial grid bunching
  replayData = await fetchJSON(`/api/analytics/gps-data?season=${currentSeason}&round=${round}&lap=last`);
  if (!replayCircuit || !replayData) return;

  replayFrame = 0;
  drawCircuit();
}

function drawCircuit() {
  const canvas = document.getElementById('circuitCanvas');
  if (!canvas || !replayCircuit) return;
  const ctx = canvas.getContext('2d');
  const W = canvas.width, H = canvas.height;
  ctx.clearRect(0, 0, W, H);

  const xs = replayCircuit.x, ys = replayCircuit.y, drs = replayCircuit.drs;
  if (!xs || !ys) return;
  
  const minX = Math.min(...xs), maxX = Math.max(...xs);
  const minY = Math.min(...ys), maxY = Math.max(...ys);
  const pad = 60;
  const sx = (W - pad*2) / (maxX - minX || 1), sy = (H - pad*2) / (maxY - minY || 1);
  const scale = Math.min(sx, sy);
  const ox = (W - (maxX - minX) * scale) / 2, oy = (H - (maxY - minY) * scale) / 2;
  const tx = x => (x - minX) * scale + ox;
  const ty = y => H - ((y - minY) * scale + oy);

  // Draw Pit Lane (Simulated as an inner parallel line near start/finish)
  ctx.strokeStyle = '#444'; ctx.lineWidth = 4; ctx.lineCap = 'round';
  ctx.beginPath();
  const pitLen = Math.min(40, xs.length);
  for(let i=0; i<pitLen; i++) {
    // Offset slightly towards center
    const offX = (xs[i] > (maxX+minX)/2) ? -15 : 15;
    const offY = (ys[i] > (maxY+minY)/2) ? -15 : 15;
    if(i===0) ctx.moveTo(tx(xs[i])+offX, ty(ys[i])+offY);
    else ctx.lineTo(tx(xs[i])+offX, ty(ys[i])+offY);
  }
  ctx.stroke();

  // Draw Base Track
  ctx.strokeStyle = '#333'; ctx.lineWidth = 12; ctx.lineJoin = 'round';
  ctx.beginPath();
  xs.forEach((x, i) => { i === 0 ? ctx.moveTo(tx(x), ty(ys[i])) : ctx.lineTo(tx(x), ty(ys[i])); });
  ctx.closePath(); ctx.stroke();

  // Draw Track Inner & DRS Zones
  ctx.lineWidth = 8;
  for(let i=1; i<xs.length; i++) {
    ctx.beginPath();
    ctx.moveTo(tx(xs[i-1]), ty(ys[i-1]));
    ctx.lineTo(tx(xs[i]), ty(ys[i]));
    // DRS is usually active when value >= 10
    ctx.strokeStyle = (drs && drs[i] >= 10) ? '#2ecc71' : '#555';
    ctx.stroke();
  }

  // Draw Sector Lines
  ctx.strokeStyle = '#e74c3c'; ctx.lineWidth = 3;
  const drawSector = (x, y, label) => {
    if(!x || !y) return;
    const px = tx(x), py = ty(y);
    ctx.beginPath(); ctx.moveTo(px - 15, py - 15); ctx.lineTo(px + 15, py + 15); ctx.stroke();
    ctx.fillStyle = '#e74c3c'; ctx.font = 'bold 10px Inter'; ctx.fillText(label, px + 20, py);
  };
  drawSector(replayCircuit.s1_x, replayCircuit.s1_y, 'Sector 1');
  drawSector(replayCircuit.s2_x, replayCircuit.s2_y, 'Sector 2');
  drawSector(xs[0], ys[0], 'Finish / S3');

  // Draw drivers and prepare overlay
  let overlayHTML = '';
  if (replayData) {
    let driversList = Object.values(replayData);
    // Sort just by arbitrary order for now, as real-time position requires distance calculation
    driversList.forEach((d, pos) => {
      const idx = Math.min(replayFrame, (d.x?.length || 1) - 1);
      
      // Build overlay HTML
      overlayHTML += `
        <div class="replay-standing-row">
            <div class="replay-standing-pos">${pos + 1}</div>
            <div class="replay-standing-color" style="background:${d.team_color}"></div>
            <div class="replay-standing-driver">${d.driver}</div>
        </div>
      `;

      if (!d.x || !d.x[idx]) return;
      const px = tx(d.x[idx]), py = ty(d.y[idx]);

      ctx.beginPath(); ctx.arc(px, py, 6, 0, Math.PI * 2);
      ctx.fillStyle = d.team_color; ctx.fill();
      ctx.strokeStyle = '#fff'; ctx.lineWidth = 1.5; ctx.stroke();

      ctx.fillStyle = '#fff'; ctx.font = 'bold 9px Inter';
      ctx.textAlign = 'center'; ctx.fillText(d.driver, px, py - 10);
    });
  }
  
  const overlayEl = document.getElementById('replayStandingsOverlay');
  if(overlayEl) overlayEl.innerHTML = overlayHTML;

  // Circuit name and lap info
  ctx.fillStyle = '#aaa'; ctx.font = '14px Orbitron';
  ctx.textAlign = 'left'; 
  ctx.fillText(replayCircuit.circuit_name || 'Grand Prix', 180, 30);
  
  ctx.fillStyle = '#f39c12'; ctx.font = 'bold 18px Orbitron';
  ctx.fillText(`LAST LAP SIMULATION`, 180, 55);
  
  // Legend for DRS
  ctx.fillStyle = '#2ecc71'; ctx.fillRect(180, 70, 12, 12);
  ctx.fillStyle = '#aaa'; ctx.font = '11px Inter'; ctx.fillText('DRS Zone', 198, 80);
}

document.getElementById('replayPlayBtn')?.addEventListener('click', () => {
  if (replayPlaying) return;
  replayPlaying = true;
  const maxFrames = replayData ? Math.max(...Object.values(replayData).map(d => d.x?.length || 0)) : 0;
  replayTimer = setInterval(() => {
    replayFrame++;
    if (replayFrame >= maxFrames) { replayFrame = maxFrames - 1; clearInterval(replayTimer); replayPlaying = false; }
    document.getElementById('replaySlider').value = (replayFrame / maxFrames * 100);
    document.getElementById('replayLapLabel').textContent = `Frame: ${replayFrame}`;
    drawCircuit();
  }, 50);
});

document.getElementById('replayPauseBtn')?.addEventListener('click', () => {
  clearInterval(replayTimer); replayPlaying = false;
});

document.getElementById('replayResetBtn')?.addEventListener('click', () => {
  clearInterval(replayTimer); replayPlaying = false;
  replayFrame = 0; document.getElementById('replaySlider').value = 0;
  drawCircuit();
});

document.getElementById('replaySlider')?.addEventListener('input', e => {
  const maxFrames = replayData ? Math.max(...Object.values(replayData).map(d => d.x?.length || 0)) : 0;
  replayFrame = Math.floor(e.target.value / 100 * maxFrames);
  drawCircuit();
});

// ===== LEADERBOARD =====
document.querySelectorAll('.lb-tab').forEach(tab => {
  tab.addEventListener('click', () => {
    document.querySelectorAll('.lb-tab').forEach(t => t.classList.remove('active'));
    tab.classList.add('active');
    document.querySelectorAll('.lb-content').forEach(c => c.classList.remove('active'));
    document.getElementById('lb' + tab.dataset.lbtab.charAt(0).toUpperCase() + tab.dataset.lbtab.slice(1)).classList.add('active');
  });
});

async function loadLeaderboard() {
  const drivers = await fetchJSON(`/api/dashboard/driver-standings?season=${currentSeason}`);
  const constructors = await fetchJSON(`/api/dashboard/constructor-standings?season=${currentSeason}`);

  const dBody = document.getElementById('driverLeaderboardBody');
  if (drivers && drivers.length) {
    dBody.innerHTML = drivers.map(d => `<tr>
      <td><span style="font-family:Orbitron;font-weight:700">${d.position}</span></td>
      <td><div class="lb-driver-cell"><div class="lb-team-color" style="background:${d.team_color}"></div><span>${d.country_flag||'🏁'} ${d.full_name||d.abbreviation}</span></div></td>
      <td style="color:${d.team_color}">${d.team}</td>
      <td>${d.nationality||''}</td>
      <td class="lb-points">${d.points}</td>
      <td>${d.wins}</td>
      <td>${d.podiums}</td>
    </tr>`).join('');
  }

  const cBody = document.getElementById('constructorLeaderboardBody');
  if (constructors && constructors.length) {
    cBody.innerHTML = constructors.map(c => `<tr>
      <td><span style="font-family:Orbitron;font-weight:700">${c.position}</span></td>
      <td><div class="lb-driver-cell"><div class="lb-team-color" style="background:${c.team_color}"></div><span style="color:${c.team_color}">${c.name}</span></div></td>
      <td>${(c.drivers||[]).map(d=>d.full_name||d.abbreviation).join(', ')}</td>
      <td class="lb-points">${c.points}</td>
    </tr>`).join('');
  }
}

// ===== LOGIN =====
document.querySelectorAll('.login-tab').forEach(tab => {
  tab.addEventListener('click', () => {
    document.querySelectorAll('.login-tab').forEach(t => t.classList.remove('active'));
    tab.classList.add('active');
    document.querySelectorAll('.login-form').forEach(f => f.classList.remove('active'));
    document.getElementById(tab.dataset.logintab === 'signin' ? 'signinForm' : 'signupForm').classList.add('active');
  });
});

document.getElementById('signinForm')?.addEventListener('submit', async e => {
  e.preventDefault();
  const msg = document.getElementById('loginMessage');
  try {
    const r = await fetch(API + '/api/auth/login', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username: document.getElementById('loginUsername').value, password: document.getElementById('loginPassword').value })
    });
    const data = await r.json();
    if (data.success) { msg.className = 'login-message success'; msg.textContent = `Welcome ${data.user.username}!`; }
    else { msg.className = 'login-message error'; msg.textContent = data.error || 'Login failed'; }
  } catch { msg.className = 'login-message error'; msg.textContent = 'Connection error'; }
});

document.getElementById('signupForm')?.addEventListener('submit', async e => {
  e.preventDefault();
  const msg = document.getElementById('registerMessage');
  try {
    const r = await fetch(API + '/api/auth/register', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        username: document.getElementById('regUsername').value,
        email: document.getElementById('regEmail').value,
        password: document.getElementById('regPassword').value
      })
    });
    const data = await r.json();
    if (data.success) { msg.className = 'login-message success'; msg.textContent = 'Account created!'; }
    else { msg.className = 'login-message error'; msg.textContent = data.error || 'Registration failed'; }
  } catch { msg.className = 'login-message error'; msg.textContent = 'Connection error'; }
});

// ===== INIT =====
document.addEventListener('DOMContentLoaded', () => { loadDashboard(); });
