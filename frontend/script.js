// FloodResQ Client Logic — Complete Full-Stack Integration

document.addEventListener('DOMContentLoaded', () => {
  // Determine API Base URL dynamically:
  // 1. window.FLOODRESQ_API_URL or <meta name="api-base">
  // 2. Relative '' when served together (e.g., Railway all-in-one)
  // 3. http://127.0.0.1:8000 when running via local static servers (Live Server, file://)
  const API_BASE = (() => {
    if (window.FLOODRESQ_API_URL) return window.FLOODRESQ_API_URL.replace(/\/$/, '');

    const metaApi = document.querySelector('meta[name="api-base"]');
    if (metaApi && metaApi.content && !metaApi.content.startsWith('http://127.0.0.1:8000')) {
      return metaApi.content.replace(/\/$/, '');
    }

    if (window.location.protocol === 'file:') return 'http://127.0.0.1:8000';

    const isLocalhost = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
    if (isLocalhost && window.location.port && window.location.port !== '8000') {
      return `http://${window.location.hostname}:8000`;
    }

    // Default to live Railway backend when running on Vercel
    if (window.location.hostname.includes('vercel.app')) {
      return 'https://floodresq-production.up.railway.app';
    }

    const storedApi = localStorage.getItem('floodresq_api_base');
    if (storedApi) return storedApi.replace(/\/$/, '');

    return '';
  })();

  let userLat = 18.5204;
  let userLng = 73.8567;
  let analyticsData = null;
  let cachedReports = [];
  let cachedResources = [];

  // ----------------- Toast Utility -----------------
  function showToast(msg, duration = 4000) {
    const toast = document.getElementById('mainToast');
    if (!toast) return;
    toast.textContent = msg;
    toast.classList.add('show');
    setTimeout(() => toast.classList.remove('show'), duration);
  }

  // ----------------- Mobile Menu -----------------
  const mobileMenu = document.getElementById('mobileMenu');
  const mainNav = document.getElementById('mainNav');
  if (mobileMenu && mainNav) {
    mobileMenu.onclick = () => mainNav.classList.toggle('open');
  }

  // ----------------- Geolocation Helper -----------------
  function captureCoordinates(callback) {
    const statusEl = document.getElementById('locationStatus');
    if (!navigator.geolocation) {
      if (statusEl) statusEl.textContent = 'Geolocation is not supported by your browser.';
      if (callback) callback(userLat, userLng);
      return;
    }
    if (statusEl) statusEl.textContent = 'Acquiring GPS coordinates…';
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        userLat = pos.coords.latitude;
        userLng = pos.coords.longitude;
        if (statusEl) {
          statusEl.textContent = `✓ GPS Captured: ${userLat.toFixed(4)}, ${userLng.toFixed(4)}`;
        }
        showToast('GPS coordinates locked.');
        if (callback) callback(userLat, userLng);
      },
      () => {
        userLat = 18.5204;
        userLng = 73.8567;
        if (statusEl) {
          statusEl.textContent = `✓ City Center Applied: ${userLat.toFixed(4)}, ${userLng.toFixed(4)} (Pune)`;
        }
        if (callback) callback(userLat, userLng);
      },
      { timeout: 10000, enableHighAccuracy: true }
    );
  }

  // ----------------- SOS Modal Logic -----------------
  const sosModal = document.getElementById('sosModal');
  const sosButton = document.getElementById('sosButton');
  const helpButton = document.getElementById('helpButton');
  const closeModal = document.getElementById('closeModal');
  const locationHelp = document.getElementById('locationHelp');
  const btnInstantSOS = document.getElementById('btnInstantSOS');
  const locationStatus = document.getElementById('locationStatus');

  [sosButton, helpButton].forEach((btn) => {
    if (btn) {
      btn.addEventListener('click', () => {
        if (sosModal) sosModal.classList.add('show');
      });
    }
  });

  if (closeModal && sosModal) {
    closeModal.onclick = () => sosModal.classList.remove('show');
  }

  window.addEventListener('click', (e) => {
    if (e.target === sosModal) sosModal.classList.remove('show');
    const ccModal = document.getElementById('commandCenterModal');
    if (e.target === ccModal) ccModal.classList.remove('show');
  });

  if (locationHelp) {
    locationHelp.onclick = () => captureCoordinates();
  }

  if (btnInstantSOS) {
    btnInstantSOS.onclick = async () => {
      btnInstantSOS.disabled = true;
      btnInstantSOS.textContent = 'Dispatching Rescue...';

      try {
        const res = await fetch(`${API_BASE}/api/sos`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            location: 'Citizen Immediate Rescue Beacon',
            lat: userLat,
            lng: userLng,
            details: 'URGENT: Life-saving rescue dispatched via one-click emergency beacon.'
          })
        });

        const data = await res.json();
        if (data.success) {
          const unit = data.dispatched_unit?.resource?.name || 'Rapid River Rescue Unit';
          const eta = data.dispatched_unit?.eta_minutes || 5;
          if (locationStatus) {
            locationStatus.innerHTML = `🚨 <b>SOS DISPATCHED!</b><br>Assigned: ${unit} (ETA: ~${eta} mins)`;
          }
          showToast(`🚨 Priority Alert! ${unit} has been dispatched.`);
          fetchStats();
          fetchMapData();
        }
      } catch (err) {
        console.error(err);
        if (locationStatus) {
          locationStatus.textContent = 'Server unreachable. Call 112 directly for emergency help.';
        }
      } finally {
        btnInstantSOS.disabled = false;
        btnInstantSOS.textContent = '🚨 Send Instant SOS Now';
      }
    };
  }

  // ----------------- Stats Ingestion -----------------
  async function fetchStats() {
    try {
      const res = await fetch(`${API_BASE}/api/stats`);
      if (!res.ok) return;
      const stats = await res.json();

      const elReports = document.getElementById('statReports');
      const elRescued = document.getElementById('statRescued');
      const elShelters = document.getElementById('statShelters');
      const elTeams = document.getElementById('statTeams');
      const elCities = document.getElementById('statCities');

      if (elReports) elReports.textContent = `${stats.citizen_reports.toLocaleString()}+`;
      if (elRescued) elRescued.textContent = stats.people_rescued.toLocaleString();
      if (elShelters) elShelters.textContent = stats.active_shelters;
      if (elTeams) elTeams.textContent = stats.rescue_teams;
      if (elCities) elCities.textContent = stats.cities_covered;

      // Command Center Card Metrics
      const elCrit = document.getElementById('metricCritical');
      const elHigh = document.getElementById('metricHigh');
      const elMod = document.getElementById('metricModerate');
      const elRescue = document.getElementById('metricRescueTeams');
      const elShelterCap = document.getElementById('metricShelterCap');

      if (elCrit) elCrit.textContent = stats.critical_incidents;
      if (elHigh) elHigh.textContent = stats.high_priority;
      if (elMod) elMod.textContent = stats.moderate_priority;
      if (elRescue) elRescue.textContent = stats.available_rescue_teams;
      if (elShelterCap) elShelterCap.textContent = `${stats.shelter_capacity}`;
    } catch (err) {
      console.warn('Could not fetch live stats:', err);
    }
  }

  // ----------------- Real-Time Analytics Tab Switching -----------------
  async function fetchAnalytics() {
    try {
      const res = await fetch(`${API_BASE}/api/analytics`);
      if (!res.ok) return;
      analyticsData = await res.json();
      renderAnalyticsTab('water_level');
    } catch (err) {
      console.warn('Could not fetch analytics:', err);
    }
  }

  function renderAnalyticsTab(tabKey) {
    if (!analyticsData || !analyticsData[tabKey]) return;
    const tabInfo = analyticsData[tabKey];

    const titleEl = document.getElementById('chartTitle');
    const dangerLineEl = document.getElementById('chartDangerLine');
    const polylineEl = document.getElementById('chartPolyline');
    const valEl = document.getElementById('chartValue');
    const trendEl = document.getElementById('chartTrend');
    const timesEl = document.getElementById('chartTimes');
    const alertTitle = document.getElementById('chartAlertTitle');
    const alertDesc = document.getElementById('chartAlertDesc');

    if (titleEl) titleEl.textContent = `${tabInfo.title} — ${tabInfo.river}`;
    if (dangerLineEl) dangerLineEl.textContent = `Danger Level (${tabInfo.danger_threshold} ${tabInfo.unit})`;
    if (valEl) valEl.textContent = `${tabInfo.current_value} ${tabInfo.unit}`;
    if (trendEl) trendEl.textContent = `↑ ${tabInfo.trend}`;

    if (alertTitle) alertTitle.textContent = tabInfo.alert.split('.')[0] || 'Active Flood Advisory';
    if (alertDesc) alertDesc.textContent = tabInfo.alert.split('.').slice(1).join('.') || 'Stay tuned to official updates.';

    // Render SVG Polyline
    if (polylineEl && tabInfo.values) {
      const vals = tabInfo.values;
      const maxVal = Math.max(...vals, tabInfo.danger_threshold) * 1.15;
      const minVal = Math.min(...vals) * 0.85;
      const width = 500;
      const height = 180;
      const padding = 20;

      const points = vals.map((v, i) => {
        const x = Math.round((i / (vals.length - 1)) * (width - 2 * padding) + padding);
        const norm = (v - minVal) / (maxVal - minVal || 1);
        const y = Math.round(height - padding - norm * (height - 2 * padding));
        return `${x},${y}`;
      }).join(' ');

      polylineEl.setAttribute('points', points);
    }

    // Render Times
    if (timesEl && tabInfo.times) {
      timesEl.innerHTML = tabInfo.times.map((t) => `<span>${t}</span>`).join('');
    }
  }

  const tabsContainer = document.getElementById('analyticsTabs');
  if (tabsContainer) {
    tabsContainer.addEventListener('click', (e) => {
      const btn = e.target.closest('button');
      if (!btn) return;
      tabsContainer.querySelectorAll('button').forEach((b) => b.classList.remove('selected'));
      btn.classList.add('selected');
      const tabKey = btn.dataset.tab;
      renderAnalyticsTab(tabKey);
    });
  }

  // ----------------- Live Flood Risk Map (Leaflet Integration) -----------------
  let homeMap = null;
  let homeMarkersLayer = null;
  let homeRiskLayer = null;

  function initHomeMap() {
    const mapEl = document.getElementById('mapViewContainer');
    if (!mapEl || typeof L === 'undefined') return;

    // Clear fake background elements to render clean Leaflet tiles
    mapEl.innerHTML = '';
    mapEl.style.background = '#e2e8f0';

    homeMap = L.map('mapViewContainer', {
      center: [18.5204, 73.8567],
      zoom: 13,
      zoomControl: true
    });

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19,
      attribution: '© <a href="https://openstreetmap.org" target="_blank">OpenStreetMap</a>'
    }).addTo(homeMap);

    homeRiskLayer = L.layerGroup().addTo(homeMap);
    homeMarkersLayer = L.layerGroup().addTo(homeMap);
  }

  async function fetchMapData(filterKeyword = '') {
    try {
      const res = await fetch(`${API_BASE}/api/map-data`);
      if (!res.ok) return;
      const data = await res.json();
      renderMapPoints(data.points, data.risk_zones || [], filterKeyword);
    } catch (err) {
      console.warn('Could not fetch map data:', err);
    }
  }

  function renderMapPoints(points, riskZones = [], filterKeyword = '') {
    if (!homeMap || !homeMarkersLayer) return;

    homeMarkersLayer.clearLayers();
    if (homeRiskLayer) homeRiskLayer.clearLayers();

    // Render flood risk zones
    if (riskZones && !filterKeyword && homeRiskLayer) {
      riskZones.forEach((zone) => {
        const color = zone.risk === 'high' ? '#ef4444' : zone.risk === 'moderate' ? '#f59e0b' : '#38bdf8';
        L.circle([zone.lat, zone.lng], {
          color: color,
          fillColor: color,
          fillOpacity: 0.18,
          radius: zone.radius_m || 800,
          weight: 1.5
        }).bindPopup(`<b>${zone.name}</b><br>Flood Risk Zone: <span style="font-weight:bold; color:${color};">${zone.risk.toUpperCase()}</span>`).addTo(homeRiskLayer);
      });
    }

    // Render incident & resource markers
    points.forEach((pt) => {
      if (filterKeyword) {
        const matchTitle = pt.title && pt.title.toLowerCase().includes(filterKeyword.toLowerCase());
        const matchType = pt.type && pt.type.toLowerCase().includes(filterKeyword.toLowerCase());
        const matchNeed = pt.need_type && pt.need_type.toLowerCase().includes(filterKeyword.toLowerCase());
        if (!matchTitle && !matchType && !matchNeed) return;
      }

      let iconHtml = '';
      let markerClass = '';
      if (pt.type === 'incident') {
        const bg = pt.urgency === 'critical' ? '#ef4444' : pt.urgency === 'high' ? '#f97316' : '#eab308';
        iconHtml = `<div style="width:28px;height:28px;background:${bg};color:white;border-radius:50%;border:2px solid white;display:grid;place-items:center;font-weight:800;font-size:14px;box-shadow:0 3px 10px rgba(0,0,0,0.4);cursor:pointer;">${pt.urgency === 'critical' ? '!' : '●'}</div>`;
        markerClass = 'incident-marker';
      } else {
        const symbol = pt.resource_type === 'rescue' ? '⛵' : pt.resource_type === 'medical' ? '✚' : pt.resource_type === 'shelter' ? '⌂' : '🍱';
        const bg = pt.resource_type === 'rescue' ? '#0284c7' : pt.resource_type === 'medical' ? '#ef4444' : pt.resource_type === 'shelter' ? '#0d9488' : '#16a34a';
        iconHtml = `<div style="width:30px;height:30px;background:${bg};color:white;border-radius:7px;border:2px solid white;display:grid;place-items:center;font-size:15px;box-shadow:0 3px 10px rgba(0,0,0,0.35);cursor:pointer;">${symbol}</div>`;
        markerClass = 'resource-marker';
      }

      const customIcon = L.divIcon({
        className: markerClass,
        html: iconHtml,
        iconSize: [30, 30],
        iconAnchor: [15, 15]
      });

      const marker = L.marker([pt.lat, pt.lng], { icon: customIcon });

      const popupHtml = `
        <div style="font-family:Inter,sans-serif; min-width:180px; padding:2px;">
          <h4 style="margin:0 0 4px; font-size:13px; color:#0f172a;">${escapeHtml(pt.title)}</h4>
          <p style="margin:0 0 6px; font-size:11px; color:#475569; line-height:1.35;">${escapeHtml(pt.description || pt.location || 'Municipal Rescue Asset')}</p>
          <div style="font-size:10px; font-weight:700; text-transform:uppercase; color:#0284c7;">
            ${pt.type === 'incident' ? `Status: ${pt.status} • Urgency: ${pt.urgency}` : `Type: ${pt.resource_type} • Status: ${pt.available ? 'Available' : 'Assigned'}`}
          </div>
        </div>
      `;

      marker.bindPopup(popupHtml);
      homeMarkersLayer.addLayer(marker);
    });
  }

  const btnSearchMap = document.getElementById('btnSearchMap');
  const mapSearchInput = document.getElementById('mapSearchInput');
  const btnRefreshMap = document.getElementById('btnRefreshMap');

  if (btnSearchMap && mapSearchInput) {
    const doSearch = () => {
      const q = mapSearchInput.value.trim();
      fetchMapData(q);
      if (q && homeMap) {
        showToast(`Filtered map by: "${q}"`);
      }
    };
    btnSearchMap.onclick = doSearch;
    mapSearchInput.addEventListener('keydown', (e) => { if (e.key === 'Enter') doSearch(); });
  }

  if (btnRefreshMap) {
    btnRefreshMap.onclick = () => {
      fetchMapData();
      showToast('Live map refreshed with real-time updates.');
    };
  }

  // ----------------- Live Command Center Modal -----------------
  const ccModal = document.getElementById('commandCenterModal');
  const btnOpenCC = document.getElementById('btnOpenCommandCenter');
  const closeCC = document.getElementById('closeCommandCenter');
  const ccList = document.getElementById('commandCenterList');
  const ccFilters = document.getElementById('ccFilters');
  let currentCCFilter = 'all';

  if (btnOpenCC && ccModal) {
    btnOpenCC.onclick = () => {
      ccModal.classList.add('show');
      loadCommandCenterData();
    };
  }

  if (closeCC && ccModal) {
    closeCC.onclick = () => ccModal.classList.remove('show');
  }

  async function loadCommandCenterData() {
    if (!ccList) return;
    ccList.innerHTML = '<div style="text-align:center; padding:30px; color:#64748b;">Loading active incident feed…</div>';

    try {
      const [repRes, rscRes] = await Promise.all([
        fetch(`${API_BASE}/api/reports`),
        fetch(`${API_BASE}/api/resources`)
      ]);

      cachedReports = await repRes.json();
      cachedResources = await rscRes.json();

      renderCommandCenterFeed();
    } catch (err) {
      console.error(err);
      ccList.innerHTML = '<div style="text-align:center; padding:30px; color:#ef303d;">Failed to load incident feed from server.</div>';
    }
  }

  function renderCommandCenterFeed() {
    if (!ccList) return;
    ccList.innerHTML = '';

    const filtered = cachedReports.filter((rep) => {
      if (currentCCFilter === 'all') return true;
      if (currentCCFilter === 'critical') return rep.urgency === 'critical';
      if (currentCCFilter === 'high') return rep.urgency === 'high';
      return rep.need_type === currentCCFilter;
    });

    if (filtered.length === 0) {
      ccList.innerHTML = '<div style="text-align:center; padding:40px; color:#64748b;">No active incidents found in this view.</div>';
      return;
    }

    filtered.forEach((rep) => {
      const item = document.createElement('div');
      item.className = 'incident-item';

      const urg = (rep.urgency || 'medium').toLowerCase();
      const isAssigned = rep.status === 'assigned';
      const isResolved = rep.status === 'resolved';

      item.innerHTML = `
        <div style="display:flex; flex-direction:column; gap:6px;">
          <span class="urgency-tag urgency-${urg}">${urg}</span>
          <span style="font-size:10px; text-align:center; color:#64748b; text-transform:uppercase; font-weight:700;">${rep.need_type}</span>
        </div>
        <div class="incident-details">
          <h4>${escapeHtml(rep.location)}</h4>
          <p>${escapeHtml(rep.description)}</p>
          <small><b>AI Triage:</b> ${escapeHtml(rep.reasoning || 'Standard triage queue.')}</small>
          ${rep.photo_url ? `<div style="margin-top:4px;"><a href="${API_BASE}${rep.photo_url}" target="_blank" style="font-size:11px; color:#0284c7; text-decoration:none; font-weight:600;">📷 View Attached Photo ↗</a></div>` : ''}
          ${rep.assigned_resource ? `<small style="color:#059669; font-weight:600;">Assigned: ${escapeHtml(rep.assigned_resource.name)}</small>` : ''}
          <div style="margin-top:5px;"><a href="status.html?id=${rep.id}" target="_blank" style="font-size:11px; color:#0284c7; text-decoration:none; font-weight:700;">🔍 View Live Status Page ↗</a></div>
        </div>
        <div class="incident-actions">
          ${!isAssigned && !isResolved ? `
            <button class="btn-action-assign" data-id="${rep.id}">⚡ Assign Best Team</button>
          ` : ''}
          ${!isResolved ? `
            <button class="btn-action-resolve" data-id="${rep.id}">✓ Mark Resolved</button>
          ` : `
            <span style="font-size:11px; color:#10b981; font-weight:700; text-align:center;">✓ Resolved</span>
          `}
        </div>
      `;

      ccList.appendChild(item);
    });

    // Wire assignment buttons
    ccList.querySelectorAll('.btn-action-assign').forEach((btn) => {
      btn.onclick = async () => {
        const id = btn.dataset.id;
        btn.disabled = true;
        btn.textContent = 'Assigning...';

        // Pick nearest or first available rescue resource
        const candidate = cachedResources.find((r) => r.available) || cachedResources[0];
        if (!candidate) {
          showToast('No available resources in inventory.');
          btn.disabled = false;
          return;
        }

        const formData = new FormData();
        formData.append('resource_id', candidate.id);

        try {
          const res = await fetch(`${API_BASE}/api/reports/${id}/assign`, {
            method: 'POST',
            body: formData
          });
          if (res.ok) {
            showToast(`Assigned ${candidate.name} to incident.`);
            loadCommandCenterData();
            fetchStats();
            fetchMapData();
          }
        } catch (e) {
          console.error(e);
        }
      };
    });

    // Wire resolve buttons
    ccList.querySelectorAll('.btn-action-resolve').forEach((btn) => {
      btn.onclick = async () => {
        const id = btn.dataset.id;
        btn.disabled = true;
        btn.textContent = 'Resolving...';
        try {
          const res = await fetch(`${API_BASE}/api/reports/${id}/resolve`, { method: 'POST' });
          if (res.ok) {
            showToast('Incident marked as safely resolved.');
            loadCommandCenterData();
            fetchStats();
            fetchMapData();
          }
        } catch (e) {
          console.error(e);
        }
      };
    });
  }

  if (ccFilters) {
    ccFilters.addEventListener('click', (e) => {
      const btn = e.target.closest('button');
      if (!btn) return;
      ccFilters.querySelectorAll('button').forEach((b) => b.classList.remove('active'));
      btn.classList.add('active');
      currentCCFilter = btn.dataset.filter;
      renderCommandCenterFeed();
    });
  }

  function escapeHtml(str) {
    if (!str) return '';
    return str.replace(/[&<>"']/g, (m) => ({
      '&': '&amp;',
      '<': '&lt;',
      '>': '&gt;',
      '"': '&quot;',
      "'": '&#39;'
    }[m]));
  }

  // ----------------- Initial Load -----------------
  initHomeMap();
  fetchStats();
  fetchAnalytics();
  fetchMapData();

  // Auto-refresh stats every 30 seconds
  setInterval(fetchStats, 30000);
});