/**
 * KubanStreetSpecial - Core Application Logic
 * State Management, Routing, API Client, and UI Helpers
 */

const API_BASE = window.location.origin;

// Global App State
const KSS = {
  currentUser: {
    id: 1,
    username: "marko_krd",
    callsign: "Красный_Чайзер",
    name: "Марк Осипов",
    city: "Краснодар",
    avatar: "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150",
    street_cred: 1480,
    wins: 24,
    losses: 5,
    team_tag: "KMS",
    team_name: "Kuban Midnight Syndicate",
    primary_car_id: 1
  },
  cars: [],
  spots: [],
  battles: [],
  pilots: [],
  teams: [],
  news: [],
  stats: {},
  currentTab: 'radar'
};

// Sound Effects Engine (Web Audio API)
let sfxEnabled = localStorage.getItem('kss_sfx') === 'true';
let audioCtx = null;

function playSfx(type = 'click') {
  if (!sfxEnabled) return;
  try {
    if (!audioCtx) audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    if (audioCtx.state === 'suspended') audioCtx.resume();

    const osc = audioCtx.createOscillator();
    const gain = audioCtx.createGain();
    osc.connect(gain);
    gain.connect(audioCtx.destination);

    if (type === 'click') {
      osc.type = 'sine';
      osc.frequency.setValueAtTime(800, audioCtx.currentTime);
      osc.frequency.exponentialRampToValueAtTime(400, audioCtx.currentTime + 0.05);
      gain.gain.setValueAtTime(0.08, audioCtx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + 0.05);
      osc.start();
      osc.stop(audioCtx.currentTime + 0.05);
    } else if (type === 'rev') {
      osc.type = 'sawtooth';
      osc.frequency.setValueAtTime(110, audioCtx.currentTime);
      osc.frequency.exponentialRampToValueAtTime(360, audioCtx.currentTime + 0.4);
      osc.frequency.exponentialRampToValueAtTime(140, audioCtx.currentTime + 0.8);
      gain.gain.setValueAtTime(0.1, audioCtx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + 0.8);
      osc.start();
      osc.stop(audioCtx.currentTime + 0.8);
    } else if (type === 'launch') {
      osc.type = 'triangle';
      osc.frequency.setValueAtTime(440, audioCtx.currentTime);
      osc.frequency.exponentialRampToValueAtTime(880, audioCtx.currentTime + 0.3);
      gain.gain.setValueAtTime(0.12, audioCtx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + 0.3);
      osc.start();
      osc.stop(audioCtx.currentTime + 0.3);
    }
  } catch (e) {}
}
window.playSfx = playSfx;

function toggleSfx() {
  sfxEnabled = !sfxEnabled;
  localStorage.setItem('kss_sfx', sfxEnabled ? 'true' : 'false');
  updateSfxButton();
  if (sfxEnabled) playSfx('click');
  showToast(sfxEnabled ? 'Звуковые эффекты включены 🔊' : 'Звук отключен 🔇', 'cyan');
}

function updateSfxButton() {
  const btn = document.getElementById('btn-sound-toggle');
  if (btn) {
    btn.innerHTML = sfxEnabled ? '🔊 SFX: ON' : '🔇 SFX: OFF';
    if (sfxEnabled) btn.classList.add('active');
    else btn.classList.remove('active');
  }
}

// API Fetch Helper
async function api(endpoint, options = {}) {
  try {
    const res = await fetch(`${API_BASE}${endpoint}`, {
      headers: {
        'Content-Type': 'application/json',
        ...(options.headers || {})
      },
      ...options
    });
    if (!res.ok) {
      let errMsg = `HTTP error ${res.status}`;
      try {
        const err = await res.json();
        if (err && err.error) errMsg = err.error;
      } catch (e) {
        try {
          const txt = await res.text();
          if (txt) errMsg = txt.slice(0, 100);
        } catch (_) {}
      }
      throw new Error(errMsg);
    }
    return await res.json();
  } catch (error) {
    console.error(`API Error on ${endpoint}:`, error);
    showToast(error.message || 'Ошибка соединения с сервером', 'red');
    throw error;
  }
}

// Toast Notifications
function showToast(message, type = 'volt') {
  const container = document.getElementById('toast-container');
  if (!container) return;

  const toast = document.createElement('div');
  toast.className = `kss-toast border-l-4 ${type === 'red' ? 'border-red-500' : (type === 'cyan' ? 'border-cyan-400' : 'border-lime-400')}`;
  
  const icon = type === 'red' ? '⚠️' : (type === 'cyan' ? '⚡' : '🏁');
  toast.innerHTML = `<span>${icon}</span> <span>${message}</span>`;
  
  container.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(50px)';
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

// Modal Controller
function openModal(modalId) {
  if (window.playSfx) window.playSfx('click');
  const modal = document.getElementById(modalId);
  if (modal) {
    modal.classList.add('open');
    document.body.style.overflow = 'hidden';
  }
}

function closeModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) {
    modal.classList.remove('open');
    document.body.style.overflow = '';
  }
}

// Sidebar Drawer Controls
function toggleSidebar() {
  if (window.playSfx) window.playSfx('click');
  const sidebar = document.getElementById('kss-sidebar');
  const backdrop = document.getElementById('sidebar-backdrop');
  if (sidebar) sidebar.classList.toggle('open');
  if (backdrop) backdrop.classList.toggle('open');
}

function closeSidebar() {
  const sidebar = document.getElementById('kss-sidebar');
  const backdrop = document.getElementById('sidebar-backdrop');
  if (sidebar) sidebar.classList.remove('open');
  if (backdrop) backdrop.classList.remove('open');
}

window.toggleSidebar = toggleSidebar;
window.closeSidebar = closeSidebar;

// Tab Switching
function switchTab(tabName) {
  if (window.playSfx) window.playSfx('click');
  KSS.currentTab = tabName;

  // Close sidebar drawer
  closeSidebar();

  // Update current view title in header
  const titleMap = {
    'radar': '⚡ Обзор платформы KSS',
    'garage': '🏎️ Реестр боевой техники',
    'spots': '🛰️ Дорожный радар & Споты',
    'battles': '⚔️ Протокол заездов и побед',
    'simulator': '🎮 Дуэль-калькулятор',
    'teams': '👥 Синдикаты Кубани',
    'leaderboard': '🏆 Таблица славы пилотов',
    'news': '📰 Новости и сводки',
    'bot': '✈️ Telegram-бот @Kuban_Streetbot',
    'chat': '💬 Эфир пилотов & Форум',
    'profile': '🪪 Цифровая лицензия пилота'
  };
  const titleEl = document.getElementById('current-view-title');
  if (titleEl && titleMap[tabName]) {
    titleEl.innerText = titleMap[tabName];
  }

  // Update nav link states
  document.querySelectorAll('.nav-link, .mobile-nav-btn, .sidebar-nav-link, .workspace-nav-pill').forEach(btn => {
    if (btn.dataset.tab === tabName) {
      btn.classList.add('active');
    } else {
      btn.classList.remove('active');
    }
  });

  // Show target section, hide others
  document.querySelectorAll('.tab-section').forEach(section => {
    if (section.id === `section-${tabName}`) {
      section.classList.remove('hidden');
    } else {
      section.classList.add('hidden');
    }
  });

  // Re-trigger map resize when switching to spots tab
  if (tabName === 'spots') {
    setTimeout(() => {
      if (window.kssMap) window.kssMap.invalidateSize();
      if (window.kssYandexMap && window.kssYandexMap.container) window.kssYandexMap.container.fitToViewport();
    }, 100);
    setTimeout(() => {
      if (window.kssMap) window.kssMap.invalidateSize();
    }, 350);
  }

  // If switching to chat, initialize and scroll to bottom
  if (tabName === 'chat' && typeof initChat === 'function') {
    initChat();
  }

  // If switching to profile, render fresh profile data
  if (tabName === 'profile' && typeof renderProfilePage === 'function') {
    renderProfilePage();
  }

  window.scrollTo({ top: 0, behavior: 'smooth' });
}


// Initial Data Load
async function loadInitialData() {
  // 1. Stats
  try {
    const statsData = await api('/api/stats');
    if (statsData.status === 'ok') {
      KSS.stats = statsData.stats;
      renderStats();
    }
  } catch (e) {
    console.warn('Stats load notice:', e);
  }

  // 2. Cars
  try {
    const carsData = await api('/api/cars');
    if (carsData.status === 'ok') {
      KSS.cars = carsData.cars;
      renderGarage();
      populateCarSelectors();
    }
  } catch (e) {
    console.warn('Cars load notice:', e);
  }

  // 3. Spots
  try {
    const spotsData = await api('/api/spots');
    if (spotsData.status === 'ok') {
      KSS.spots = spotsData.spots;
      renderSpotsList();
      if (typeof initSpotsMap === 'function') {
        initSpotsMap(KSS.spots);
      }
    }
  } catch (e) {
    console.warn('Spots load notice:', e);
  }

  // 4. Battles
  try {
    const battlesData = await api('/api/battles');
    if (battlesData.status === 'ok') {
      KSS.battles = battlesData.battles;
      renderBattlesFeed();
    }
  } catch (e) {
    console.warn('Battles load notice:', e);
  }

  // 5. Pilots
  try {
    const pilotsData = await api('/api/pilots');
    if (pilotsData.status === 'ok') {
      KSS.pilots = pilotsData.pilots;
      renderLeaderboard();
    }
  } catch (e) {
    console.warn('Pilots load notice:', e);
  }

  // 6. Teams
  try {
    const teamsData = await api('/api/teams');
    if (teamsData.status === 'ok') {
      KSS.teams = teamsData.teams;
      renderTeams();
    }
  } catch (e) {
    console.warn('Teams load notice:', e);
  }

  // 7. News & Announcements
  try {
    const newsData = await api('/api/news');
    if (newsData && newsData.status === 'ok') {
      KSS.news = newsData.news;
      if (typeof renderNews === 'function') {
        renderNews();
      }
    }
  } catch (e) {
    console.warn('News loading notice:', e);
  }

  try {
    if (typeof renderProfilePage === 'function') {
      renderProfilePage();
    }
  } catch (e) {
    console.warn('Profile render notice:', e);
  }

  try {
    if (typeof initChat === 'function') {
      initChat();
    }
  } catch (e) {
    console.warn('Chat init notice:', e);
  }

  try {
    updateUserDisplay();
  } catch (e) {
    console.warn('User display notice:', e);
  }
}

// Render Stats Bar on Radar
function renderStats() {
  const s = KSS.stats;
  const countCars = document.getElementById('stat-cars-count');
  const countBattles = document.getElementById('stat-battles-count');
  const countSpots = document.getElementById('stat-spots-count');
  const kingCallsign = document.getElementById('stat-king-callsign');
  const kingScore = document.getElementById('stat-king-score');
  const dragRecord = document.getElementById('stat-drag-record');

  if (countCars) countCars.innerText = s.cars_registered || 0;
  if (countBattles) countBattles.innerText = s.battles_logged || 0;
  if (countSpots) countSpots.innerText = s.spots_active || 0;
  
  if (s.street_king && kingCallsign) {
    kingCallsign.innerText = s.street_king.callsign;
    kingScore.innerText = `${s.street_king.street_cred} PTS`;
  }

  if (s.record_quarter_mile && dragRecord) {
    dragRecord.innerText = `${s.record_quarter_mile.quarter_mile}s (${s.record_quarter_mile.make} ${s.record_quarter_mile.model})`;
  }
}

function updateUserDisplay() {
  const u = KSS.currentUser;
  if (!u) return;

  const userNameEl = document.getElementById('user-header-callsign');
  const userCredEl = document.getElementById('user-header-cred');
  const userAvatarEl = document.getElementById('user-header-avatar');

  if (userNameEl) userNameEl.innerText = u.callsign || u.name;
  if (userCredEl) userCredEl.innerText = `${u.street_cred || 1000} PTS`;
  if (userAvatarEl && u.avatar) userAvatarEl.src = u.avatar;

  // Sidebar User Information
  const sideNameEl = document.getElementById('sidebar-user-callsign');
  const sideCredEl = document.getElementById('sidebar-user-cred');
  const sideCityEl = document.getElementById('sidebar-user-city');
  const sideAvatarEl = document.getElementById('sidebar-user-avatar');

  if (sideNameEl) sideNameEl.innerText = u.callsign || u.name;
  if (sideCredEl) sideCredEl.innerText = `${u.street_cred || 1000} PTS`;
  if (sideCityEl) sideCityEl.innerText = u.city || 'Краснодар';
  if (sideAvatarEl && u.avatar) sideAvatarEl.src = u.avatar;

  if (typeof renderProfileCard === 'function') {
    renderProfileCard();
  }
}


// Document Ready
document.addEventListener('DOMContentLoaded', () => {
  // Navigation Event Listeners
  document.querySelectorAll('[data-tab]').forEach(el => {
    el.addEventListener('click', (e) => {
      e.preventDefault();
      const tab = el.dataset.tab;
      switchTab(tab);
    });
  });

  // Modal close handlers (backdrop & close buttons)
  document.querySelectorAll('.kss-modal-overlay').forEach(modal => {
    modal.addEventListener('click', (e) => {
      if (e.target === modal) {
        modal.classList.remove('open');
        document.body.style.overflow = '';
      }
    });
  });

  document.querySelectorAll('[data-close-modal]').forEach(btn => {
    btn.addEventListener('click', () => {
      const modalId = btn.dataset.closeModal;
      closeModal(modalId);
    });
  });

  // Check session and Auth Gate
  if (typeof checkExistingSession === 'function') {
    checkExistingSession();
  }

  // Load backend data
  loadInitialData();
});

// =========================================================================
// WATCHDOG DIAGNOSTIC CONTROLLER
// =========================================================================
async function openWatchdogModal() {
  openModal('watchdog-modal');
  await refreshWatchdogStatus();
}

async function refreshWatchdogStatus() {
  const container = document.getElementById('watchdog-status-content');
  if (!container) return;

  try {
    const res = await api('/api/watchdog/status');
    const isOnline = res.status === 'online';
    const srvOnline = res.server_online !== false;
    const tunOnline = res.tunnel_online !== false;

    container.innerHTML = `
      <div class="grid grid-cols-2 gap-3 font-mono">
        <div class="p-3 bg-black/60 border border-white/10 rounded-xl space-y-1">
          <div class="text-[10px] text-gray-400">СЕРВЕР ЯДРА KSS</div>
          <div class="text-xs font-bold ${srvOnline ? 'text-lime-400' : 'text-red-400'} flex items-center gap-1.5">
            <span class="w-2 h-2 rounded-full ${srvOnline ? 'bg-lime-400 animate-pulse' : 'bg-red-500'}"></span>
            ${srvOnline ? '100% ОНЛАЙН' : 'СБОЙ'}
          </div>
        </div>

        <div class="p-3 bg-black/60 border border-white/10 rounded-xl space-y-1">
          <div class="text-[10px] text-gray-400">ВНЕШНИЙ ТУННЕЛЬ</div>
          <div class="text-xs font-bold ${tunOnline ? 'text-cyan-400' : 'text-yellow-400'} flex items-center gap-1.5">
            <span class="w-2 h-2 rounded-full ${tunOnline ? 'bg-cyan-400 animate-pulse' : 'bg-yellow-400'}"></span>
            ${tunOnline ? 'АКТИВЕН' : 'ПЕРЕПОДКЛЮЧЕНИЕ'}
          </div>
        </div>

        <div class="p-3 bg-black/60 border border-white/10 rounded-xl space-y-1">
          <div class="text-[10px] text-gray-400">UPTIME (НЕПРЕРЫВНО)</div>
          <div class="text-xs font-bold text-white">${res.uptime_human || 'Активен'}</div>
        </div>

        <div class="p-3 bg-black/60 border border-white/10 rounded-xl space-y-1">
          <div class="text-[10px] text-gray-400">ОТКЛИК (PING)</div>
          <div class="text-xs font-bold text-lime-400">${res.latency_ms || 1} ms</div>
        </div>
      </div>

      <div class="p-3 bg-black/70 border border-white/10 rounded-xl space-y-2 text-xs font-mono">
        <div class="flex justify-between items-center text-gray-400">
          <span>Служба контроля:</span>
          <span class="text-lime-300 font-bold">KSS Watchdog 24/7 Engine</span>
        </div>
        <div class="flex justify-between items-center text-gray-400">
          <span>Всего проверок:</span>
          <span class="text-white font-bold">${res.checks_total || 1}</span>
        </div>
        <div class="flex justify-between items-center text-gray-400">
          <span>Авто-восстановлений:</span>
          <span class="text-lime-400 font-bold">${res.recoveries_count || 0}</span>
        </div>
        <div class="flex justify-between items-center text-gray-400">
          <span>Публичный адрес:</span>
          <span class="text-cyan-300 font-bold truncate max-w-[200px]">${res.public_url || 'Локальный порт 8080'}</span>
        </div>
      </div>

      ${res.recent_logs && res.recent_logs.length ? `
        <div class="p-2.5 bg-black/90 border border-white/5 rounded-xl text-[10px] font-mono text-gray-400 space-y-1 max-h-24 overflow-y-auto">
          <div class="text-gray-500 font-bold">Журнал мониторинга:</div>
          ${res.recent_logs.map(l => `<div>${l}</div>`).join('')}
        </div>
      ` : ''}
    `;
  } catch (err) {
    container.innerHTML = `
      <div class="p-4 bg-red-500/10 border border-red-500/20 text-red-400 rounded-xl text-xs font-mono">
        Ошибка получения статуса: ${err.message}
      </div>
    `;
  }
}

window.openWatchdogModal = openWatchdogModal;
window.refreshWatchdogStatus = refreshWatchdogStatus;

// =========================================================================
// UNIVERSAL PHOTO & VIDEO UPLOADER
// =========================================================================
async function uploadFileToServer(file) {
  if (!file) throw new Error('Файл не выбран');

  const isVideo = file.type.startsWith('video/') || /\.(mp4|webm|mov|m4v)$/i.test(file.name);
  const isImage = file.type.startsWith('image/') || /\.(jpg|jpeg|png|webp|gif)$/i.test(file.name);

  if (!isVideo && !isImage) {
    throw new Error('Поддерживаются только фотографии (JPG, PNG, WEBP, GIF) и видео (MP4, WEBM, MOV)!');
  }

  const maxBytes = 50 * 1024 * 1024; // 50MB
  if (file.size > maxBytes) {
    throw new Error(`Файл превышает лимит 50 МБ (размер: ${(file.size / (1024 * 1024)).toFixed(1)} МБ).`);
  }

  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = async () => {
      try {
        const payload = {
          filename: file.name,
          data: reader.result,
          media_type: isVideo ? 'video' : 'image'
        };
        const res = await api('/api/upload', {
          method: 'POST',
          body: JSON.stringify(payload)
        });
        if (res && res.status === 'ok') {
          resolve(res);
        } else {
          reject(new Error(res.error || 'Ошибка сохранения на сервере'));
        }
      } catch (e) {
        reject(e);
      }
    };
    reader.onerror = () => reject(new Error('Не удалось прочитать файл с устройства'));
    reader.readAsDataURL(file);
  });
}

async function uploadGenericFile(fileInputEl, targetInputId, previewContainerId = null) {
  const file = fileInputEl.files && fileInputEl.files[0];
  if (!file) return;

  const targetInput = document.getElementById(targetInputId);
  const previewBox = previewContainerId ? document.getElementById(previewContainerId) : null;
  const previewName = previewContainerId ? document.getElementById(`${previewContainerId}-name`) : null;

  try {
    showToast(`Загрузка ${file.type.startsWith('video') ? 'видео' : 'фото'}... ⏳`, 'cyan');
    const res = await uploadFileToServer(file);
    if (res && res.url) {
      if (targetInput) {
        targetInput.value = res.url;
      }
      if (previewBox) {
        previewBox.classList.remove('hidden');
        if (previewName) {
          const icon = res.media_type === 'video' ? '🎥' : '📷';
          previewName.innerText = `${icon} ${res.filename} (${res.size_kb} KB)`;
        }
      }
      showToast(`${res.media_type === 'video' ? 'Видео' : 'Фото'} успешно загружено! ✅`, 'volt');
    }
  } catch (err) {
    console.error('File upload failed:', err);
    showToast(`Ошибка загрузки: ${err.message}`, 'red');
  } finally {
    fileInputEl.value = '';
  }
}

function clearGenericUpload(targetInputId, previewContainerId) {
  const targetInput = document.getElementById(targetInputId);
  if (targetInput) targetInput.value = '';
  const previewBox = document.getElementById(previewContainerId);
  if (previewBox) previewBox.classList.add('hidden');
}

window.uploadFileToServer = uploadFileToServer;
window.uploadGenericFile = uploadGenericFile;
window.clearGenericUpload = clearGenericUpload;

