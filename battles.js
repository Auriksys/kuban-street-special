/**
 * KubanStreetSpecial - Battles, Kill-List & Duel Simulator Module
 */

function renderBattlesFeed() {
  const container = document.getElementById('battles-feed-container') || document.getElementById('battles-feed');
  const previewContainer = document.getElementById('battles-feed-preview');
  if (!container && !previewContainer) return;


  const battles = KSS.battles;
  if (!battles || battles.length === 0) {
    const emptyHtml = `
      <div class="py-16 text-center text-gray-500 font-mono">
        <div class="text-5xl mb-3">⚔️</div>
        <p class="text-xl text-gray-200 font-bold font-race">ЗАЕЗДОВ ПОКА НЕ ЗАФИКСИРОВАНО</p>
        <p class="text-xs text-gray-400 mt-2 max-w-md mx-auto">Выезжай на трассу, побеждай соперников и вписывай заезды через сайт или бота!</p>
        <div class="mt-6 flex justify-center gap-3">
          <button class="btn-kss-red text-xs py-2.5 px-5" onclick="openModal('battle-register-modal')">
            + ВПИСАТЬ ЗАЕЗД
          </button>
        </div>
      </div>
    `;
    if (container) container.innerHTML = emptyHtml;
    if (previewContainer) previewContainer.innerHTML = emptyHtml;
    return;
  }

  const html = battles.map(b => {
    const disciplineColor = b.discipline.includes('Тоге') ? 'badge-red' : (b.discipline.includes('Дрэг') ? 'badge-volt' : 'badge-cyan');
    const loserTitle = b.loser_callsign ? `${b.loser_callsign} (${b.loser_make} ${b.loser_model})` : (b.loser_make ? `${b.loser_make} ${b.loser_model}` : b.loser_custom_name);
    let proofMedia = '';
    let videoBtn = '';
    if (b.video_proof_url) {
      const vUrl = b.video_proof_url;
      const isVideo = /\.(mp4|webm|mov|m4v)$/i.test(vUrl) || /youtube\.com|youtu\.be|rutube\.ru|vk\.com\/video/i.test(vUrl);
      if (/youtu\.?be/i.test(vUrl)) {
        const match = vUrl.match(/(?:youtu\.be\/|youtube\.com\/(?:embed\/|v\/|watch\?v=|watch\?.+&v=))([\w-]{11})/);
        if (match && match[1]) {
          proofMedia = `
            <div class="mt-3 rounded-xl overflow-hidden border border-white/10 max-w-sm aspect-video bg-black shadow-lg">
              <iframe src="https://www.youtube.com/embed/${match[1]}" class="w-full h-full" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>
            </div>
          `;
        }
      } else if (isVideo) {
        proofMedia = `
          <div class="mt-3 rounded-xl overflow-hidden border border-white/10 max-w-sm bg-black shadow-lg">
            <video src="${vUrl}" controls playsinline preload="metadata" class="w-full max-h-56 object-contain bg-black"></video>
          </div>
        `;
      } else {
        proofMedia = `
          <div class="mt-3 rounded-xl overflow-hidden border border-white/10 max-w-xs max-h-48 bg-black">
            <img src="${vUrl}" class="w-full h-full object-cover cursor-pointer hover:scale-105 transition-transform" onclick="window.open('${vUrl}', '_blank')" title="Открыть Dragy / Телеметрию">
          </div>
        `;
      }
      videoBtn = `
        <a href="${b.video_proof_url}" target="_blank" class="text-xs text-red-400 hover:text-red-300 flex items-center gap-1 font-mono">
          ▶️ ${isVideo ? 'Видео заезда' : 'Dragy телеметрия'} ↗
        </a>
      `;
    }

    return `
      <div class="kss-card p-5 space-y-4">
        <!-- Top row: Discipline & Location & Date -->
        <div class="flex items-center justify-between flex-wrap gap-2 text-xs">
          <div class="flex items-center gap-2">
            <span class="kss-badge ${disciplineColor}">${b.discipline}</span>
            <span class="text-gray-400">📍 <b>${b.spot_name || 'Краснодарский край'}</b></span>
          </div>
          <div class="text-gray-500 font-mono">
            +${b.cred_delta} Street Cred • ${new Date(b.date_time).toLocaleDateString('ru-RU')}
          </div>
        </div>

        <!-- Middle row: Winner vs Loser Comparison -->
        <div class="grid grid-cols-1 md:grid-cols-11 gap-3 items-center bg-[#12141f] p-4 rounded-xl border border-white/5">
          <!-- Winner side -->
          <div class="md:col-span-5 flex items-center gap-3">
            <div class="relative w-16 h-16 rounded-lg overflow-hidden bg-gray-800 flex-shrink-0 border border-lime-400/40">
              <img src="${b.winner_car_photo || 'https://images.unsplash.com/photo-1542282088-72c9c27ed0cd?w=200'}" class="w-full h-full object-cover">
            </div>
            <div>
              <div class="text-[10px] text-lime-400 font-bold uppercase tracking-wider font-race">🏆 ПОБЕДИТЕЛЬ</div>
              <div class="text-base font-bold text-white font-race">${b.winner_make} ${b.winner_model}</div>
              <div class="text-xs text-gray-400 font-medium">👤 ${b.winner_callsign} <span class="text-lime-300 font-mono">(${b.winner_hp} hp)</span></div>
            </div>
          </div>

          <!-- Gap / VS Badge -->
          <div class="md:col-span-1 text-center py-2 md:py-0">
            <div class="inline-block bg-black/60 border border-white/10 px-2 py-1 rounded text-[11px] font-bold text-lime-400 font-mono">
              VS
            </div>
          </div>

          <!-- Loser side -->
          <div class="md:col-span-5 flex items-center justify-end gap-3 text-right">
            <div>
              <div class="text-[10px] text-red-400 font-bold uppercase tracking-wider font-race">ПОРАЖЕНИЕ</div>
              <div class="text-base font-bold text-gray-300 font-race">${b.loser_make ? `${b.loser_make} ${b.loser_model}` : b.loser_custom_name}</div>
              <div class="text-xs text-gray-400 font-medium">👤 ${b.loser_callsign || 'Оппонент'} ${b.loser_hp ? `<span class="text-gray-400 font-mono">(${b.loser_hp} hp)</span>` : ''}</div>
            </div>
            <div class="relative w-16 h-16 rounded-lg overflow-hidden bg-gray-800 flex-shrink-0 border border-white/10 opacity-70">
              <img src="${b.loser_car_photo || 'https://images.unsplash.com/photo-1503376780353-7e6692767b70?w=200'}" class="w-full h-full object-cover">
            </div>
          </div>
        </div>

        <!-- Optional Proof Media (Video or Dragy Slip) -->
        ${proofMedia}

        <!-- Bottom row: Gap description & Notes -->
        <div class="flex items-center justify-between text-xs pt-1 border-t border-white/5 flex-wrap gap-2">
          <div class="flex items-center gap-2">
            <span class="text-gray-400 font-mono">Разрыв на финише:</span>
            <span class="text-lime-300 font-bold font-race px-2 py-0.5 rounded bg-lime-400/10 border border-lime-400/20">${b.gap_description}</span>
          </div>
          ${b.telemetry_notes ? `<div class="text-gray-400 italic text-xs max-w-md truncate">«${b.telemetry_notes}»</div>` : ''}
          ${videoBtn}
        </div>
      </div>
    `;
  }).join('');

  if (container) container.innerHTML = html;
  if (previewContainer) {
    previewContainer.innerHTML = battles.slice(0, 3).map(b => {
      const disciplineColor = b.discipline.includes('Тоге') ? 'badge-red' : (b.discipline.includes('Дрэг') ? 'badge-volt' : 'badge-cyan');
      return `
        <div class="kss-card p-4 flex items-center justify-between gap-3 text-xs">
          <div class="flex items-center gap-3">
            <span class="kss-badge ${disciplineColor}">${b.discipline}</span>
            <div>
              <div class="font-bold text-white font-race text-sm">
                ${b.winner_make} ${b.winner_model} <span class="text-lime-400">ПОБЕДА</span> над ${b.loser_make ? `${b.loser_make} ${b.loser_model}` : b.loser_custom_name}
              </div>
              <div class="text-gray-400 text-[11px]">
                📍 ${b.spot_name || 'Кубань'} • Разрыв: <b class="text-lime-300 font-mono">${b.gap_description}</b>
              </div>
            </div>
          </div>
          <button class="btn-kss-outline text-[11px] py-1 px-2.5 hidden sm:block" onclick="switchTab('battles')">
            Детали →
          </button>
        </div>
      `;
    }).join('');
  }
}

// Submit Battle / Win
async function handleBattleRegistration(e) {
  e.preventDefault();
  const form = e.target;

  const winnerCarId = parseInt(form.winner_car_id.value);
  const winnerCar = KSS.cars.find(c => c.id === winnerCarId);
  const loserCarId = form.loser_car_id.value ? parseInt(form.loser_car_id.value) : null;
  const loserCar = loserCarId ? KSS.cars.find(c => c.id === loserCarId) : null;

  const spotId = form.spot_id.value ? parseInt(form.spot_id.value) : null;
  const spot = spotId ? KSS.spots.find(s => s.id === spotId) : null;

  const payload = {
    discipline: form.discipline.value,
    spot_id: spotId,
    spot_name: spot ? spot.name : form.custom_spot.value || 'Краснодарский край',
    winner_id: winnerCar ? winnerCar.user_id : KSS.currentUser.id,
    winner_car_id: winnerCarId,
    loser_id: loserCar ? loserCar.user_id : null,
    loser_car_id: loserCarId,
    loser_custom_name: loserCar ? '' : form.loser_custom_name.value.trim(),
    gap_description: form.gap_description.value.trim() || '1 корпус',
    telemetry_notes: form.telemetry_notes.value.trim(),
    video_proof_url: form.video_proof_url.value.trim()
  };

  try {
    const res = await api('/api/battles', {
      method: 'POST',
      body: JSON.stringify(payload)
    });

    if (res.status === 'ok') {
      showToast('Заезд зафиксирован! Рейтинг Street Cred обновлен 🏆', 'volt');
      closeModal('battle-register-modal');
      form.reset();

      // Refresh data
      const battlesRes = await api('/api/battles');
      if (battlesRes.status === 'ok') {
        KSS.battles = battlesRes.battles;
        renderBattlesFeed();
      }
      const statsRes = await api('/api/stats');
      if (statsRes.status === 'ok') {
        KSS.stats = statsRes.stats;
        renderStats();
      }
    }
  } catch (err) {
    console.error('Failed to log battle:', err);
  }
}

// Callout a car directly
function calloutCar(carId, carName) {
  openModal('battle-register-modal');
  const loserSel = document.getElementById('battle-loser-car');
  if (loserSel) {
    loserSel.value = carId;
  }
}

// Open simulator with preselected car
function openSimWithCar(carId) {
  closeModal('car-detail-modal');
  switchTab('simulator');
  const sim1 = document.getElementById('sim-car-1');
  if (sim1) sim1.value = carId;
}

// Duel Simulator Execution
async function runDuelSimulation() {
  const car1Id = document.getElementById('sim-car-1')?.value;
  const car2Id = document.getElementById('sim-car-2')?.value;
  const discipline = document.getElementById('sim-discipline')?.value || 'Дрэг 402м';
  const resultBox = document.getElementById('sim-result-box');

  if (!car1Id || !car2Id) {
    showToast('Выберите оба автомобиля для дуэли', 'red');
    return;
  }

  if (car1Id === car2Id) {
    showToast('Выберите разные автомобили!', 'red');
    return;
  }

  // Animation phase: Professional Drag Christmas Tree Lights
  if (resultBox) {
    resultBox.innerHTML = `
      <div class="py-10 text-center space-y-6">
        <div class="inline-flex flex-col items-center gap-2 bg-black/80 border border-white/20 p-5 rounded-2xl shadow-2xl">
          <div class="flex gap-3">
            <div id="tree-amb1" class="tree-light active-yellow"></div>
            <div id="tree-amb2" class="tree-light"></div>
            <div id="tree-amb3" class="tree-light"></div>
          </div>
          <div class="flex gap-3">
            <div id="tree-green" class="tree-light"></div>
          </div>
        </div>

        <div id="tree-status-text" class="text-xl font-black font-race text-yellow-400 tracking-wider">
          🟡 PRE-STAGE: ПРОГРЕВ РЕЗИНЫ И ЗАЦЕП...
        </div>
        <div class="text-xs text-gray-400 font-mono">Телеметрия ELO, развесовка по осям, давление наддува...</div>
      </div>
    `;
    resultBox.classList.remove('hidden');

    // Play optional rev sound if enabled
    if (window.playSfx) window.playSfx('rev');

    setTimeout(() => {
      document.getElementById('tree-amb2')?.classList.add('active-yellow');
      const st = document.getElementById('tree-status-text');
      if (st) st.innerText = '🟡 🟡 STAGED: ЛАУНЧ-КОНТРОЛЬ АКТИВЕН!';
    }, 600);

    setTimeout(() => {
      document.getElementById('tree-amb3')?.classList.add('active-yellow');
      const st = document.getElementById('tree-status-text');
      if (st) st.innerText = '🟡 🟡 🟡 ГОТОВНОСТЬ: 3-2-1...';
    }, 1200);

    setTimeout(() => {
      document.getElementById('tree-green')?.classList.add('active-green');
      const st = document.getElementById('tree-status-text');
      if (st) {
        st.innerText = '🟢 GREEN LIGHT! СТАРТ В ПОЛ!';
        st.className = 'text-2xl font-black font-race text-lime-400 tracking-wider';
      }
      if (window.playSfx) window.playSfx('launch');
    }, 1800);
  }

  try {
    const res = await api('/api/simulate-duel', {
      method: 'POST',
      body: JSON.stringify({ car1_id: car1Id, car2_id: car2Id, discipline: discipline })
    });

    if (res.status === 'ok') {
      setTimeout(() => {
        renderSimulationResult(res);
      }, 2300);
    }
  } catch (err) {
    console.error('Simulation error:', err);
  }
}

function renderSimulationResult(data) {
  const resultBox = document.getElementById('sim-result-box');
  if (!resultBox) return;

  const c1 = data.car1;
  const c2 = data.car2;

  resultBox.innerHTML = `
    <div class="bg-[#121522] border-2 border-lime-400/50 rounded-2xl p-6 space-y-6">
      <div class="text-center space-y-1">
        <span class="kss-badge badge-volt font-mono">РЕЗУЛЬТАТ ТЕЛЕМЕТРИИ KSS</span>
        <h3 class="text-2xl font-black text-white font-race">${data.verdict}</h3>
        <p class="text-xs text-gray-400">Дисциплина: <b>${data.discipline}</b></p>
      </div>

      <!-- Probability Bars -->
      <div class="space-y-4 bg-black/40 p-4 rounded-xl border border-white/5">
        <div class="space-y-1.5">
          <div class="flex justify-between text-sm font-race">
            <span class="font-bold text-white">${c1.name} <span class="text-xs text-gray-400 font-normal">(${c1.hp_ton} л.с./т)</span></span>
            <span class="font-bold text-cyan-400 font-mono">${c1.win_chance}%</span>
          </div>
          <div class="spec-gauge-bar h-3 bg-gray-800">
            <div class="spec-gauge-fill bg-cyan-400" style="width: ${c1.win_chance}%"></div>
          </div>
        </div>

        <div class="space-y-1.5">
          <div class="flex justify-between text-sm font-race">
            <span class="font-bold text-white">${c2.name} <span class="text-xs text-gray-400 font-normal">(${c2.hp_ton} л.с./т)</span></span>
            <span class="font-bold text-red-400 font-mono">${c2.win_chance}%</span>
          </div>
          <div class="spec-gauge-bar h-3 bg-gray-800">
            <div class="spec-gauge-fill bg-red-400" style="width: ${c2.win_chance}%"></div>
          </div>
        </div>
      </div>

      <div class="text-center pt-2">
        <button class="btn-kss-volt px-8" onclick="openBattleLogFromSim('${c1.id}', '${c2.id}')">
          📝 Внести реальный заезд с этим исходом
        </button>
      </div>
    </div>
  `;
}

function openBattleLogFromSim(c1Id, c2Id) {
  openModal('battle-register-modal');
  const win = document.getElementById('battle-winner-car');
  const lose = document.getElementById('battle-loser-car');
  if (win) win.value = c1Id;
  if (lose) lose.value = c2Id;
}

// Initial Listeners
document.addEventListener('DOMContentLoaded', () => {
  document.getElementById('form-register-battle')?.addEventListener('submit', handleBattleRegistration);
  document.getElementById('btn-run-simulation')?.addEventListener('click', runDuelSimulation);

  // Toggle custom loser input when selecting dropdown
  const loserSel = document.getElementById('battle-loser-car');
  const loserCustomWrap = document.getElementById('wrap-loser-custom');
  loserSel?.addEventListener('change', () => {
    if (loserSel.value === '') {
      loserCustomWrap?.classList.remove('hidden');
    } else {
      loserCustomWrap?.classList.add('hidden');
    }
  });
});

async function submitBattleForm() {
  const discipline = document.getElementById('input-battle-discipline')?.value || 'Дрэг 402м';
  const spotId = document.getElementById('battle-spot-id')?.value;
  const winnerCarInput = document.getElementById('input-battle-winner-car') || document.getElementById('battle-winner-car');
  const winnerCarId = parseInt(winnerCarInput?.value || 1);
  const loserCustom = document.getElementById('input-battle-loser-custom')?.value.trim();
  const gap = document.getElementById('input-battle-gap')?.value.trim() || '1 корпус';
  const videoProof = document.getElementById('input-battle-video')?.value.trim() || null;

  const winnerCar = KSS.cars?.find(c => c.id === winnerCarId);
  const winnerId = winnerCar ? winnerCar.user_id : (KSS.currentUser?.id || 1);
  const spot = KSS.spots?.find(s => s.id == spotId);

  const payload = {
    discipline,
    spot_id: spotId ? parseInt(spotId) : null,
    spot_name: spot ? spot.name : 'Кубань',
    winner_id: winnerId,
    winner_car_id: winnerCarId,
    loser_custom_name: loserCustom || 'Оппонент',
    gap_description: gap,
    telemetry_notes: 'Заезд зафиксирован пилотом',
    video_proof_url: videoProof
  };

  try {
    const res = await api('/api/battles', {
      method: 'POST',
      body: JSON.stringify(payload)
    });
    if (res.status === 'ok') {
      showToast('Победа зафиксирована! Рейтинг пилота пересчитан.', 'volt');
      closeModal('battle-register-modal');
      const bRes = await api('/api/battles');
      if (bRes.status === 'ok') {
        KSS.battles = bRes.battles;
        renderBattlesFeed();
      }
    }
  } catch (e) {
    showToast('Ошибка: ' + e.message, 'red');
  }
}
window.submitBattleForm = submitBattleForm;

