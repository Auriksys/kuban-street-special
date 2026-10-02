/**
 * KubanStreetSpecial - Krasnodar Krai Interactive Touge & Drag Map
 * Zero-API-key fail-proof Leaflet engine with Dark Matter, Satellite & OSM layers,
 * custom glowing neon pins, interactive coordinate inspector, deep links into Yandex Maps & Navigator,
 * and Live Temporary Markers (20-49 min TTL) with instant creation, removal, and real-time countdown.
 */

let kssMap = null;
let kssMarkersMap = {};
let kssMarkersGroup = null;
let kssTempMarkersGroup = null;
let kssTempMarkersMap = {};
let kssTempMarkersData = [];
let kssClickMarker = null;
let kssTimerTicker = null;

function initSpotsMap(spots) {
  const mapContainer = document.getElementById('spots-yandex-map');
  if (!mapContainer) return;

  // Check if Leaflet is loaded. If not, retry after a short delay
  if (typeof L === 'undefined') {
    console.warn('Leaflet is loading...');
    setTimeout(() => initSpotsMap(spots), 200);
    return;
  }

  // If already initialized, re-render markers and update size
  if (kssMap) {
    renderMapMarkers(spots);
    loadLiveMarkers();
    setTimeout(() => kssMap.invalidateSize(), 100);
    return;
  }

  try {
    // 1. Initialize Map centered on Krasnodar Krai
    kssMap = L.map('spots-yandex-map', {
      center: [44.75, 38.9],
      zoom: 8,
      zoomControl: true,
      attributionControl: false
    });

    window.kssMap = kssMap;

    // 2. Base Tile Layers
    const darkLayer = L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
      maxZoom: 19,
      subdomains: 'abcd',
      attribution: '&copy; CartoDB &copy; OpenStreetMap'
    });

    const satLayer = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{x}/{y}', {
      maxZoom: 19,
      attribution: '&copy; Esri World Imagery'
    });

    const osmLayer = L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19,
      attribution: '&copy; OpenStreetMap'
    });

    // Default to Dark Matter
    darkLayer.addTo(kssMap);

    // 3. Layer Control (Спутник / Ночь / Улицы)
    const baseLayers = {
      "🌃 KSS Ночная (Dark)": darkLayer,
      "🛰️ Спутник HD": satLayer,
      "🗺️ Улицы и дороги": osmLayer
    };
    L.control.layers(baseLayers, null, { position: 'topright' }).addTo(kssMap);

    // 4. Groups for spot markers and live temporary markers
    kssMarkersGroup = L.layerGroup().addTo(kssMap);
    kssTempMarkersGroup = L.layerGroup().addTo(kssMap);

    // 5. Interactive Coordinate Inspector on Map Click
    kssMap.on('click', function(e) {
      const lat = Number(e.latlng.lat).toFixed(5);
      const lng = Number(e.latlng.lng).toFixed(5);

      if (kssClickMarker) {
        kssMap.removeLayer(kssClickMarker);
      }

      const clickIcon = L.divIcon({
        className: 'custom-click-pin-wrapper',
        html: `
          <div class="click-pulse-pin" style="
            display: flex;
            align-items: center;
            justify-content: center;
            width: 20px;
            height: 20px;
            background: #d6ff00;
            border-radius: 50%;
            border: 3px solid #000;
            box-shadow: 0 0 15px #d6ff00, 0 0 30px #d6ff00;
          "></div>
        `,
        iconSize: [20, 20],
        iconAnchor: [10, 10]
      });

      kssClickMarker = L.marker([lat, lng], { icon: clickIcon }).addTo(kssMap);

      const coordBadge = document.getElementById('selected-coord-badge');
      if (coordBadge) {
        coordBadge.innerHTML = `
          <div class="flex items-center gap-2 flex-wrap">
            <span>📍 Выбрана точка: <b class="text-lime-400 font-mono text-sm">${lat}, ${lng}</b></span>
            <span class="text-[11px] text-gray-400 bg-white/5 px-2 py-0.5 rounded border border-white/10">Скопировано в буфер 📋</span>
          </div>
          <div class="flex items-center gap-2 flex-wrap">
            <button onclick="openAddMarkerModal(${lat}, ${lng})" class="px-3 py-1 bg-red-600 hover:bg-red-500 text-white font-bold text-xs rounded transition-colors shadow flex items-center gap-1">
              <span>🚨</span> <span>Поставить метку здесь</span>
            </button>
            <a href="https://yandex.ru/maps/?pt=${lng},${lat}&z=16&l=map" target="_blank" class="px-2.5 py-1 bg-yellow-400 text-black font-bold text-xs rounded hover:bg-yellow-300 transition-colors shadow-sm">
              Яндекс.Карты ↗
            </a>
            <a href="https://yandex.ru/maps/?rtext=~${lat},${lng}&rtt=auto" target="_blank" class="px-2.5 py-1 bg-lime-400 text-black font-bold text-xs rounded hover:bg-lime-300 transition-colors shadow-sm">
              Навигатор 🚗
            </a>
          </div>
        `;
      }

      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(`${lat}, ${lng}`).catch(() => {});
      }

      if (typeof showToast === 'function') {
        showToast(`📍 Координаты [${lat}, ${lng}] скопированы!`, 'cyan');
      }
    });

    // 6. Observe visibility to auto-invalidate size
    setupMapResizeObserver(mapContainer);

    // 7. Render initial spots & live temporary markers
    renderMapMarkers(spots);
    loadLiveMarkers();

    // 8. Background Polling & Real-Time Second Ticker
    if (kssTimerTicker) clearInterval(kssTimerTicker);
    kssTimerTicker = setInterval(updateLiveMarkersTimers, 1000);
    setInterval(loadLiveMarkers, 25000);

  } catch (err) {
    console.error('Failed to initialize map:', err);
  }
}

function setupMapResizeObserver(container) {
  if (window.ResizeObserver) {
    const ro = new ResizeObserver(() => {
      if (kssMap) kssMap.invalidateSize();
    });
    ro.observe(container);
  }
  window.addEventListener('resize', () => {
    if (kssMap) kssMap.invalidateSize();
  });
}

// -------------------------------------------------------------
// STATIC SPOTS RENDERING
// -------------------------------------------------------------

function renderMapMarkers(spots) {
  if (!kssMap || !kssMarkersGroup || !Array.isArray(spots) || spots.length === 0) return;

  kssMarkersGroup.clearLayers();
  kssMarkersMap = {};

  const bounds = [];

  spots.forEach(spot => {
    if (!spot.lat || !spot.lng) return;

    let pinColor = '#d6ff00';
    let pinEmoji = '🏁';
    let pinGlow = 'rgba(214, 255, 0, 0.7)';

    if (spot.type === 'Тоге') {
      pinColor = '#ff2a55';
      pinEmoji = '⛰️';
      pinGlow = 'rgba(255, 42, 85, 0.7)';
    } else if (spot.type === 'Ролл-он') {
      pinColor = '#00f0ff';
      pinEmoji = '⚡';
      pinGlow = 'rgba(0, 240, 255, 0.7)';
    }

    const customPin = L.divIcon({
      className: 'kss-map-marker-pin',
      html: `
        <div style="
          width: 36px;
          height: 36px;
          background: #080a10;
          border: 2px solid ${pinColor};
          border-radius: 50% 50% 50% 0;
          transform: rotate(-45deg);
          box-shadow: 0 0 16px ${pinGlow}, 0 4px 12px rgba(0,0,0,0.8);
          display: flex;
          align-items: center;
          justify-content: center;
          cursor: pointer;
        ">
          <span style="
            transform: rotate(45deg);
            font-size: 16px;
            line-height: 1;
          ">${pinEmoji}</span>
        </div>
      `,
      iconSize: [36, 36],
      iconAnchor: [18, 36],
      popupAnchor: [0, -36]
    });

    const stars = '⭐'.repeat(spot.difficulty || 3);
    const dangerColor = (spot.danger_level || '').includes('Высокая') ? '#ff2a55' : '#d6ff00';
    const fallbackImg = 'https://images.unsplash.com/photo-1568605117036-5fe5e7bab0b7?w=800';

    const popupContent = `
      <div style="width: 290px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0c0e17; color: #fff; border-radius: 16px; overflow: hidden; border: 1px solid rgba(255,255,255,0.15); box-shadow: 0 20px 40px rgba(0,0,0,0.9);">
        <div style="position: relative; height: 125px; background: #000; overflow: hidden;">
          <img src="${spot.image_url || fallbackImg}" alt="${spot.name}" style="width: 100%; height: 100%; object-fit: cover;" onerror="this.src='${fallbackImg}'">
          <div style="position: absolute; inset: 0; background: linear-gradient(to top, #0c0e17 0%, transparent 60%);"></div>
          <div style="position: absolute; top: 8px; left: 8px; background: ${pinColor}; color: #000; font-size: 10px; font-weight: 900; padding: 2px 8px; border-radius: 6px; text-transform: uppercase;">
            ${spot.type}
          </div>
          <div style="position: absolute; bottom: 6px; left: 10px; right: 10px;">
            <div style="font-size: 15px; font-weight: 900; color: #fff; text-shadow: 0 2px 6px rgba(0,0,0,0.8);">${spot.name}</div>
          </div>
        </div>

        <div style="padding: 12px 14px 14px 14px;">
          <div style="font-size: 11px; color: #9ca3af; margin-bottom: 6px;">📍 ${spot.city} • ${spot.region || 'Краснодарский край'}</div>

          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 6px; font-size: 11px; background: rgba(255,255,255,0.03); padding: 8px; border-radius: 8px; border: 1px solid rgba(255,255,255,0.06); margin-bottom: 8px;">
            <div>Дистанция: <b style="color: #fff;">${spot.length_km || 0} км</b></div>
            <div>Перепад: <b style="color: #fff;">+${spot.elevation_gain_m || 0} м</b></div>
            <div>Сложность: <b style="color: #facc15;">${stars}</b></div>
            <div>ДПС: <b style="color: ${dangerColor};">${spot.danger_level || 'Низкая'}</b></div>
          </div>

          <div style="font-size: 11px; color: #aaa; font-family: monospace; margin-bottom: 10px; background: rgba(0,0,0,0.4); padding: 5px 8px; border-radius: 6px; border: 1px solid rgba(255,255,255,0.05); display: flex; justify-content: space-between;">
            <span>GPS:</span>
            <b style="color: #d6ff00;">${Number(spot.lat).toFixed(5)}, ${Number(spot.lng).toFixed(5)}</b>
          </div>

          <div style="display: flex; gap: 6px; flex-direction: column;">
            <div style="display: flex; gap: 6px;">
              <a href="https://yandex.ru/maps/?pt=${spot.lng},${spot.lat}&z=16&l=map" target="_blank" style="flex: 1; text-align: center; background: #ffcc00; color: #000; font-weight: 800; font-size: 11px; padding: 7px 6px; border-radius: 8px; text-decoration: none; display: flex; align-items: center; justify-content: center; gap: 4px;">
                <span>Яндекс.Карты</span> <span>↗</span>
              </a>
              <a href="https://yandex.ru/maps/?rtext=~${spot.lat},${spot.lng}&rtt=auto" target="_blank" style="flex: 1; text-align: center; background: #3b82f6; color: #fff; font-weight: 800; font-size: 11px; padding: 7px 6px; border-radius: 8px; text-decoration: none; display: flex; align-items: center; justify-content: center; gap: 4px;">
                <span>Навигатор</span> <span>🚗</span>
              </a>
            </div>
            <button onclick="selectSpotForBattle(${spot.id})" style="width: 100%; background: #d6ff00; color: #000; font-weight: 800; font-size: 11px; padding: 8px; border-radius: 8px; border: none; cursor: pointer; transition: opacity 0.2s;">
              + Вписать заезд на споте
            </button>
          </div>
        </div>
      </div>
    `;

    const marker = L.marker([spot.lat, spot.lng], { icon: customPin });
    marker.bindPopup(popupContent, { maxWidth: 320, className: 'kss-leaflet-popup' });
    kssMarkersGroup.addLayer(marker);
    kssMarkersMap[spot.id] = marker;

    bounds.push([spot.lat, spot.lng]);
  });

  if (bounds.length > 0 && kssMap) {
    kssMap.fitBounds(bounds, { padding: [50, 50], maxZoom: 11 });
  }
}

function flyToSpot(lat, lng, spotId) {
  if (kssMap) {
    kssMap.flyTo([lat, lng], 14, { duration: 1.2 });
    const mapEl = document.getElementById('spots-yandex-map');
    if (mapEl) {
      window.scrollTo({ top: mapEl.offsetTop - 80, behavior: 'smooth' });
    }

    setTimeout(() => {
      if (kssMarkersMap[spotId]) {
        kssMarkersMap[spotId].openPopup();
      }
    }, 1250);
  }
}

function selectSpotForBattle(spotId) {
  openModal('battle-register-modal');
  const sel = document.getElementById('battle-spot-id');
  if (sel) sel.value = spotId;
}

function renderSpotsList(filterType = null) {
  const container = document.getElementById('spots-cards-list');
  if (!container) return;

  let spots = KSS.spots || [];
  if (filterType && filterType !== 'ALL') {
    spots = spots.filter(s => s.type === filterType);
  }

  if (spots.length === 0) {
    container.innerHTML = `
      <div class="col-span-full py-16 text-center text-gray-500 font-mono">
        <div class="text-5xl mb-3">⛰️</div>
        <p class="text-xl text-gray-200 font-bold font-race">СПОТЫ ПОКА НЕ ДОБАВЛЕНЫ</p>
        <p class="text-xs text-gray-400 mt-2 max-w-md mx-auto">Администратор опубликует перевалы и прямики края через программу управления.</p>
      </div>
    `;
    return;
  }

  container.innerHTML = spots.map(s => {
    const stars = '⭐'.repeat(s.difficulty || 3);
    const badgeColor = s.type === 'Тоге' ? 'badge-red' : (s.type === 'Дрэг' ? 'badge-volt' : 'badge-cyan');

    return `
      <div class="kss-card p-4 space-y-3 cursor-pointer group" onclick="flyToSpot(${s.lat}, ${s.lng}, ${s.id})">
        <div class="relative h-36 rounded-lg overflow-hidden bg-gray-900">
          <img src="${s.image_url}" alt="${s.name}" class="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105" onerror="this.src='https://images.unsplash.com/photo-1568605117036-5fe5e7bab0b7?w=800'">
          <div class="absolute inset-0 bg-gradient-to-t from-black via-black/30 to-transparent"></div>
          <div class="absolute top-2 left-2 flex gap-1">
            <span class="kss-badge ${badgeColor}">${s.type}</span>
          </div>
          <div class="absolute bottom-2 left-3 right-3">
            <h4 class="text-base font-bold text-white font-race">${s.name}</h4>
            <p class="text-xs text-gray-300">📍 ${s.city} • ${s.region || 'Краснодарский край'}</p>
          </div>
        </div>

        <div class="space-y-1.5 text-xs">
          <div class="flex justify-between text-gray-400">
            <span>Координаты:</span>
            <span class="text-lime-400 font-mono font-bold">${Number(s.lat).toFixed(4)}, ${Number(s.lng).toFixed(4)}</span>
          </div>
          <div class="flex justify-between text-gray-400">
            <span>Протяженность:</span>
            <span class="text-white font-mono font-bold">${s.length_km} км</span>
          </div>
          <div class="flex justify-between text-gray-400">
            <span>Перепад высоты:</span>
            <span class="text-white font-mono font-bold">+${s.elevation_gain_m} м</span>
          </div>
          <div class="flex justify-between text-gray-400">
            <span>Сложность:</span>
            <span class="text-yellow-400">${stars}</span>
          </div>
          <div class="flex justify-between text-gray-400">
            <span>Опасность:</span>
            <span class="${(s.danger_level || '').includes('Высокая') ? 'text-red-400 font-bold' : 'text-lime-400'}">${s.danger_level}</span>
          </div>
        </div>

        <p class="text-xs text-gray-400 line-clamp-2 italic">«${s.safety_notes || s.description || 'Соблюдайте безопасность при ночных заездах'}»</p>

        <div class="pt-2 border-t border-white/5 flex items-center justify-between">
          <span class="text-[11px] text-gray-500 font-mono">Сбор: ${s.recommended_time || '23:00'}</span>
          <span class="text-lime-400 text-xs font-race font-bold group-hover:translate-x-1 transition-transform inline-flex items-center gap-1">
            ПОКАЗАТЬ НА КАРТЕ 🎯
          </span>
        </div>
      </div>
    `;
  }).join('');
}


// =============================================================
// LIVE TEMPORARY MARKERS ENGINE (20-49 MINUTES TTL)
// =============================================================

function formatRemainingTime(seconds) {
  if (seconds <= 0) return 'Истекла';
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${m}м ${s < 10 ? '0' : ''}${s}с`;
}

async function loadLiveMarkers() {
  try {
    const res = await api('/api/markers');
    if (res && res.status === 'ok') {
      kssTempMarkersData = res.markers || [];
      renderTempMapMarkers();
      renderLiveMarkersFeed();
      updateLiveMarkersCount();
    }
  } catch (err) {
    console.warn("Could not load live markers:", err);
  }
}

function updateLiveMarkersCount() {
  const badge = document.getElementById('live-markers-count');
  if (badge) {
    const count = kssTempMarkersData.length;
    badge.innerText = `${count} ${count === 1 ? 'активная метка' : (count >= 2 && count <= 4 ? 'активные метки' : 'активных меток')}`;
  }
}

function getCategoryConfig(cat) {
  switch (cat) {
    case 'ДПС':
      return {
        color: '#ff1f4b',
        beaconClass: 'marker-beacon-red',
        icon: '🚨',
        title: 'Засада ДПС / Радар',
        badgeClass: 'badge-red'
      };
    case 'Сходка':
      return {
        color: '#d6ff00',
        beaconClass: 'marker-beacon-lime',
        icon: '🏁',
        title: 'Сходка / Уличный заезд',
        badgeClass: 'badge-volt'
      };
    case 'Опасность':
      return {
        color: '#f59e0b',
        beaconClass: 'marker-beacon-amber',
        icon: '⚠️',
        title: 'Опасность на дороге',
        badgeClass: 'bg-amber-500/20 text-amber-300 border-amber-500/40'
      };
    default:
      return {
        color: '#00f0ff',
        beaconClass: 'marker-beacon-cyan',
        icon: '💬',
        title: 'Сообщение пилота',
        badgeClass: 'badge-cyan'
      };
  }
}

function renderTempMapMarkers() {
  if (!kssMap || !kssTempMarkersGroup) return;

  kssTempMarkersGroup.clearLayers();
  kssTempMarkersMap = {};

  kssTempMarkersData.forEach(m => {
    const cfg = getCategoryConfig(m.category);
    const minLeft = Math.ceil(m.remaining_seconds / 60);

    const pinIcon = L.divIcon({
      className: 'kss-live-marker-wrapper',
      html: `
        <div style="position: relative; width: 40px; height: 40px;">
          <div class="${cfg.beaconClass}" style="
            width: 38px;
            height: 38px;
            background: #080a10;
            border: 2.5px solid ${cfg.color};
            border-radius: 50% 50% 50% 0;
            transform: rotate(-45deg);
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            box-shadow: 0 4px 15px rgba(0,0,0,0.9);
          ">
            <span style="
              transform: rotate(45deg);
              font-size: 17px;
              line-height: 1;
            ">${cfg.icon}</span>
          </div>
          <div class="marker-time-badge" style="background: ${cfg.color}; color: #000;">
            ${minLeft}м
          </div>
        </div>
      `,
      iconSize: [40, 40],
      iconAnchor: [20, 40],
      popupAnchor: [0, -40]
    });

    const popupHtml = `
      <div style="width: 280px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0c0e17; color: #fff; border-radius: 14px; overflow: hidden; border: 1px solid ${cfg.color}; box-shadow: 0 20px 40px rgba(0,0,0,0.95); padding: 14px;">
        <div style="display: flex; align-items: center; justify-content: space-between; border-bottom: 1px solid rgba(255,255,255,0.1); pb-2; margin-bottom: 10px;">
          <div style="display: flex; align-items: center; gap: 6px;">
            <span style="font-size: 18px;">${cfg.icon}</span>
            <b style="color: ${cfg.color}; font-size: 13px; font-weight: 800; text-transform: uppercase;">${cfg.title}</b>
          </div>
        </div>

        <div style="margin-bottom: 10px; background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.07); padding: 10px; border-radius: 10px; font-size: 13px; line-height: 1.4; color: #f3f4f6;">
          «${m.message}»
        </div>

        <div style="font-size: 11px; color: #9ca3af; margin-bottom: 6px; display: flex; justify-content: space-between;">
          <span>Пилот: <b style="color: #fff;">${m.callsign}</b></span>
          <span style="color: #6b7280;">${new Date(m.created_at).toLocaleTimeString('ru-RU', {hour: '2-digit', minute:'2-digit'})}</span>
        </div>

        <div style="font-size: 11px; margin-bottom: 10px; background: rgba(0,0,0,0.4); padding: 6px 8px; border-radius: 6px; border: 1px solid rgba(255,255,255,0.06); display: flex; justify-content: space-between; align-items: center;">
          <span style="color: #9ca3af;">⏳ Осталось:</span>
          <b id="popup-timer-${m.id}" style="color: #d6ff00; font-family: monospace; font-size: 12px;">${formatRemainingTime(m.remaining_seconds)}</b>
        </div>

        ${m.photo_url ? `
          <div style="margin-bottom: 8px; border-radius: 8px; overflow: hidden; max-height: 140px; border: 1px solid rgba(255,255,255,0.15);">
            <img src="${m.photo_url}" style="width: 100%; height: 100%; object-fit: cover; cursor: pointer;" onclick="window.open('${m.photo_url}', '_blank')">
          </div>
        ` : ''}

        <!-- Waze-style Community Verification -->
        <div style="display: flex; gap: 6px; margin-bottom: 8px;">
          <button onclick="confirmMarker(${m.id})" style="flex: 1; background: rgba(214, 255, 0, 0.12); border: 1px solid rgba(214, 255, 0, 0.4); color: #d6ff00; font-weight: 800; font-size: 10px; padding: 6px 4px; border-radius: 6px; cursor: pointer;">
            ⚠️ Подтверждаю (<span id="confirm-count-${m.id}">${m.confirmations || 1}</span>)
          </button>
          <button onclick="voteClearMarker(${m.id})" style="flex: 1; background: rgba(52, 211, 153, 0.12); border: 1px solid rgba(52, 211, 153, 0.4); color: #34d399; font-weight: 800; font-size: 10px; padding: 6px 4px; border-radius: 6px; cursor: pointer;">
            ✅ Чисто (${m.clear_votes || 0}/2)
          </button>
        </div>

        <div style="display: flex; gap: 6px; margin-bottom: 8px;">
          <a href="https://yandex.ru/maps/?pt=${m.lng},${m.lat}&z=16&l=map" target="_blank" style="flex: 1; text-align: center; background: #ffcc00; color: #000; font-weight: 800; font-size: 10px; padding: 6px; border-radius: 6px; text-decoration: none;">
            Яндекс.Карты ↗
          </a>
          <a href="https://yandex.ru/maps/?rtext=~${m.lat},${m.lng}&rtt=auto" target="_blank" style="flex: 1; text-align: center; background: #3b82f6; color: #fff; font-weight: 800; font-size: 10px; padding: 6px; border-radius: 6px; text-decoration: none;">
            Навигатор 🚗
          </a>
        </div>

        <button onclick="removeLiveMarker(${m.id})" style="width: 100%; background: rgba(239, 68, 68, 0.12); border: 1px solid rgba(239, 68, 68, 0.35); color: #f87171; font-weight: 800; font-size: 10px; padding: 6px; border-radius: 6px; cursor: pointer; transition: background 0.2s;">
          🗑️ УДАЛИТЬ МЕТКУ
        </button>
      </div>
    `;

    const marker = L.marker([m.lat, m.lng], { icon: pinIcon });
    marker.bindPopup(popupHtml, { maxWidth: 310, className: 'kss-leaflet-popup' });
    kssTempMarkersGroup.addLayer(marker);
    kssTempMarkersMap[m.id] = marker;
  });
}

function renderLiveMarkersFeed() {
  const container = document.getElementById('live-markers-container');
  if (!container) return;

  if (kssTempMarkersData.length === 0) {
    container.innerHTML = `
      <div class="col-span-full py-6 text-center text-gray-500 font-mono text-xs">
        <span>🛣️ На дорогах края спокойно. Нажмите <b>«+ Поставить метку»</b>, если заметили ДПС, камеру или заезд!</span>
      </div>
    `;
    return;
  }

  container.innerHTML = kssTempMarkersData.map(m => {
    const cfg = getCategoryConfig(m.category);
    return `
      <div class="bg-black/60 border border-white/10 rounded-xl p-3 space-y-2.5 hover:border-lime-400/40 transition-colors">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-1.5">
            <span class="text-base">${cfg.icon}</span>
            <span class="text-xs font-bold font-race text-white">${cfg.title}</span>
          </div>
          <span id="feed-timer-${m.id}" class="text-[11px] font-mono text-lime-400 font-bold bg-white/5 px-2 py-0.5 rounded">
            ⏳ ${formatRemainingTime(m.remaining_seconds)}
          </span>
        </div>

        <p class="text-xs text-gray-200 line-clamp-2 italic">«${m.message}»</p>

        ${m.photo_url ? `
          <div class="rounded-lg overflow-hidden border border-white/10 max-h-28 bg-black">
            <img src="${m.photo_url}" class="w-full h-full object-cover cursor-pointer hover:scale-105 transition-transform" onclick="window.open('${m.photo_url}', '_blank')">
          </div>
        ` : ''}

        <!-- Waze Confirmation / Clear Buttons -->
        <div class="grid grid-cols-2 gap-2 pt-1">
          <button onclick="confirmMarker(${m.id})" class="text-[10px] font-mono font-bold bg-lime-400/10 hover:bg-lime-400/20 border border-lime-400/30 text-lime-400 py-1 px-1.5 rounded transition-colors text-center truncate">
            ⚠️ Подтверждаю (<span id="feed-confirm-count-${m.id}">${m.confirmations || 1}</span>)
          </button>
          <button onclick="voteClearMarker(${m.id})" class="text-[10px] font-mono font-bold bg-emerald-500/10 hover:bg-emerald-500/20 border border-emerald-500/30 text-emerald-400 py-1 px-1.5 rounded transition-colors text-center truncate">
            ✅ Чисто (${m.clear_votes || 0}/2)
          </button>
        </div>

        <div class="flex items-center justify-between pt-1 border-t border-white/5 text-[11px] text-gray-400 font-mono">
          <span>Пилот: <b class="text-white">${m.callsign}</b></span>
          <div class="flex gap-2">
            <button onclick="flyToLiveMarker(${m.lat}, ${m.lng}, ${m.id})" class="text-lime-400 hover:underline font-bold">
              На карте 🎯
            </button>
            <button onclick="removeLiveMarker(${m.id})" class="text-red-400 hover:text-red-300">
              🗑️
            </button>
          </div>
        </div>
      </div>
    `;
  }).join('');
}

function flyToLiveMarker(lat, lng, id) {
  if (kssMap) {
    kssMap.flyTo([lat, lng], 15, { duration: 1 });
    const mapEl = document.getElementById('spots-yandex-map');
    if (mapEl) {
      window.scrollTo({ top: mapEl.offsetTop - 80, behavior: 'smooth' });
    }
    setTimeout(() => {
      if (kssTempMarkersMap[id]) {
        kssTempMarkersMap[id].openPopup();
      }
    }, 1100);
  }
}

function updateLiveMarkersTimers() {
  let hasExpired = false;

  for (let i = kssTempMarkersData.length - 1; i >= 0; i--) {
    const m = kssTempMarkersData[i];
    m.remaining_seconds = Math.max(0, (m.remaining_seconds || 0) - 1);

    const timeStr = formatRemainingTime(m.remaining_seconds);

    // Update inside popup if open
    const popTimer = document.getElementById(`popup-timer-${m.id}`);
    if (popTimer) popTimer.innerText = timeStr;

    // Update in feed
    const feedTimer = document.getElementById(`feed-timer-${m.id}`);
    if (feedTimer) feedTimer.innerText = `⏳ ${timeStr}`;

    if (m.remaining_seconds <= 0) {
      hasExpired = true;
      kssTempMarkersData.splice(i, 1);
    }
  }

  if (hasExpired) {
    renderTempMapMarkers();
    renderLiveMarkersFeed();
    updateLiveMarkersCount();
  }
}

// -------------------------------------------------------------
// MODAL: CREATE & REMOVE TEMPORARY MARKERS
// -------------------------------------------------------------

function openAddMarkerModal(lat = null, lng = null) {
  const inputLat = document.getElementById('marker-input-lat');
  const inputLng = document.getElementById('marker-input-lng');
  const inputMsg = document.getElementById('marker-input-msg');
  const inputDuration = document.getElementById('marker-input-duration');
  const durationDisplay = document.getElementById('marker-duration-display');

  if (lat && lng) {
    if (inputLat) inputLat.value = Number(lat).toFixed(5);
    if (inputLng) inputLng.value = Number(lng).toFixed(5);
  } else if (kssMap) {
    const center = kssMap.getCenter();
    if (inputLat) inputLat.value = center.lat.toFixed(5);
    if (inputLng) inputLng.value = center.lng.toFixed(5);
  } else {
    if (inputLat) inputLat.value = '45.03550';
    if (inputLng) inputLng.value = '38.97530';
  }

  if (inputMsg) inputMsg.value = '';
  if (inputDuration) inputDuration.value = 30;
  if (durationDisplay) durationDisplay.innerText = '30 минут';

  openModal('add-marker-modal');
}

function setMarkerDuration(minutes) {
  const inputDuration = document.getElementById('marker-input-duration');
  const durationDisplay = document.getElementById('marker-duration-display');
  const val = Math.min(49, Math.max(20, parseInt(minutes)));
  if (inputDuration) inputDuration.value = val;
  if (durationDisplay) durationDisplay.innerText = `${val} минут`;
}

function onDurationSliderChange(val) {
  const durationDisplay = document.getElementById('marker-duration-display');
  if (durationDisplay) durationDisplay.innerText = `${val} минут`;
}

async function submitAddMarker() {
  const cat = document.getElementById('marker-input-cat')?.value || 'ДПС';
  const msg = document.getElementById('marker-input-msg')?.value.trim();
  const lat = parseFloat(document.getElementById('marker-input-lat')?.value);
  const lng = parseFloat(document.getElementById('marker-input-lng')?.value);
  const duration = parseInt(document.getElementById('marker-input-duration')?.value || 30);

  if (!msg) {
    showToast('Введите текст сообщения для метки!', 'red');
    return;
  }
  if (isNaN(lat) || isNaN(lng)) {
    showToast('Укажите корректные координаты!', 'red');
    return;
  }

  const u = KSS.currentUser || { id: 1, callsign: 'Пилот' };

  const payload = {
    user_id: u.id,
    callsign: u.callsign,
    category: cat,
    message: msg,
    lat: lat,
    lng: lng,
    duration_minutes: duration,
    photo_url: document.getElementById('marker-input-photo')?.value.trim() || null
  };

  try {
    const res = await api('/api/markers', {
      method: 'POST',
      body: JSON.stringify(payload)
    });

    if (res && res.status === 'ok') {
      closeModal('add-marker-modal');
      showToast(`Метка «${cat}» установлена на ${duration} минут! 🚨`, 'volt');
      await loadLiveMarkers();
      flyToLiveMarker(lat, lng, res.marker.id);
    }
  } catch (err) {
    console.error('Failed to add marker:', err);
  }
}

async function removeLiveMarker(markerId) {
  if (!confirm('Удалить эту метку с карты?')) return;

  try {
    const res = await api(`/api/markers/${markerId}`, { method: 'DELETE' });
    if (res && res.status === 'ok') {
      kssTempMarkersData = kssTempMarkersData.filter(m => m.id !== markerId);
      renderTempMapMarkers();
      renderLiveMarkersFeed();
      updateLiveMarkersCount();
      showToast('Метка удалена с карты 🗑️', 'cyan');
    }
  } catch (err) {
    console.error('Failed to delete marker:', err);
  }
}

async function confirmMarker(markerId) {
  try {
    const res = await api('/api/markers/confirm', {
      method: 'POST',
      body: JSON.stringify({ marker_id: markerId })
    });
    if (res && res.status === 'ok') {
      const marker = kssTempMarkersData.find(m => m.id === markerId);
      if (marker) {
        marker.confirmations = res.confirmations;
        const c1 = document.getElementById(`confirm-count-${markerId}`);
        const c2 = document.getElementById(`feed-confirm-count-${markerId}`);
        if (c1) c1.innerText = res.confirmations;
        if (c2) c2.innerText = res.confirmations;
      }
      showToast(`⚠️ Обстановка подтверждена пилотом! (+${res.confirmations})`, 'volt');
    }
  } catch (e) {
    console.error('Failed to confirm marker:', e);
  }
}

async function voteClearMarker(markerId) {
  try {
    const res = await api('/api/markers/clear', {
      method: 'POST',
      body: JSON.stringify({ marker_id: markerId })
    });
    if (res && res.status === 'ok') {
      if (res.deleted) {
        kssTempMarkersData = kssTempMarkersData.filter(m => m.id !== markerId);
        renderTempMapMarkers();
        renderLiveMarkersFeed();
        updateLiveMarkersCount();
        showToast('✅ Метка снята: чистота трассы подтверждена пилотами!', 'cyan');
      } else {
        const marker = kssTempMarkersData.find(m => m.id === markerId);
        if (marker) {
          marker.clear_votes = res.clear_votes;
        }
        renderTempMapMarkers();
        renderLiveMarkersFeed();
        showToast(`Голос «Чисто» принят: еще 1 подтверждение, и метка снимется (${res.clear_votes}/2)`, 'cyan');
      }
    }
  } catch (e) {
    console.error('Failed to clear marker:', e);
  }
}

// Global exports
window.initSpotsMap = initSpotsMap;
window.renderMapMarkers = renderMapMarkers;
window.renderSpotsList = renderSpotsList;
window.flyToSpot = flyToSpot;
window.selectSpotForBattle = selectSpotForBattle;
window.loadLiveMarkers = loadLiveMarkers;
window.openAddMarkerModal = openAddMarkerModal;
window.setMarkerDuration = setMarkerDuration;
window.onDurationSliderChange = onDurationSliderChange;
window.submitAddMarker = submitAddMarker;
window.removeLiveMarker = removeLiveMarker;
window.confirmMarker = confirmMarker;
window.voteClearMarker = voteClearMarker;
window.flyToLiveMarker = flyToLiveMarker;

// Spot Filter Buttons
document.addEventListener('DOMContentLoaded', () => {
  const spotFilterBtns = document.querySelectorAll('[data-spot-filter]');
  spotFilterBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      spotFilterBtns.forEach(b => b.classList.remove('active', 'border-lime-400', 'text-lime-400'));
      btn.classList.add('active', 'border-lime-400', 'text-lime-400');
      const filter = btn.dataset.spotFilter;
      renderSpotsList(filter);
    });
  });
});
