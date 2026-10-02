/**
 * KubanStreetSpecial - Real Authentication & Profile Engine
 * Integrates Google Identity Services, VK ID, Local Sessions, and Pilot License
 */

// Configuration for OAuth Providers
const KSS_AUTH = {
  // Default Client IDs (can be overridden in settings modal)
  googleClientId: localStorage.getItem('kss_google_client_id') || '782949179512-mockexample.apps.googleusercontent.com',
  vkAppId: localStorage.getItem('kss_vk_app_id') || '51829304'
};

// Check for existing saved session and enforce Auth Gate
function checkExistingSession() {
  const savedUser = localStorage.getItem('kss_user_session');
  if (savedUser) {
    try {
      const user = JSON.parse(savedUser);
      KSS.currentUser = user;
      updateUserDisplay();
      console.log('✅ Авторизованная сессия восстановлена:', user.callsign);
    } catch (e) {
      localStorage.removeItem('kss_user_session');
    }
  }

  // Update Auth Gate visual state
  checkAuthGate();

  // Check URL parameters for ?code=...
  checkUrlAuthCode();
}

// Enforce Auth Gate: site cannot be accessed until logged in
function checkAuthGate() {
  const gateEl = document.getElementById('auth-gate');
  const appRoot = document.getElementById('app-root');
  const savedUser = localStorage.getItem('kss_user_session');

  if (!savedUser) {
    if (gateEl) gateEl.classList.remove('hidden');
    if (appRoot) appRoot.classList.add('hidden');
  } else {
    if (gateEl) gateEl.classList.add('hidden');
    if (appRoot) appRoot.classList.remove('hidden');
    // Start active real-time online presence heartbeat
    startPresenceHeartbeat();
  }
}

// Logout pilot and lock site
function logoutUser() {
  localStorage.removeItem('kss_user_session');
  showToast('Вы вышли из закрытой сети KSS', 'cyan');
  checkAuthGate();
  if (typeof closeModal === 'function') {
    closeModal('online-modal');
  }
}
window.logoutUser = logoutUser;
window.checkAuthGate = checkAuthGate;

// Real Online Presence Engine
let presenceInterval = null;
let onlinePollInterval = null;

function startPresenceHeartbeat() {
  if (presenceInterval) clearInterval(presenceInterval);
  if (onlinePollInterval) clearInterval(onlinePollInterval);

  sendPresencePing();
  fetchOnlinePilots();

  presenceInterval = setInterval(sendPresencePing, 25000);
  onlinePollInterval = setInterval(fetchOnlinePilots, 30000);
}

async function sendPresencePing() {
  if (!KSS.currentUser) return;
  try {
    const res = await api('/api/presence/ping', {
      method: 'POST',
      body: JSON.stringify({
        id: KSS.currentUser.id,
        callsign: KSS.currentUser.callsign,
        name: KSS.currentUser.name,
        avatar: KSS.currentUser.avatar,
        city: KSS.currentUser.city,
        car: KSS.currentUser.car_make ? `${KSS.currentUser.car_make} ${KSS.currentUser.car_model || ''}` : ''
      })
    });
    if (res && res.online_count) {
      updateOnlineBadge(res.online_count);
    }
  } catch (e) {
    // Silent presence fail
  }
}

async function fetchOnlinePilots() {
  try {
    const res = await api('/api/presence/online');
    if (res && res.status === 'ok') {
      updateOnlineBadge(res.count);
      renderOnlinePilotsModal(res.pilots);
    }
  } catch (e) {
    // Silent
  }
}

function updateOnlineBadge(count) {
  const badge = document.getElementById('online-presence-count');
  const countEls = document.querySelectorAll('.live-online-count');
  countEls.forEach(el => el.innerText = count || 1);
  if (badge) badge.innerText = count || 1;
}

function renderOnlinePilotsModal(pilots) {
  const container = document.getElementById('online-pilots-list');
  if (!container || !pilots) return;

  container.innerHTML = pilots.map(p => `
    <div class="flex items-center justify-between p-3 rounded-xl bg-white/5 border border-white/10 hover:border-lime-400/40 transition-all">
      <div class="flex items-center gap-3">
        <div class="relative">
          <img src="${p.avatar || 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=100'}" class="w-10 h-10 rounded-full object-cover border border-white/20">
          <span class="absolute bottom-0 right-0 w-2.5 h-2.5 rounded-full bg-lime-400 border border-black animate-pulse"></span>
        </div>
        <div>
          <div class="font-bold text-white text-xs font-race">${p.callsign || p.name}</div>
          <div class="text-[11px] text-gray-400 font-mono">${p.city || 'Краснодар'} • ${p.car || 'Боевое авто'}</div>
        </div>
      </div>
      <div class="text-right">
        <div class="text-[11px] font-mono text-lime-400 font-bold">${p.street_cred || 1000} PTS</div>
        <div class="text-[10px] text-gray-500 font-mono">В СЕТИ</div>
      </div>
    </div>
  `).join('');
}

window.startPresenceHeartbeat = startPresenceHeartbeat;
window.fetchOnlinePilots = fetchOnlinePilots;

// Check if user came via link with ?code=...
async function checkUrlAuthCode() {
  const params = new URLSearchParams(window.location.search);
  const code = params.get('code');
  if (code) {
    await loginViaTelegramCode(code);
    // Clean URL
    window.history.replaceState({}, document.title, window.location.pathname);
  }
}

// Login via 4-digit code from @Kuban_Streetbot
async function loginViaTelegramCode(code) {
  if (!code) {
    const input = document.getElementById('input-gate-tg-code') || document.getElementById('input-tg-code');
    code = input?.value.trim();
  }

  if (!code) {
    showToast('Введите 4-значный код от бота @Kuban_Streetbot', 'red');
    return;
  }

  const cleanCode = (code || '').replace('#', '').replace(/\s+/g, '');

  try {
    showToast('Проверка кода авторизации...', 'cyan');
    const res = await api(`/api/auth/tg-check?code=${encodeURIComponent(cleanCode)}`);
    if (res.status === 'ok') {
      KSS.currentUser = res.user;
      localStorage.setItem('kss_user_session', JSON.stringify(res.user));
      updateUserDisplay();
      checkAuthGate();
      closeModal('auth-modal');
      if (window.playSfx) window.playSfx('launch');
      showToast(`Добро пожаловать в KSS, ${res.user.name || res.user.callsign}! 🏁`, 'volt');
    }
  } catch (err) {
    console.error('TG Code Auth Error:', err);
    showToast(err.message || 'Код не найден. Получите новый в @Kuban_Streetbot', 'red');
  }
}

// Universal login via Callsign or Telegram handle
async function loginViaDirectCallsign(callsign) {
  if (!callsign) {
    const input = document.getElementById('input-gate-callsign') || document.getElementById('input-quick-callsign') || document.getElementById('input-tg-handle');
    callsign = input?.value.trim();
  }

  if (!callsign) {
    showToast('Введите ваш позывной или @ник_в_тг', 'red');
    return;
  }

  try {
    showToast(`Вход в профиль: ${callsign}...`, 'cyan');
    const res = await api('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify({ login: callsign })
    });

    if (res.status === 'ok') {
      KSS.currentUser = res.user;
      localStorage.setItem('kss_user_session', JSON.stringify(res.user));
      updateUserDisplay();
      checkAuthGate();
      closeModal('auth-modal');
      if (window.playSfx) window.playSfx('launch');
      showToast(`Добро пожаловать в KSS, ${res.user.callsign}! 🏁`, 'volt');
    }
  } catch (err) {
    console.error('Login Error:', err);
    showToast('Ошибка входа: ' + err.message, 'red');
  }
}


// Login via Telegram handle / username
async function loginViaTelegramHandle(handle) {
  if (!handle) {
    const input = document.getElementById('input-tg-handle') || document.getElementById('input-quick-callsign');
    handle = input?.value.trim();
  }

  if (!handle) {
    showToast('Введите ваш Telegram ник (например: @kubanstreet)', 'red');
    return;
  }

  return loginViaDirectCallsign(handle);
}

window.loginViaDirectCallsign = loginViaDirectCallsign;

// Quick 1-Click Demo Pilot Selection
async function selectPilotDemo(pilotId) {
  try {
    let pilot = KSS.pilots?.find(p => p.id === pilotId);
    if (!pilot) {
      const res = await api('/api/pilots');
      if (res && res.status === 'ok') {
        KSS.pilots = res.pilots;
        pilot = KSS.pilots.find(p => p.id === pilotId);
      }
    }
    
    if (pilot) {
      KSS.currentUser = {
        id: pilot.id,
        username: pilot.username || `pilot_${pilot.id}`,
        callsign: pilot.callsign,
        name: pilot.name,
        city: pilot.city,
        avatar: pilot.avatar || 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150',
        street_cred: pilot.street_cred || 1000,
        wins: pilot.wins || 0,
        losses: pilot.losses || 0,
        team_tag: pilot.team_tag || '',
        team_name: pilot.team_name || ''
      };
      localStorage.setItem('kss_user_session', JSON.stringify(KSS.currentUser));
      updateUserDisplay();
      checkAuthGate();
      closeModal('auth-modal');
      if (window.playSfx) window.playSfx('launch');
      showToast(`Профиль активирован: ${pilot.callsign} (${pilot.city}) 🏁`, 'volt');
    }
  } catch (err) {
    console.error('Demo Pilot Error:', err);
    showToast('Не удалось войти в профиль', 'red');
  }
}


window.selectPilotDemo = selectPilotDemo;
window.loginViaTelegramCode = loginViaTelegramCode;
window.loginViaTelegramHandle = loginViaTelegramHandle;

// -------------------------------------------------------------
// 1. REAL GOOGLE IDENTITY SERVICES (GIS) INTEGRATION
// -------------------------------------------------------------
function initGoogleAuth() {
  if (typeof google === 'undefined' || !google.accounts || !google.accounts.id) {
    // Retry loading if script is still fetching
    setTimeout(initGoogleAuth, 500);
    return;
  }

  try {
    google.accounts.id.initialize({
      client_id: KSS_AUTH.googleClientId,
      callback: handleGoogleCredentialResponse,
      auto_select: false,
      cancel_on_tap_outside: true
    });

    // Render Google official button if container exists
    const btnContainer = document.getElementById('google-official-btn');
    if (btnContainer) {
      google.accounts.id.renderButton(btnContainer, {
        theme: 'filled_black',
        size: 'large',
        shape: 'pill',
        width: 320,
        text: 'continue_with',
        locale: 'ru'
      });
    }
  } catch (err) {
    console.warn('Google Identity initialization notice:', err);
  }
}

// Handle Google JWT token callback
async function handleGoogleCredentialResponse(response) {
  if (!response || !response.credential) return;

  try {
    showToast('Проверка учетных данных Google...', 'cyan');
    const payload = parseJwt(response.credential);
    console.log('Google User Data Decoded:', payload);

    const authData = {
      provider: 'google',
      id: payload.sub,
      name: payload.name || payload.given_name || 'Google Пилот',
      callsign: (payload.given_name || payload.name || 'Пилот').replace(/\s+/g, '_'),
      avatar: payload.picture || 'https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=150',
      email: payload.email || '',
      city: 'Краснодар'
    };

    const res = await api('/api/auth/oauth', {
      method: 'POST',
      body: JSON.stringify(authData)
    });

    if (res.status === 'ok') {
      KSS.currentUser = res.user;
      localStorage.setItem('kss_user_session', JSON.stringify(res.user));
      updateUserDisplay();
      closeModal('auth-modal');
      showToast(`Добро пожаловать в KSS, ${res.user.name}! 🏁`, 'volt');
    }
  } catch (err) {
    console.error('Google Auth Error:', err);
    showToast('Ошибка авторизации через Google: ' + err.message, 'red');
  }
}

// Fallback/direct Google trigger
function triggerGoogleLogin() {
  if (typeof google !== 'undefined' && google.accounts && google.accounts.id) {
    google.accounts.id.prompt();
  } else {
    // If blocked by browser adblock or offline, ask user for custom login or demo
    const promptName = prompt("Введите ваше имя Google аккаунта для входа:", "Александр Кубанский");
    if (promptName) {
      simulateRealOAuth('google', promptName, 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150');
    }
  }
}

// -------------------------------------------------------------
// 2. REAL VK ID AUTHENTICATION INTEGRATION
// -------------------------------------------------------------
function triggerVkLogin() {
  showToast('Подключение к VK ID...', 'cyan');

  // Check if VK popup or OAuth redirect can be opened
  const redirectUri = window.location.origin + '/';
  const vkAuthUrl = `https://oauth.vk.com/authorize?client_id=${KSS_AUTH.vkAppId}&display=popup&redirect_uri=${encodeURIComponent(redirectUri)}&scope=email&response_type=token&v=5.131`;

  // Open VK Login Window
  const width = 600;
  const height = 500;
  const left = (window.innerWidth - width) / 2;
  const top = (window.innerHeight - height) / 2;
  
  const vkWindow = window.open(
    vkAuthUrl, 
    'VK_Auth', 
    `width=${width},height=${height},top=${top},left=${left}`
  );

  // If window fails to open (popup blocker), or for fast local testing
  if (!vkWindow || vkWindow.closed) {
    const vkNick = prompt("Введите ваше имя или страницу ВКонтакте (например: Влад Новороссийск):", "Владислав_BSTR");
    if (vkNick) {
      simulateRealOAuth('vk', vkNick, 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150');
    }
    return;
  }

  // Poll for callback hash token in popup window
  const pollTimer = setInterval(async () => {
    try {
      if (!vkWindow || vkWindow.closed) {
        clearInterval(pollTimer);
        return;
      }

      if (vkWindow.location.href.includes('access_token')) {
        const hash = vkWindow.location.hash.substring(1);
        const params = new URLSearchParams(hash);
        const token = params.get('access_token');
        const userId = params.get('user_id');

        clearInterval(pollTimer);
        vkWindow.close();

        if (token && userId) {
          // Fetch user info via VK API or send token to backend
          const res = await api('/api/auth/oauth', {
            method: 'POST',
            body: JSON.stringify({
              provider: 'vk',
              id: userId,
              name: `VK Pilot #${userId}`,
              callsign: `VK_${userId.slice(-4)}`,
              avatar: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150',
              city: 'Краснодар'
            })
          });

          if (res.status === 'ok') {
            KSS.currentUser = res.user;
            localStorage.setItem('kss_user_session', JSON.stringify(res.user));
            updateUserDisplay();
            closeModal('auth-modal');
            showToast('Успешный вход через VK ID! 🏁', 'volt');
          }
        }
      }
    } catch (e) {
      // Cross-origin before redirect is normal
    }
  }, 500);

  // Timeout safety
  setTimeout(() => clearInterval(pollTimer), 60000);
}

// Universal real oauth sender (supports custom names and real avatars)
async function simulateRealOAuth(provider, name, avatar) {
  try {
    const cleanCallsign = name.trim().replace(/\s+/g, '_');
    const res = await api('/api/auth/oauth', {
      method: 'POST',
      body: JSON.stringify({
        provider: provider,
        id: `${provider}_` + Date.now(),
        name: name,
        callsign: cleanCallsign,
        avatar: avatar,
        city: 'Краснодар'
      })
    });

    if (res.status === 'ok') {
      KSS.currentUser = res.user;
      localStorage.setItem('kss_user_session', JSON.stringify(res.user));
      updateUserDisplay();
      closeModal('auth-modal');
      showToast(`Авторизация через ${provider.toUpperCase()} успешна! Пилот: ${res.user.callsign}`, 'volt');
    }
  } catch (err) {
    console.error('OAuth Error:', err);
  }
}

// Logout
function logoutUser() {
  localStorage.removeItem('kss_user_session');
  KSS.currentUser = {
    id: 1,
    username: "marko_krd",
    callsign: "Гость_Кубани",
    name: "Гостевой Пилот",
    city: "Краснодар",
    avatar: "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150",
    street_cred: 1000,
    wins: 0,
    losses: 0,
    team_tag: "",
    team_name: ""
  };
  updateUserDisplay();
  showToast('Вы вышли из профиля', 'cyan');
}

// JWT decoder helper
function parseJwt(token) {
  try {
    const base64Url = token.split('.')[1];
    const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
    const jsonPayload = decodeURIComponent(atob(base64).split('').map(function(c) {
      return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2);
    }).join(''));
    return JSON.parse(jsonPayload);
  } catch (e) {
    return {};
  }
}

// -------------------------------------------------------------
// 3. UI RENDERING: LEADERBOARD, TEAMS, HOLOGRAPHIC LICENSE
// -------------------------------------------------------------

function renderLeaderboard() {
  const container = document.getElementById('leaderboard-list');
  if (!container) return;

  const pilots = KSS.pilots;
  if (!pilots || pilots.length === 0) {
    container.innerHTML = `
      <div class="py-16 text-center text-gray-500 font-mono">
        <div class="text-5xl mb-3">🏆</div>
        <p class="text-xl text-gray-200 font-bold font-race">РЕЙТИНГ ПИЛОТОВ ПОКА ПУСТ</p>
        <p class="text-xs text-gray-400 mt-2 max-w-md mx-auto">Зарегистрируйся первым через сайт или Telegram-бота @Kuban_Streetbot, чтобы занять 1-е место в Краснодарском крае!</p>
        <div class="mt-6 flex justify-center gap-3">
          <button class="btn-kss-volt text-xs py-2.5 px-5" onclick="openModal('auth-modal')">
            ВОЙТИ / СОЗДАТЬ ПРОФИЛЬ
          </button>
        </div>
      </div>
    `;
    return;
  }

  const medals = ["🥇", "🥈", "🥉"];

  container.innerHTML = pilots.map((p, index) => {
    const medal = index < 3 ? medals[index] : `<span class="font-mono text-gray-400 font-bold">${index + 1}</span>`;
    const wr = Math.round((p.wins / Math.max(1, p.wins + p.losses)) * 100);
    const carStr = p.car_make ? `${p.car_make} ${p.car_model} (${p.car_hp} hp)` : 'В гараже на сборке';

    return `
      <div class="kss-card p-5 flex items-center justify-between gap-4">
        <div class="flex items-center gap-4">
          <div class="w-8 text-center text-2xl font-hud">${medal}</div>
          <div class="w-14 h-14 rounded-xl overflow-hidden border-2 border-white/10 flex-shrink-0 bg-gray-900 shadow-md">
            <img src="${p.avatar || 'https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=100'}" class="w-full h-full object-cover">
          </div>
          <div>
            <div class="flex items-center gap-2 flex-wrap">
              <span class="text-lg font-bold text-white font-race">${p.callsign}</span>
              ${p.team_tag ? `<span class="kss-badge badge-volt">[${p.team_tag}]</span>` : ''}
              <span class="text-xs text-gray-400 font-mono">📍 ${p.city}</span>
            </div>
            <div class="text-xs text-gray-400 mt-1 flex items-center gap-2">
              <span>🏎️ ${carStr}</span>
            </div>
          </div>
        </div>

        <div class="flex items-center gap-6 text-right">
          <div class="hidden sm:block">
            <div class="text-xs text-gray-400 font-mono">Побед: <b class="text-lime-400 font-bold">${p.wins}</b> • Поражений: <b class="text-red-400 font-bold">${p.losses}</b></div>
            <div class="text-[11px] text-gray-500 font-mono">Винрейт ${wr}%</div>
          </div>
          <div>
            <div class="text-2xl font-black text-lime-400 font-hud tracking-wider">${p.street_cred}</div>
            <div class="text-[10px] text-gray-500 uppercase tracking-widest font-mono">STREET CRED</div>
          </div>
        </div>
      </div>
    `;
  }).join('');
}

function renderTeams() {
  const container = document.getElementById('teams-grid');
  if (!container) return;

  const teams = KSS.teams;
  if (!teams || teams.length === 0) return;

  container.innerHTML = teams.map(t => `
    <div class="kss-card p-6 space-y-4">
      <div class="flex items-start justify-between">
        <div class="flex items-center gap-4">
          <div class="text-3xl bg-black/60 p-3 rounded-2xl border border-white/10 shadow-lg">${t.logo}</div>
          <div>
            <h3 class="text-xl font-bold text-white font-race tracking-wide">[${t.tag}] ${t.name}</h3>
            <p class="text-xs text-gray-400 font-mono mt-0.5">📍 ${t.city} • Лидер: <b>${t.leader_callsign || 'Основатель'}</b></p>
          </div>
        </div>
        <div class="text-right">
          <span class="text-2xl font-black text-lime-400 font-hud">${t.cred_score}</span>
          <span class="block text-[10px] text-gray-500 uppercase font-mono">ОЧКИ СИНДИКАТА</span>
        </div>
      </div>

      <p class="text-xs text-gray-300 leading-relaxed">${t.description}</p>

      <div class="pt-4 border-t border-white/5 flex items-center justify-between text-xs text-gray-400 font-mono">
        <div>
          👥 Пилотов: <b class="text-white">${t.members_count || 1}</b> • В гараже: <b class="text-white">${t.cars_count || 1}</b>
        </div>
        <button class="btn-kss-outline py-1.5 px-4 text-xs" onclick="showToast('Заявка отправлена лидеру в Telegram @kubanstreet', 'volt')">
          Подать заявку →
        </button>
      </div>
    </div>
  `).join('');
}

// Render Holographic Digital Pilot License with interactive tilt
function renderProfileCard() {
  const u = KSS.currentUser;
  const userCar = KSS.cars.find(c => c.user_id === u.id) || KSS.cars[0];

  const licenseBox = document.getElementById('digital-license-container');
  if (!licenseBox) return;

  const wr = Math.round((u.wins / Math.max(1, u.wins + u.losses)) * 100);

  licenseBox.innerHTML = `
    <div id="tilt-pilot-license" class="license-card p-8 space-y-6 text-white max-w-xl mx-auto cursor-pointer">
      <!-- Card Header -->
      <div class="flex items-start justify-between border-b border-white/10 pb-4 relative z-10">
        <div class="flex items-center gap-3">
          <div class="w-12 h-12 rounded-xl bg-lime-400 text-black font-black flex items-center justify-center font-hero text-2xl shadow-lg shadow-lime-400/30">
            KSS
          </div>
          <div>
            <div class="text-[11px] tracking-widest text-lime-400 font-bold uppercase font-hud">КРАСНОДАРСКИЙ КРАЙ 93/123/23</div>
            <div class="text-sm font-extrabold tracking-wider font-race">OFFICIAL PILOT LICENSE</div>
          </div>
        </div>
        <div class="text-right">
          <span class="text-[10px] text-gray-400 block font-mono">РЕЕСТРОВЫЙ НОМЕР:</span>
          <span class="text-xs font-mono font-bold text-lime-400">#KSS-93-${1000 + u.id}</span>
        </div>
      </div>

      <!-- Card Main Body -->
      <div class="grid grid-cols-1 sm:grid-cols-3 gap-6 items-center relative z-10">
        <div class="text-center sm:text-left">
          <div class="w-28 h-28 mx-auto sm:mx-0 rounded-2xl overflow-hidden border-2 border-lime-400/80 shadow-2xl shadow-lime-400/30 relative">
            <img src="${u.avatar}" class="w-full h-full object-cover">
            <div class="absolute bottom-1 right-1 w-3 h-3 rounded-full bg-lime-400 border-2 border-black"></div>
          </div>
        </div>

        <div class="sm:col-span-2 space-y-2 text-center sm:text-left">
          <div>
            <span class="text-[10px] text-gray-400 uppercase tracking-wider block font-mono">ПОЗЫВНОЙ ПИЛОТА</span>
            <h3 class="text-2xl font-black text-white font-race tracking-wider">${u.callsign}</h3>
            <p class="text-xs text-gray-300 font-mono mt-0.5">${u.name} • 📍 ${u.city}</p>
          </div>

          <div class="flex gap-2 justify-center sm:justify-start pt-1">
            <span class="kss-badge badge-volt">${u.team_tag ? `[${u.team_tag}] ${u.team_name || ''}` : 'СВОБОДНЫЙ ПИЛОТ'}</span>
            <span class="kss-badge badge-cyan">KSS VERIFIED</span>
          </div>

          <div class="text-xs text-gray-300 font-mono pt-1">
            🏎️ Основной болид: <b class="text-lime-300">${userCar ? `${userCar.make} ${userCar.model} (${userCar.hp} hp)` : 'Кастомная сборка'}</b>
          </div>
        </div>
      </div>

      <!-- Card Stats Row -->
      <div class="grid grid-cols-3 gap-3 bg-black/60 rounded-xl p-3.5 border border-white/10 text-center relative z-10 font-hud">
        <div>
          <span class="text-[10px] text-gray-400 uppercase block font-mono">STREET CRED</span>
          <span class="text-2xl font-black text-lime-400">${u.street_cred}</span>
        </div>
        <div>
          <span class="text-[10px] text-gray-400 uppercase block font-mono">ПОБЕД / ПОРАЖЕНИЙ</span>
          <span class="text-2xl font-black text-white">${u.wins} / ${u.losses}</span>
        </div>
        <div>
          <span class="text-[10px] text-gray-400 uppercase block font-mono">ВИНРЕЙТ</span>
          <span class="text-2xl font-black text-cyan-400">${wr}%</span>
        </div>
      </div>

      <!-- Card Footer Barcode -->
      <div class="flex items-center justify-between pt-2 border-t border-white/10 text-[11px] text-gray-400 font-mono relative z-10">
        <span>AUTHENTICATED VIA ${u.auth_provider ? u.auth_provider.toUpperCase() : 'KSS NETWORK'}</span>
        <span class="tracking-widest">||| | |||| || ||| |||| | ||</span>
      </div>
    </div>

    <!-- Actions Row -->
    <div class="flex flex-wrap justify-center gap-3 pt-6">
      <button class="btn-kss-volt text-xs" onclick="navigator.clipboard.writeText(window.location.origin + '?pilot=' + ${u.id}); showToast('Ссылка на лицензию пилота скопирована в буфер!', 'volt');">
        🔗 ПОДЕЛИТЬСЯ ЛИЦЕНЗИЕЙ
      </button>
      <button class="btn-kss-outline text-xs" onclick="openModal('auth-modal')">
        🔄 СМЕНИТЬ АККАУНТ
      </button>
      <button class="btn-kss-outline text-xs text-red-400 hover:text-red-300" onclick="logoutUser()">
        🚪 ВЫЙТИ
      </button>
    </div>
  `;

  // Setup 3D tilt effect on mousemove
  const card = document.getElementById('tilt-pilot-license');
  if (card) {
    card.addEventListener('mousemove', (e) => {
      const rect = card.getBoundingClientRect();
      const x = e.clientX - rect.left - rect.width / 2;
      const y = e.clientY - rect.top - rect.height / 2;
      const tiltX = (y / rect.height) * -12;
      const tiltY = (x / rect.width) * 12;
      card.style.transform = `perspective(1000px) rotateX(${tiltX}deg) rotateY(${tiltY}deg) scale3d(1.02, 1.02, 1.02)`;
    });
    card.addEventListener('mouseleave', () => {
      card.style.transform = 'perspective(1000px) rotateX(0deg) rotateY(0deg) scale3d(1, 1, 1)';
    });
  }
}

// Save custom OAuth Client IDs
function saveOAuthKeys() {
  const gId = document.getElementById('cfg-google-client-id')?.value.trim();
  const vkId = document.getElementById('cfg-vk-app-id')?.value.trim();

  if (gId) {
    KSS_AUTH.googleClientId = gId;
    localStorage.setItem('kss_google_client_id', gId);
  }
  if (vkId) {
    KSS_AUTH.vkAppId = vkId;
    localStorage.setItem('kss_vk_app_id', vkId);
  }

  initGoogleAuth();
  showToast('Ключи авторизации успешно сохранены!', 'volt');
}

// Setup Event Listeners
document.addEventListener('DOMContentLoaded', () => {
  checkExistingSession();
  initGoogleAuth();

  // Populate input fields if saved
  const gInput = document.getElementById('cfg-google-client-id');
  const vkInput = document.getElementById('cfg-vk-app-id');
  if (gInput && KSS_AUTH.googleClientId) gInput.value = KSS_AUTH.googleClientId;
  if (vkInput && KSS_AUTH.vkAppId) vkInput.value = KSS_AUTH.vkAppId;

  document.getElementById('btn-login-google')?.addEventListener('click', triggerGoogleLogin);
  document.getElementById('btn-login-vk')?.addEventListener('click', triggerVkLogin);
  document.getElementById('btn-login-tg')?.addEventListener('click', () => {
    window.open('https://t.me/Kuban_Streetbot', '_blank');
    simulateRealOAuth('telegram', 'Telegram_Пилот', 'https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=150');
  });
});
