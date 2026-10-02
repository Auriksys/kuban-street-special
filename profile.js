/**
 * KubanStreetSpecial - User Profile, Digital Pilot License & Garage Engine
 */

async function loadUserProfileData(userId) {
  try {
    const res = await api(`/api/profile/${userId}`);
    if (res && res.status === 'ok' && res.profile) {
      return res.profile;
    }
  } catch (e) {
    console.warn("Could not fetch remote profile, falling back to local state:", e);
  }
  return null;
}

async function renderProfilePage() {
  const container = document.getElementById('profile-card-container');
  if (!container) return;

  const localUser = KSS.currentUser;
  if (!localUser) {
    container.innerHTML = `
      <div class="py-16 text-center text-gray-500 font-mono">
        <p class="text-xl text-gray-300 font-bold font-race">ВЫ НЕ АВТОРИЗОВАНЫ</p>
        <p class="text-xs text-gray-400 mt-2">Войдите в систему для просмотра профиля пилота.</p>
        <button class="btn-kss-volt text-xs py-2 px-5 mt-4" onclick="checkAuthGate()">ВОЙТИ</button>
      </div>
    `;
    return;
  }

  // Fetch full profile from server if possible
  const remote = await loadUserProfileData(localUser.id);
  const u = remote || localUser;
  const userCar = u.car || (KSS.cars ? KSS.cars.find(c => c.user_id === u.id) : null);
  const wr = Math.round((u.wins / Math.max(1, (u.wins || 0) + (u.losses || 0))) * 100);

  container.innerHTML = `
    <div class="space-y-8">
      
      <!-- 1. Holographic Digital Pilot License with 3D Tilt -->
      <div id="tilt-pilot-license" class="license-card p-6 sm:p-8 space-y-6 text-white max-w-2xl mx-auto cursor-pointer">
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
            <div class="w-28 h-28 mx-auto sm:mx-0 rounded-2xl overflow-hidden border-2 border-lime-400/80 shadow-2xl shadow-lime-400/30 relative bg-gray-900">
              <img src="${u.avatar || 'https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=200'}" class="w-full h-full object-cover">
              <div class="absolute bottom-1 right-1 w-3.5 h-3.5 rounded-full bg-emerald-400 border-2 border-black animate-pulse" title="В сети"></div>
            </div>
          </div>

          <div class="sm:col-span-2 space-y-2 text-center sm:text-left">
            <div>
              <span class="text-[10px] text-gray-400 uppercase tracking-wider block font-mono">ПОЗЫВНОЙ ПИЛОТА</span>
              <h3 class="text-2xl font-black text-white font-race tracking-wider">${u.callsign}</h3>
              <p class="text-xs text-gray-300 font-mono mt-0.5">${u.name || u.callsign} • 📍 ${u.city || 'Краснодар'}</p>
            </div>

            <div class="flex gap-2 justify-center sm:justify-start pt-1 flex-wrap">
              <span class="kss-badge badge-volt">${u.team_tag ? `[${u.team_tag}] ${u.team_name || ''}` : 'СВОБОДНЫЙ ПИЛОТ'}</span>
              <span class="kss-badge badge-cyan">KSS VERIFIED</span>
              ${u.telegram_handle ? `<a href="https://t.me/${u.telegram_handle.replace('@','')}" target="_blank" class="kss-badge bg-blue-500/20 text-blue-300 border-blue-500/40 hover:bg-blue-500/30">✈️ ${u.telegram_handle}</a>` : ''}
            </div>

            <p class="text-xs text-gray-400 italic pt-1">«${u.bio || 'Ночной асфальт Кубани не прощает ошибок.'}»</p>
          </div>
        </div>

        <!-- Card Stats Row -->
        <div class="grid grid-cols-3 gap-3 bg-black/60 rounded-xl p-3.5 border border-white/10 text-center relative z-10 font-hud">
          <div>
            <span class="text-[10px] text-gray-400 uppercase block font-mono">STREET CRED</span>
            <span class="text-2xl font-black text-lime-400">${u.street_cred || 1000}</span>
          </div>
          <div>
            <span class="text-[10px] text-gray-400 uppercase block font-mono">ПОБЕД / ПОРАЖЕНИЙ</span>
            <span class="text-2xl font-black text-white">${u.wins || 0} / ${u.losses || 0}</span>
          </div>
          <div>
            <span class="text-[10px] text-gray-400 uppercase block font-mono">ВИНРЕЙТ</span>
            <span class="text-2xl font-black text-cyan-400">${wr}%</span>
          </div>
        </div>

        <!-- Card Footer -->
        <div class="flex items-center justify-between pt-2 border-t border-white/10 text-[11px] text-gray-400 font-mono relative z-10">
          <span>АВТОРИЗОВАН: ${(u.auth_provider || 'KSS NETWORK').toUpperCase()}</span>
          <span class="tracking-widest hidden sm:inline">||| | |||| || ||| |||| | ||</span>
        </div>
      </div>

      <!-- Action Buttons Row -->
      <div class="flex flex-wrap justify-center gap-3">
        <button class="btn-kss-volt text-xs py-2 px-5 flex items-center gap-1.5" onclick="openEditProfileModal()">
          <span>✏️</span> <span>РЕДАКТИРОВАТЬ ПРОФИЛЬ</span>
        </button>
        <button class="btn-kss-outline text-xs py-2 px-4 flex items-center gap-1.5" onclick="openModal('car-register-modal')">
          <span>🏎️</span> <span>ДОБАВИТЬ / СМЕНИТЬ АВТО</span>
        </button>
        <button class="btn-kss-outline text-xs py-2 px-4" onclick="navigator.clipboard.writeText(window.location.origin + '?pilot=' + ${u.id}); showToast('Ссылка на профиль скопирована в буфер!', 'cyan');">
          🔗 ПОДЕЛИТЬСЯ
        </button>
        <button class="btn-kss-outline text-xs py-2 px-4 text-red-400 hover:text-red-300" onclick="logoutUser()">
          🚪 ВЫЙТИ
        </button>
      </div>

      <!-- 2. Primary Car Showcase Card -->
      <div class="space-y-4">
        <div class="flex items-center justify-between">
          <h3 class="text-lg font-black text-white font-race tracking-wider flex items-center gap-2">
            <span>🏎️</span> <span>БОЕВОЙ БОЛИД ПИЛОТА:</span>
          </h3>
          ${userCar ? `<span class="kss-badge badge-volt font-mono font-bold">${userCar.hp} HP • ${userCar.drivetrain}</span>` : ''}
        </div>

        ${userCar ? renderPrimaryCarBlock(userCar) : renderNoCarBlock()}
      </div>

      <!-- 3. Pilot's Battles History -->
      ${u.recent_battles && u.recent_battles.length > 0 ? renderPilotBattlesBlock(u.recent_battles, u.id) : ''}

    </div>
  `;

  setupLicenseTilt();
}

function renderPrimaryCarBlock(car) {
  let specs = {};
  if (car.specs && typeof car.specs === 'object') {
    specs = car.specs;
  } else if (car.specs_json) {
    try {
      specs = JSON.parse(car.specs_json);
    } catch (e) {
      specs = {};
    }
  }
  const ptw = Math.round((car.hp / (car.weight || 1400)) * 1000);

  return `
    <div class="kss-card p-6 space-y-6">
      <div class="grid grid-cols-1 lg:grid-cols-12 gap-6 items-center">
        <!-- Car Photo -->
        <div class="lg:col-span-5 relative h-56 rounded-2xl overflow-hidden bg-gray-900 border border-white/10 group shadow-xl">
          <img src="${car.photo_url || 'https://images.unsplash.com/photo-1617814076367-b759c7d7e738?w=800'}" class="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105">
          <div class="absolute inset-0 bg-gradient-to-t from-black/80 via-black/20 to-transparent"></div>
          <div class="absolute top-3 left-3 flex gap-1.5">
            <span class="kss-badge badge-volt">${car.drivetrain}</span>
            <span class="kss-badge badge-cyan">${car.aspiration}</span>
          </div>
          <div class="absolute bottom-3 left-3 right-3 flex justify-between items-end">
            <div>
              <div class="text-xs text-lime-400 font-mono font-bold">${car.year || 2020} • ${car.engine_code || 'Мотор'}</div>
              <div class="text-xl font-black text-white font-race">${car.make} ${car.model}</div>
            </div>
            ${car.plate_number ? `<span class="bg-white text-black font-mono font-bold text-xs px-2.5 py-1 rounded border border-black shadow">${car.plate_number}</span>` : ''}
          </div>
        </div>

        <!-- Telemetry & Specs -->
        <div class="lg:col-span-7 space-y-4">
          <!-- 4 Main Telemetry Gauges -->
          <div class="grid grid-cols-2 sm:grid-cols-4 gap-3 text-center">
            <div class="bg-black/60 p-3 rounded-xl border border-white/10">
              <span class="text-[10px] text-gray-400 uppercase font-mono block">МОЩНОСТЬ</span>
              <span class="text-xl font-black text-lime-400 font-hud">${car.hp} <span class="text-xs">л.с.</span></span>
            </div>
            <div class="bg-black/60 p-3 rounded-xl border border-white/10">
              <span class="text-[10px] text-gray-400 uppercase font-mono block">МОМЕНТ</span>
              <span class="text-xl font-black text-white font-hud">${car.torque || Math.round(car.hp * 1.25)} <span class="text-xs">Нм</span></span>
            </div>
            <div class="bg-black/60 p-3 rounded-xl border border-white/10">
              <span class="text-[10px] text-gray-400 uppercase font-mono block">0-100 КМ/Ч</span>
              <span class="text-xl font-black text-cyan-400 font-hud">${car.zero_to_hundred ? car.zero_to_hundred.toFixed(1) : '4.2'}<span class="text-xs">с</span></span>
            </div>
            <div class="bg-black/60 p-3 rounded-xl border border-white/10">
              <span class="text-[10px] text-gray-400 uppercase font-mono block">1/4 МИЛИ</span>
              <span class="text-xl font-black text-yellow-400 font-hud">${car.quarter_mile ? car.quarter_mile.toFixed(1) : '12.0'}<span class="text-xs">с</span></span>
            </div>
          </div>

          <!-- Specs List -->
          <div class="space-y-1.5 text-xs">
            <div class="flex justify-between p-2 rounded bg-white/[0.02] border border-white/5">
              <span class="text-gray-400">Снаряженная масса:</span>
              <span class="text-white font-mono font-bold">${car.weight || 1450} кг (${ptw} л.с./тонну)</span>
            </div>
            ${specs.turbo ? `
              <div class="flex justify-between p-2 rounded bg-white/[0.02] border border-white/5">
                <span class="text-gray-400">Турбо / Наддув:</span>
                <span class="text-lime-300 font-mono font-bold">${specs.turbo}</span>
              </div>
            ` : ''}
            ${specs.ecu ? `
              <div class="flex justify-between p-2 rounded bg-white/[0.02] border border-white/5">
                <span class="text-gray-400">ЭБУ / Настройка:</span>
                <span class="text-white font-mono">${specs.ecu}</span>
              </div>
            ` : ''}
            ${specs.suspension ? `
              <div class="flex justify-between p-2 rounded bg-white/[0.02] border border-white/5">
                <span class="text-gray-400">Подвеска:</span>
                <span class="text-white font-mono">${specs.suspension}</span>
              </div>
            ` : ''}
            ${specs.tires ? `
              <div class="flex justify-between p-2 rounded bg-white/[0.02] border border-white/5">
                <span class="text-gray-400">Резина / Зацеп:</span>
                <span class="text-cyan-300 font-mono font-bold">${specs.tires}</span>
              </div>
            ` : ''}
          </div>
        </div>
      </div>
    </div>
  `;
}

function renderNoCarBlock() {
  return `
    <div class="kss-card p-8 text-center space-y-4 border-dashed border-white/20">
      <div class="text-5xl">🏎️</div>
      <h4 class="text-lg font-bold text-white font-race">В ГАРАЖЕ ПОКА НЕТ АВТОМОБИЛЯ</h4>
      <p class="text-xs text-gray-400 max-w-md mx-auto">Внесите свой боевой автомобиль в базу KSS через Telegram-бота @Kuban_Streetbot за 5 быстрых шагов или заполните веб-форму.</p>
      <div class="flex justify-center gap-3 pt-2">
        <a href="https://t.me/Kuban_Streetbot?start=car" target="_blank" class="btn-kss-volt text-xs py-2 px-5">
          Внести авто через бота (/car) →
        </a>
        <button onclick="openModal('car-register-modal')" class="btn-kss-outline text-xs py-2 px-4">
          Заполнить форму на сайте
        </button>
      </div>
    </div>
  `;
}

function renderPilotBattlesBlock(battles, currentUserId) {
  return `
    <div class="space-y-4 pt-4">
      <h3 class="text-lg font-black text-white font-race tracking-wider flex items-center gap-2">
        <span>⚔️</span> <span>ИСТОРИЯ СХВАТОК ПИЛОТА:</span>
      </h3>
      <div class="space-y-2">
        ${battles.map(b => {
          const isWinner = b.winner_id === currentUserId;
          const badgeClass = isWinner ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/40' : 'bg-red-500/20 text-red-400 border-red-500/40';
          const outcomeText = isWinner ? '🏆 ПОБЕДА' : '❌ ПОРАЖЕНИЕ';
          const opponent = isWinner ? (b.loser_callsign || 'Соперник') : (b.winner_callsign || 'Победитель');

          return `
            <div class="kss-card p-3.5 flex items-center justify-between gap-4 text-xs font-mono">
              <div class="flex items-center gap-3">
                <span class="px-2.5 py-1 rounded font-bold border ${badgeClass}">${outcomeText}</span>
                <div>
                  <span class="text-white font-bold">${b.discipline}</span>
                  <span class="text-gray-400">против <b>${opponent}</b></span>
                </div>
              </div>
              <div class="text-right">
                <span class="text-gray-400">${b.gap_description || ''}</span>
                <span class="${isWinner ? 'text-lime-400' : 'text-red-400'} font-bold ml-2">${isWinner ? '+' : '-'}${b.cred_delta || 25} PTS</span>
              </div>
            </div>
          `;
        }).join('')}
      </div>
    </div>
  `;
}

function setupLicenseTilt() {
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

// -------------------------------------------------------------
// EDIT PROFILE MODAL
// -------------------------------------------------------------

function openEditProfileModal() {
  const u = KSS.currentUser;
  if (!u) return;

  const elCallsign = document.getElementById('edit-profile-callsign');
  const elName = document.getElementById('edit-profile-name');
  const elCity = document.getElementById('edit-profile-city');
  const elAvatar = document.getElementById('edit-profile-avatar');
  const elBio = document.getElementById('edit-profile-bio');
  const elTg = document.getElementById('edit-profile-tg');
  const elVk = document.getElementById('edit-profile-vk');

  if (elCallsign) elCallsign.value = u.callsign || '';
  if (elName) elName.value = u.name || '';
  if (elCity) elCity.value = u.city || 'Краснодар';
  if (elAvatar) elAvatar.value = u.avatar || '';
  if (elBio) elBio.value = u.bio || '';
  if (elTg) elTg.value = u.telegram_handle || '';
  if (elVk) elVk.value = u.vk_url || '';

  openModal('edit-profile-modal');
}

function selectAvatarPreset(url) {
  const elAvatar = document.getElementById('edit-profile-avatar');
  if (elAvatar) {
    elAvatar.value = url;
    showToast('Аватар выбран!', 'volt');
  }
}

async function saveProfileUpdates() {
  const u = KSS.currentUser;
  if (!u) return;

  const callsign = document.getElementById('edit-profile-callsign')?.value.trim();
  const name = document.getElementById('edit-profile-name')?.value.trim();
  const city = document.getElementById('edit-profile-city')?.value.trim();
  const avatar = document.getElementById('edit-profile-avatar')?.value.trim();
  const bio = document.getElementById('edit-profile-bio')?.value.trim();
  const telegram_handle = document.getElementById('edit-profile-tg')?.value.trim();
  const vk_url = document.getElementById('edit-profile-vk')?.value.trim();

  if (!callsign) {
    showToast('Позывной не может быть пустым!', 'red');
    return;
  }

  const payload = {
    user_id: u.id,
    callsign: callsign,
    name: name || callsign,
    city: city || 'Краснодар',
    avatar: avatar || u.avatar,
    bio: bio || '',
    telegram_handle: telegram_handle ? (telegram_handle.startsWith('@') ? telegram_handle : `@${telegram_handle}`) : '',
    vk_url: vk_url || ''
  };

  try {
    const res = await api('/api/profile/update', {
      method: 'POST',
      body: JSON.stringify(payload)
    });

    if (res && res.status === 'ok' && res.user) {
      KSS.currentUser = { ...KSS.currentUser, ...res.user };
      localStorage.setItem('kss_user_session', JSON.stringify(KSS.currentUser));

      if (typeof updateUserDisplay === 'function') {
        updateUserDisplay();
      }

      closeModal('edit-profile-modal');
      renderProfilePage();
      showToast('Профиль пилота успешно обновлен! 🏁', 'volt');
    }
  } catch (err) {
    console.error('Save profile error:', err);
  }
}

// Global exports
window.renderProfilePage = renderProfilePage;
window.openEditProfileModal = openEditProfileModal;
window.selectAvatarPreset = selectAvatarPreset;
window.saveProfileUpdates = saveProfileUpdates;
