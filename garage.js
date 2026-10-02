/**
 * KubanStreetSpecial - Garage & Car Registry Module
 * Handles Car Catalog, Gran Turismo Spec Sheets, and Registration
 */

function renderGarage(filterCars = null) {
  const container = document.getElementById('garage-cards-grid') || document.getElementById('garage-grid');
  const previewContainer = document.getElementById('radar-cars-preview');

  const cars = filterCars || KSS.cars;
  if (!cars || cars.length === 0) {
    if (container) {
      container.innerHTML = `
        <div class="col-span-full py-16 text-center text-gray-500 font-mono">
          <div class="text-5xl mb-3">🏎️</div>
          <p class="text-xl text-gray-200 font-bold font-race">ГАРАЖ ПОКА ПУСТ</p>
          <p class="text-xs text-gray-400 mt-2 max-w-md mx-auto">Машины пока не зарегистрированы. Добавьте свой боевой болид первым через сайт или через бота в Telegram!</p>
          <div class="mt-6 flex flex-wrap justify-center gap-3">
            <button class="btn-kss-volt text-xs py-2.5 px-5" onclick="switchTab('bot')">
              + ВНЕСТИ АВТО ЧЕРЕЗ БОТА
            </button>
          </div>
        </div>
      `;
    }
    if (previewContainer) {
      previewContainer.innerHTML = '<div class="col-span-full text-center py-6 text-gray-500 font-mono text-xs">Автомобили пока не добавлены</div>';
    }
    return;
  }


  const cardsHtml = cars.map(car => {
    const ptw = Math.round((car.hp / car.weight) * 1000);
    const teamBadge = car.team_tag ? `<span class="kss-badge badge-volt">[${car.team_tag}]</span>` : '';
    const driveColor = car.drivetrain === 'AWD' ? 'badge-cyan' : (car.drivetrain === 'RWD' ? 'badge-red' : 'badge-gray');
    const rollTime = car.roll_hundred_two_hundred ? `${car.roll_hundred_two_hundred.toFixed(1)}с` : (car.hp > 500 ? '6.8с' : (car.hp > 400 ? '7.9с' : '9.5с'));
    const isDragy = car.dragy_verified || car.hp >= 460;
    const boostStr = car.boost_bar ? `${car.boost_bar} bar` : (car.aspiration === 'Турбо' ? '1.6 bar' : 'Атмо');
    const fuelStr = car.fuel_type || 'АИ-100';

    return `
      <div class="kss-card group flex flex-col justify-between" onclick="openCarDetail(${car.id})">
        <div>
          <!-- Car Image Header -->
          <div class="relative h-48 w-full overflow-hidden bg-gray-900 rounded-t-xl">
            <img src="${car.photo_url || 'https://images.unsplash.com/photo-1503376780353-7e6692767b70?w=600'}" 
                 alt="${car.make} ${car.model}" 
                 class="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105"
                 onerror="this.src='https://images.unsplash.com/photo-1542282088-72c9c27ed0cd?w=600'">
            <div class="absolute inset-0 bg-gradient-to-t from-[#0b0e14] via-transparent to-black/40"></div>
            
            <!-- Badges overlay -->
            <div class="absolute top-3 left-3 flex gap-1.5 flex-wrap">
              <span class="kss-badge ${driveColor}">${car.drivetrain}</span>
              <span class="kss-badge badge-volt">${car.aspiration}</span>
              ${isDragy ? `<span class="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-amber-500/20 border border-amber-400/50 text-amber-300">⏱️ DRAGY VERIFIED</span>` : ''}
            </div>

            <div class="absolute top-3 right-3">
              <span class="bg-black/80 backdrop-blur border border-white/10 text-xs px-2.5 py-1 rounded font-mono text-gray-300">
                ${car.plate_number || 'РЕГИОН 93'}
              </span>
            </div>

            <!-- Bottom of image info -->
            <div class="absolute bottom-2 left-3 right-3 flex justify-between items-end">
              <div>
                <h3 class="text-lg font-bold text-white font-race tracking-wide group-hover:text-lime-300 transition-colors">
                  ${car.make} ${car.model} <span class="text-xs text-gray-400 font-normal">${car.generation || ''}</span>
                </h3>
                <p class="text-xs text-gray-300 flex items-center gap-1.5 mt-0.5">
                  ${teamBadge} <span>${car.owner_callsign || 'Пилот'}</span> <span class="text-gray-500">•</span> <span class="text-gray-400">${car.owner_city || 'Кубань'}</span>
                </p>
              </div>
            </div>
          </div>

          <!-- Serious Telemetry Row (0-100, 100-200, 402m) -->
          <div class="p-4 space-y-3">
            <div class="grid grid-cols-4 gap-1.5 py-2 border-y border-white/5 text-center bg-black/30 rounded-lg p-2">
              <div>
                <span class="text-[9px] text-gray-500 uppercase tracking-wider block font-mono">Мощность</span>
                <span class="text-sm font-bold text-lime-400 font-hud">${car.hp} <span class="text-[10px] text-gray-400">hp</span></span>
              </div>
              <div>
                <span class="text-[9px] text-gray-500 uppercase tracking-wider block font-mono">0-100</span>
                <span class="text-sm font-bold text-cyan-400 font-hud">${car.zero_to_hundred ? car.zero_to_hundred.toFixed(1) + 'с' : '—'}</span>
              </div>
              <div>
                <span class="text-[9px] text-amber-400 uppercase tracking-wider block font-mono font-bold">100-200</span>
                <span class="text-sm font-bold text-amber-300 font-hud">${rollTime}</span>
              </div>
              <div>
                <span class="text-[9px] text-gray-500 uppercase tracking-wider block font-mono">402м</span>
                <span class="text-sm font-bold text-white font-hud">${car.quarter_mile ? car.quarter_mile.toFixed(1) + 'с' : '—'}</span>
              </div>
            </div>

            <!-- Engine & Fuel/Boost Details -->
            <div class="flex items-center justify-between text-[11px] font-mono text-gray-400 pt-0.5">
              <span>⚙️ ${car.engine_code || 'Мотор'} • ${boostStr}</span>
              <span class="text-lime-300 font-bold bg-lime-400/10 px-1.5 py-0.5 rounded border border-lime-400/20">${fuelStr}</span>
            </div>

            <!-- Power to weight ratio -->
            <div class="space-y-1 pt-1">
              <div class="flex justify-between text-[11px] text-gray-400 font-mono">
                <span>Удельная отдача:</span>
                <span class="text-lime-300 font-bold">${ptw} л.с./тонну (${car.weight} кг)</span>
              </div>
              <div class="spec-gauge-bar">
                <div class="spec-gauge-fill bg-gradient-to-r from-cyan-500 via-lime-400 to-red-500" style="width: ${Math.min(100, (ptw / 500) * 100)}%"></div>
              </div>
            </div>
          </div>
        </div>

        <!-- Footer Action -->
        <div class="px-4 pb-4 pt-2 border-t border-white/5 flex items-center justify-between">
          <span class="text-xs text-gray-400 hover:text-white transition-colors flex items-center gap-1 font-mono">
            🔍 Паспорт авто
          </span>
          <button onclick="event.stopPropagation(); challengeCar(${car.id})" class="text-xs font-race font-bold text-lime-400 hover:text-lime-300 bg-lime-400/10 hover:bg-lime-400/20 border border-lime-400/30 px-3 py-1 rounded-lg transition-colors">
            ВЫЗВАТЬ НА ДУЭЛЬ ⚔️
          </button>
        </div>
      </div>
    `;
  }).join('');

  if (container) {
    container.innerHTML = cardsHtml;
  }

  if (previewContainer) {
    const previewCars = cars.slice(0, 4);
    previewContainer.innerHTML = previewCars.map(car => `
      <div class="kss-card cursor-pointer group flex flex-col justify-between" onclick="openCarDetail(${car.id})">
        <div class="relative h-36 w-full overflow-hidden bg-gray-900 rounded-t-xl">
          <img src="${car.photo_url || 'https://images.unsplash.com/photo-1503376780353-7e6692767b70?w=600'}" class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300">
          <div class="absolute inset-0 bg-gradient-to-t from-black via-transparent to-transparent"></div>
          <div class="absolute bottom-2 left-3 right-3 flex justify-between items-end">
            <div>
              <div class="text-sm font-bold text-white font-race">${car.make} ${car.model}</div>
              <div class="text-[10px] text-gray-300">${car.owner_callsign || 'Пилот'} • ${car.owner_city || 'Кубань'}</div>
            </div>
            <div class="text-xs font-mono font-bold text-lime-400">${car.hp} л.с.</div>
          </div>
        </div>
        <div class="p-3 bg-black/40 flex justify-between items-center text-[11px] font-mono text-gray-400">
          <span>${car.drivetrain} • ${car.aspiration || 'Турбо'}</span>
          <span class="text-lime-400 font-bold">СМОТРЕТЬ →</span>
        </div>
      </div>
    `).join('');
  }
}


// Open Car Detail Technical Sheet Modal
async function openCarDetail(carId) {
  try {
    const res = await api(`/api/cars/${carId}`);
    if (res.status !== 'ok' || !res.car) return;
    const c = res.car;
    const ptw = Math.round((c.hp / c.weight) * 1000);

    const modalContent = document.getElementById('car-detail-modal-body');
    if (!modalContent) return;

    // Build Victories list
    let victoriesHtml = '';
    if (c.victories && c.victories.length > 0) {
      victoriesHtml = c.victories.map(v => `
        <div class="bg-[#141724] border border-white/5 rounded-lg p-3 flex items-center justify-between text-sm">
          <div class="flex items-center gap-2.5">
            <span class="text-lime-400 font-bold">🏆 ПОБЕДА</span>
            <span class="text-gray-400">над</span>
            <span class="text-white font-medium">${v.loser_callsign ? v.loser_callsign : (v.loser_make ? `${v.loser_make} ${v.loser_model}` : v.loser_custom_name)}</span>
          </div>
          <div class="text-right">
            <div class="text-xs text-cyan-300 font-mono">${v.gap_description || '1 корпус'}</div>
            <div class="text-[11px] text-gray-500">${v.discipline} • ${v.spot_name || 'Кубань'}</div>
          </div>
        </div>
      `).join('');
    } else {
      victoriesHtml = '<p class="text-xs text-gray-500 italic py-2">Заезды пока не зафиксированы в бортовом журнале</p>';
    }

    // Build specs list
    let modsHtml = '';
    if (c.specs && typeof c.specs === 'object') {
      modsHtml = Object.entries(c.specs).map(([key, val]) => `
        <div class="flex justify-between py-1.5 border-b border-white/5 text-xs">
          <span class="text-gray-400 uppercase tracking-wider">${key}:</span>
          <span class="text-white font-mono text-right max-w-[60%]">${val}</span>
        </div>
      `).join('');
    }

    const rollStr = c.roll_hundred_two_hundred ? `${c.roll_hundred_two_hundred.toFixed(1)}с` : (c.hp > 500 ? '6.8с' : (c.hp > 400 ? '7.9с' : '9.5с'));
    const isDragy = c.dragy_verified || c.hp >= 460;
    const boostStr = c.boost_bar ? `${c.boost_bar} bar` : (c.aspiration === 'Турбо' ? '1.6 bar' : 'Атмосфера');
    const fuelStr = c.fuel_type || 'АИ-100';

    modalContent.innerHTML = `
      <div class="relative">
        <!-- Banner Image -->
        <div class="relative h-64 w-full bg-gray-900 rounded-t-2xl overflow-hidden">
          <img src="${c.photo_url}" alt="${c.make} ${c.model}" class="w-full h-full object-cover">
          <div class="absolute inset-0 bg-gradient-to-t from-[#0f1118] via-transparent to-black/50"></div>
          
          <button class="absolute top-4 right-4 bg-black/60 text-white rounded-full p-2 hover:bg-black transition-colors" onclick="closeModal('car-detail-modal')">
            ✕
          </button>

          <div class="absolute bottom-4 left-6 right-6 flex items-end justify-between flex-wrap gap-2">
            <div>
              <div class="flex gap-2 mb-1.5 flex-wrap items-center">
                <span class="kss-badge badge-volt">${c.drivetrain}</span>
                <span class="kss-badge badge-cyan">${c.aspiration}</span>
                <span class="kss-badge bg-black/60 border border-white/20 text-gray-300 font-mono">${boostStr}</span>
                <span class="kss-badge bg-lime-500/20 text-lime-300 border-lime-500/40 font-mono">${fuelStr}</span>
                ${isDragy ? `<span class="dragy-verified-seal">⏱️ DRAGY VERIFIED</span>` : ''}
              </div>
              <h2 class="text-3xl font-extrabold text-white font-race tracking-wider">${c.make} ${c.model} ${c.generation || ''}</h2>
              <p class="text-sm text-gray-300 flex items-center gap-2 mt-1">
                <span>👤 Пилот: <b>${c.owner_callsign}</b> (${c.owner_name || ''})</span>
                ${c.team_tag ? `<span class="kss-badge badge-volt">[${c.team_tag}] ${c.team_name}</span>` : ''}
              </p>
            </div>
            <div class="text-right hidden sm:block">
              <div class="bg-black/80 border border-white/20 px-3 py-1.5 rounded font-mono text-sm tracking-widest text-lime-400">
                ${c.plate_number || 'КРАСНОДАР'}
              </div>
            </div>
          </div>
        </div>

        <!-- Body Details -->
        <div class="p-6 space-y-6">
          <!-- Big Specs Row: 5 Telemetry Gauges -->
          <div class="grid grid-cols-2 sm:grid-cols-5 gap-2.5 bg-[#141724] border border-white/10 rounded-xl p-3.5 text-center">
            <div>
              <div class="text-[10px] text-gray-400 uppercase tracking-wider font-mono">Мощность</div>
              <div class="text-xl font-black text-lime-400 font-hud">${c.hp} <span class="text-[10px] font-normal text-gray-400">л.с.</span></div>
              <div class="text-[10px] text-gray-500 font-mono mt-0.5">${c.engine_code || 'Мотор'}</div>
            </div>
            <div>
              <div class="text-[10px] text-gray-400 uppercase tracking-wider font-mono">0-100 КМ/Ч</div>
              <div class="text-xl font-black text-cyan-400 font-hud">${c.zero_to_hundred ? c.zero_to_hundred.toFixed(1) + 'с' : '—'}</div>
              <div class="text-[10px] text-gray-500 font-mono mt-0.5">Старт</div>
            </div>
            <div>
              <div class="text-[10px] text-amber-400 uppercase tracking-wider font-mono font-bold">100-200 РОЛЛ</div>
              <div class="text-xl font-black text-amber-300 font-hud">${rollStr}</div>
              <div class="text-[10px] text-amber-500 font-mono mt-0.5">Ролл-он</div>
            </div>
            <div>
              <div class="text-[10px] text-gray-400 uppercase tracking-wider font-mono">402 МЕТРА</div>
              <div class="text-xl font-black text-white font-hud">${c.quarter_mile ? c.quarter_mile.toFixed(1) + 'с' : '—'}</div>
              <div class="text-[10px] text-gray-500 font-mono mt-0.5">Квотер</div>
            </div>
            <div class="col-span-2 sm:col-span-1">
              <div class="text-[10px] text-gray-400 uppercase tracking-wider font-mono">P2W ОТДАЧА</div>
              <div class="text-xl font-black text-lime-300 font-hud">${ptw}</div>
              <div class="text-[10px] text-gray-400 font-mono mt-0.5">л.с./т (${c.weight} кг)</div>
            </div>
          </div>

          <!-- Build Spec List (Gran Turismo style) -->
          <div class="space-y-2">
            <h4 class="text-sm font-bold text-gray-300 uppercase tracking-wider font-race flex items-center gap-2">
              <span>🔧 СПЕК-ЛИСТ И ДОРАБОТКИ</span>
            </h4>
            <div class="bg-[#12141e] border border-white/5 rounded-xl p-4 space-y-1">
              ${modsHtml || '<p class="text-xs text-gray-500">Заводской спек / базовые доработки</p>'}
            </div>
          </div>

          <!-- Victories / Kill List -->
          <div class="space-y-2">
            <h4 class="text-sm font-bold text-gray-300 uppercase tracking-wider font-race flex items-center gap-2">
              <span>⚔️ КИЛЛ-ЛИСТ АВТОМОБИЛЯ (ПОБЕДЫ В ДРЭГЕ И ТОГЕ)</span>
            </h4>
            <div class="space-y-2">
              ${victoriesHtml}
            </div>
          </div>

          <!-- Action Buttons -->
          <div class="flex gap-3 pt-2">
            <button class="flex-1 btn-kss-volt" onclick="closeModal('car-detail-modal'); challengeCar(${c.id})">
              ⚔️ ВЫЗВАТЬ НА ДУЭЛЬ
            </button>
            <button class="btn-kss-outline" onclick="closeModal('car-detail-modal'); openSimWithCar(${c.id})">
              🎮 В СИМУЛЯТОР
            </button>
          </div>
        </div>
      </div>
    `;

    openModal('car-detail-modal');
  } catch (err) {
    console.error('Error opening car detail:', err);
  }
}

// Live calculation on car registration form
function setupCarFormListeners() {
  const hpInput = document.getElementById('reg-car-hp');
  const weightInput = document.getElementById('reg-car-weight');
  const ptwDisplay = document.getElementById('reg-car-ptw-preview');

  function updatePtw() {
    const hp = parseFloat(hpInput?.value) || 0;
    const w = parseFloat(weightInput?.value) || 0;
    if (hp > 0 && w > 0 && ptwDisplay) {
      const ptw = Math.round((hp / w) * 1000);
      ptwDisplay.innerText = `${ptw} л.с./т`;
    }
  }

  hpInput?.addEventListener('input', updatePtw);
  weightInput?.addEventListener('input', updatePtw);
}

// Submit Car Registration
async function handleCarRegistration(e) {
  e.preventDefault();
  const form = e.target;

  const payload = {
    user_id: KSS.currentUser?.id || 1,
    make: form.make.value.trim(),
    model: form.model.value.trim(),
    generation: form.generation.value.trim(),
    year: parseInt(form.year.value) || 2018,
    plate_number: form.plate_number.value.trim(),
    hp: parseInt(form.hp.value) || 200,
    torque: parseInt(form.torque.value) || null,
    weight: parseInt(form.weight.value) || 1400,
    drivetrain: form.drivetrain.value,
    aspiration: form.aspiration.value,
    engine_code: form.engine_code.value.trim(),
    zero_to_hundred: parseFloat(form.zero_to_hundred.value) || null,
    quarter_mile: parseFloat(form.quarter_mile.value) || null,
    photo_url: form.photo_url.value.trim() || 'https://images.unsplash.com/photo-1542282088-72c9c27ed0cd?w=800',
    specs: {
      "Турбина / Впуск": form.spec_turbo?.value || "Сток",
      "Прошивка / ЭБУ": form.spec_ecu?.value || "Кастом",
      "Подвеска": form.spec_suspension?.value || "Коиловеры",
      "Тормозная система": form.spec_brakes?.value || "Спортивные суппорты",
      "Шины / Зацеп": form.spec_tires?.value || "Полуслик",
      "Выхлоп": form.spec_exhaust?.value || "Прямоток"
    }
  };

  try {
    const res = await api('/api/cars', {
      method: 'POST',
      body: JSON.stringify(payload)
    });

    if (res.status === 'ok') {
      showToast('Автомобиль успешно внесен в реестр Кубани!', 'volt');
      closeModal('car-register-modal');
      form.reset();
      
      // Reload cars
      const carsRes = await api('/api/cars');
      if (carsRes.status === 'ok') {
        KSS.cars = carsRes.cars;
        renderGarage();
        populateCarSelectors();
      }
    }
  } catch (err) {
    console.error('Failed to register car:', err);
  }
}

// Populate car dropdowns for battle logger and simulator
function populateCarSelectors() {
  const winnerSel = document.getElementById('input-battle-winner-car') || document.getElementById('battle-winner-car');
  const loserSel = document.getElementById('battle-loser-car');
  const sim1Sel = document.getElementById('sim-car-1');
  const sim2Sel = document.getElementById('sim-car-2');
  const spotSel = document.getElementById('battle-spot-id');

  const optionsHtml = KSS.cars.map(c => 
    `<option value="${c.id}">${c.make} ${c.model} (${c.hp} hp, ${c.owner_callsign || 'Пилот'})</option>`
  ).join('');

  if (winnerSel) winnerSel.innerHTML = optionsHtml;
  if (loserSel) {
    loserSel.innerHTML = `<option value="">-- Ввести вручную (не из базы) --</option>` + optionsHtml;
  }
  if (sim1Sel) {
    sim1Sel.innerHTML = optionsHtml;
    if (KSS.cars.length > 0) sim1Sel.value = KSS.cars[0].id;
  }
  if (sim2Sel) {
    sim2Sel.innerHTML = optionsHtml;
    if (KSS.cars.length > 1) sim2Sel.value = KSS.cars[1].id;
  }
  if (spotSel && KSS.spots) {
    spotSel.innerHTML = KSS.spots.map(s => `<option value="${s.id}">${s.name} (${s.type}, ${s.city})</option>`).join('');
  }
}


// Filter listeners
document.addEventListener('DOMContentLoaded', () => {
  const filterDrivetrain = document.getElementById('filter-drivetrain');
  const filterCity = document.getElementById('filter-city');
  const searchInput = document.getElementById('search-cars');

  function applyFilters() {
    let filtered = [...KSS.cars];
    const drive = filterDrivetrain?.value;
    const city = filterCity?.value;
    const q = searchInput?.value.toLowerCase().trim();

    if (drive && drive !== 'ALL') {
      filtered = filtered.filter(c => c.drivetrain === drive);
    }
    if (city && city !== 'ALL') {
      filtered = filtered.filter(c => c.owner_city === city);
    }
    if (q) {
      filtered = filtered.filter(c => 
        c.make.toLowerCase().includes(q) ||
        c.model.toLowerCase().includes(q) ||
        (c.engine_code && c.engine_code.toLowerCase().includes(q)) ||
        (c.owner_callsign && c.owner_callsign.toLowerCase().includes(q))
      );
    }
    renderGarage(filtered);
  }

  filterDrivetrain?.addEventListener('change', applyFilters);
  filterCity?.addEventListener('change', applyFilters);
  searchInput?.addEventListener('input', applyFilters);

  setupCarFormListeners();
  document.getElementById('form-register-car')?.addEventListener('submit', handleCarRegistration);
});

async function submitQuickCarForm() {
  const make = document.getElementById('input-car-make')?.value.trim();
  const model = document.getElementById('input-car-model')?.value.trim();
  const hp = parseInt(document.getElementById('input-car-hp')?.value) || 300;
  const drivetrain = document.getElementById('input-car-drivetrain')?.value || 'RWD';
  const photo = document.getElementById('input-car-photo')?.value.trim() || 'https://images.unsplash.com/photo-1503376780353-7e6692767b70?w=800';

  if (!make || !model) {
    showToast('Введите марку и модель автомобиля', 'red');
    return;
  }

  const payload = {
    user_id: KSS.currentUser?.id || 1,
    make,
    model,
    hp,
    drivetrain,
    photo_url: photo,
    weight: 1400,
    aspiration: 'Турбо'
  };

  try {
    const res = await api('/api/cars', {
      method: 'POST',
      body: JSON.stringify(payload)
    });
    if (res.status === 'ok') {
      showToast('Автомобиль успешно внесен в реестр Кубани!', 'volt');
      closeModal('car-register-modal');
      const carsRes = await api('/api/cars');
      if (carsRes.status === 'ok') {
        KSS.cars = carsRes.cars;
        renderGarage();
        populateCarSelectors();
      }
    }
  } catch (e) {
    showToast('Ошибка сохранения: ' + e.message, 'red');
  }
}

let activeDrivetrain = 'ALL';
function setDrivetrainFilter(drive) {
  activeDrivetrain = drive;
  document.querySelectorAll('[data-drivetrain-filter]').forEach(b => {
    if (b.dataset.drivetrainFilter === drive) {
      b.classList.add('active', 'border-lime-400', 'text-lime-400');
    } else {
      b.classList.remove('active', 'border-lime-400', 'text-lime-400');
    }
  });
  filterGarageCars();
}

function filterGarageCars() {
  const query = document.getElementById('garage-search-input')?.value.toLowerCase().trim() || '';
  let filtered = [...KSS.cars];

  if (activeDrivetrain && activeDrivetrain !== 'ALL') {
    filtered = filtered.filter(c => c.drivetrain === activeDrivetrain);
  }

  if (query) {
    filtered = filtered.filter(c =>
      (c.make && c.make.toLowerCase().includes(query)) ||
      (c.model && c.model.toLowerCase().includes(query)) ||
      (c.engine_code && c.engine_code.toLowerCase().includes(query)) ||
      (c.owner_callsign && c.owner_callsign.toLowerCase().includes(query))
    );
  }

  renderGarage(filtered);
}

function challengeCar(carId) {
  const targetCar = KSS.cars ? KSS.cars.find(c => c.id === carId) : null;
  const myCar = KSS.cars ? (KSS.cars.find(c => c.user_id === KSS.currentUser?.id) || KSS.cars[0]) : null;

  switchTab('simulator');

  const sim1 = document.getElementById('sim-car-1');
  const sim2 = document.getElementById('sim-car-2');
  if (sim1 && myCar) sim1.value = myCar.id;
  if (sim2 && targetCar) sim2.value = targetCar.id;

  if (typeof updateSimPreviews === 'function') {
    updateSimPreviews();
  }

  const oppName = targetCar ? `${targetCar.make} ${targetCar.model}` : 'соперника';
  showToast(`⚔️ Вызов сформирован против ${oppName}! Рассчитайте дуэль!`, 'volt');

  const simBox = document.getElementById('section-simulator');
  if (simBox) {
    simBox.scrollIntoView({ behavior: 'smooth' });
  }
}

window.challengeCar = challengeCar;
window.submitQuickCarForm = submitQuickCarForm;
window.setDrivetrainFilter = setDrivetrainFilter;
window.filterGarageCars = filterGarageCars;

