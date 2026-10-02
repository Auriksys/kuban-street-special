/**
 * KubanStreetSpecial - News & Announcements Module
 */

function renderNews() {
  const container = document.getElementById('news-feed-list');
  const radarContainer = document.getElementById('news-radar-preview');
  if (!container && !radarContainer) return;

  const newsList = KSS.news || [];

  if (newsList.length === 0) {
    const emptyHtml = `
      <div class="col-span-full py-16 text-center text-gray-500 font-mono">
        <div class="text-4xl mb-3">📰</div>
        <p class="text-lg text-gray-300 font-bold font-race">НОВОСТЕЙ И АНОНСОВ ПОКА НЕТ</p>
        <p class="text-xs text-gray-500 mt-1">Администратор скоро опубликует расписание заездов и сходки через панель управления.</p>
      </div>
    `;
    if (container) container.innerHTML = emptyHtml;
    if (radarContainer) radarContainer.innerHTML = emptyHtml;
    return;
  }

  const html = newsList.map(n => {
    const dateStr = n.created_at ? new Date(n.created_at).toLocaleDateString('ru-RU', { day: 'numeric', month: 'long', hour: '2-digit', minute: '2-digit' }) : '';
    const imgHtml = n.image_url ? `
      <div class="relative h-56 sm:h-72 w-full overflow-hidden bg-black/60 rounded-xl mb-4">
        <img src="${n.image_url}" alt="${n.title}" class="w-full h-full object-cover" onerror="this.parentElement.style.display='none'">
        <div class="absolute inset-0 bg-gradient-to-t from-[#0e111a] via-transparent to-transparent"></div>
        <div class="absolute top-3 left-3">
          <span class="kss-badge badge-volt">${n.category || 'Анонс'}</span>
        </div>
      </div>
    ` : '';

    return `
      <article class="kss-card p-6 space-y-3">
        ${imgHtml}
        <div class="flex items-center justify-between gap-2 flex-wrap text-xs text-gray-400 font-mono">
          <span class="text-lime-400 font-bold">👤 ${n.author || 'Администрация KSS'}</span>
          <span>📅 ${dateStr}</span>
        </div>
        <h3 class="text-xl sm:text-2xl font-black text-white font-race tracking-wide">${n.title}</h3>
        <p class="text-sm text-gray-300 leading-relaxed whitespace-pre-line">${n.content}</p>
      </article>
    `;
  }).join('');

  if (container) container.innerHTML = html;
  if (radarContainer) {
    const top2 = newsList.slice(0, 2);
    radarContainer.innerHTML = top2.map(n => `
      <div class="kss-card p-4 flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
        ${n.image_url ? `<img src="${n.image_url}" class="w-20 h-20 rounded-xl object-cover flex-shrink-0 border border-white/10" onerror="this.style.display='none'">` : ''}
        <div class="space-y-1 flex-1">
          <div class="flex items-center gap-2">
            <span class="kss-badge badge-volt">${n.category || 'Анонс'}</span>
            <span class="text-[11px] text-gray-400 font-mono">${n.created_at ? new Date(n.created_at).toLocaleDateString('ru-RU') : ''}</span>
          </div>
          <h4 class="text-base font-bold text-white font-race">${n.title}</h4>
          <p class="text-xs text-gray-400 line-clamp-2">${n.content}</p>
        </div>
        <button class="btn-kss-outline text-xs whitespace-nowrap" onclick="switchTab('news')">Читать →</button>
      </div>
    `).join('');
  }
}
window.renderNews = renderNews;
