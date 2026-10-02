/**
 * KubanStreetSpecial - Live Street Chatter & Forum Module
 * Real-time radio channels for Krasnodar Krai street racers and pilots.
 */

let activeChatChannel = 'general';
let chatPollTimer = null;
let lastMessageId = 0;
let isChatScrolledToBottom = true;

const CHANNELS_CONFIG = {
  'general': {
    title: '#эфир-кубани',
    icon: '💬',
    desc: 'Главный открытый канал пилотов края: сходки, разговоры, обсуждения.'
  },
  'radar': {
    title: '#радар-дпс',
    icon: '🚨',
    desc: 'Оперативная обстановка на дорогах: посты ДПС, камеры, облавы и чистые трассы.'
  },
  'battles': {
    title: '#заезды-402м',
    icon: '⚔️',
    desc: 'Поиск соперников на квотер и ролл-он, пари, вызовы на дуэль и результаты.'
  },
  'tech': {
    title: '#тех-зона',
    icon: '⚙️',
    desc: 'Спек-листы, логи наддува, замеры Dragy, прошивки ЭБУ и подбор резины.'
  }
};

async function initChat() {
  renderChatChannelsList();
  await loadChatMessages();

  // Background auto-refresh every 3.5 seconds
  if (chatPollTimer) clearInterval(chatPollTimer);
  chatPollTimer = setInterval(() => {
    if (KSS.currentTab === 'chat') {
      loadChatMessages(true);
    }
  }, 3500);

  // Setup input key handlers
  const inputEl = document.getElementById('chat-message-input');
  if (inputEl) {
    inputEl.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendChatMessage();
      }
    });
  }

  // Setup scroll listener
  const msgContainer = document.getElementById('chat-messages-scroll');
  if (msgContainer) {
    msgContainer.addEventListener('scroll', () => {
      const threshold = 60;
      const atBottom = msgContainer.scrollHeight - msgContainer.scrollTop - msgContainer.clientHeight < threshold;
      isChatScrolledToBottom = atBottom;
    });
  }
}

function renderChatChannelsList() {
  const container = document.getElementById('chat-channels-bar');
  if (!container) return;

  container.innerHTML = Object.entries(CHANNELS_CONFIG).map(([key, cfg]) => {
    const isActive = key === activeChatChannel;
    return `
      <button onclick="switchChatChannel('${key}')" 
              class="chat-channel-btn px-3 py-2 rounded-xl text-xs font-race font-bold transition-all flex items-center gap-2 whitespace-nowrap ${isActive ? 'bg-lime-400 text-black shadow-lg shadow-lime-400/25' : 'bg-white/5 text-gray-400 hover:text-white hover:bg-white/10 border border-white/5'}">
        <span>${cfg.icon}</span>
        <span>${cfg.title}</span>
      </button>
    `;
  }).join('');

  // Update header title & description
  const headerTitle = document.getElementById('chat-channel-header-title');
  const headerDesc = document.getElementById('chat-channel-header-desc');
  const cfg = CHANNELS_CONFIG[activeChatChannel];
  if (headerTitle && cfg) headerTitle.innerText = `${cfg.icon} ${cfg.title}`;
  if (headerDesc && cfg) headerDesc.innerText = cfg.desc;
}

function switchChatChannel(channel) {
  if (!CHANNELS_CONFIG[channel]) return;
  activeChatChannel = channel;
  renderChatChannelsList();
  lastMessageId = 0;
  isChatScrolledToBottom = true;
  loadChatMessages();
}

async function loadChatMessages(isSilent = false) {
  const container = document.getElementById('chat-messages-container');
  if (!container) return;

  try {
    const res = await api(`/api/chat?channel=${activeChatChannel}&limit=60`);
    if (res && res.status === 'ok') {
      const messages = res.messages || [];
      renderChatMessages(messages);
    }
  } catch (err) {
    if (!isSilent) console.error('Failed to load chat messages:', err);
  }
}

function renderChatMessages(messages) {
  const container = document.getElementById('chat-messages-container');
  const scrollBox = document.getElementById('chat-messages-scroll');
  if (!container) return;

  if (messages.length === 0) {
    container.innerHTML = `
      <div class="py-16 text-center text-gray-500 font-mono text-xs">
        <div class="text-4xl mb-2">📻</div>
        <p class="text-white font-bold font-race text-sm">В ЭФИРЕ ПОКА ТИШИНА</p>
        <p class="text-gray-400 mt-1">Будьте первым, кто напишет сообщение в канал ${CHANNELS_CONFIG[activeChatChannel]?.title || ''}!</p>
      </div>
    `;
    return;
  }

  const currentUser = KSS.currentUser || {};

  container.innerHTML = messages.map(m => {
    const isMe = currentUser.id && m.user_id === currentUser.id;
    const isKssAdmin = m.callsign.includes('Красный_Чайзер') || (m.street_cred && m.street_cred >= 1400);
    const timeStr = m.created_at ? new Date(m.created_at).toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' }) : '';
    const avatar = m.avatar || 'https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=100';

    return `
      <div class="flex gap-3 items-start group transition-colors p-2.5 rounded-2xl hover:bg-white/[0.02] ${isMe ? 'bg-white/[0.015]' : ''}">
        <!-- Avatar -->
        <div class="relative w-10 h-10 rounded-xl overflow-hidden border border-white/10 bg-gray-900 flex-shrink-0">
          <img src="${avatar}" class="w-full h-full object-cover">
          ${isKssAdmin ? '<div class="absolute -bottom-0.5 -right-0.5 w-3 h-3 bg-lime-400 rounded-full border border-black" title="Проверенный пилот KSS"></div>' : ''}
        </div>

        <!-- Content -->
        <div class="flex-1 min-w-0 space-y-1">
          <!-- Author Info Header -->
          <div class="flex items-center justify-between flex-wrap gap-1">
            <div class="flex items-center gap-2 flex-wrap">
              <span class="font-race font-bold text-xs text-white tracking-wide">${m.callsign}</span>
              ${m.car_name ? `<span class="px-1.5 py-0.5 rounded text-[10px] font-mono bg-white/5 border border-white/10 text-lime-300 font-bold">${m.car_name}</span>` : ''}
              ${m.street_cred ? `<span class="text-[10px] font-mono text-gray-500">${m.street_cred} PTS</span>` : ''}
            </div>
            <span class="text-[10px] font-mono text-gray-500">${timeStr}</span>
          </div>

          <!-- Message Text -->
          <div class="text-xs text-gray-200 leading-relaxed font-sans break-words bg-black/40 border border-white/5 rounded-xl p-3">
            ${m.message ? `<div>${escapeHtml(m.message)}</div>` : ''}
            ${renderMediaAttachment(m.image_url, m.media_type)}
          </div>

          <!-- Action & Likes Footer -->
          <div class="flex items-center justify-between pt-0.5 text-[11px] font-mono">
            <button onclick="likeChatMessage(${m.id})" class="inline-flex items-center gap-1.5 text-gray-400 hover:text-red-400 transition-colors py-0.5 px-2 rounded-lg hover:bg-white/5">
              <span>🔥</span>
              <span id="chat-likes-${m.id}" class="font-bold text-white">${m.likes_count || 0}</span>
            </button>

            ${isMe ? `
              <button onclick="deleteChatMessage(${m.id})" class="text-gray-600 hover:text-red-400 transition-colors opacity-0 group-hover:opacity-100 py-0.5 px-1.5" title="Удалить сообщение">
                🗑️
              </button>
            ` : ''}
          </div>
        </div>
      </div>
    `;
  }).join('');

  if (isChatScrolledToBottom && scrollBox) {
    scrollBox.scrollTop = scrollBox.scrollHeight;
  }
}

function renderMediaAttachment(url, mediaType) {
  if (!url) return '';
  const isVideo = mediaType === 'video' || /\.(mp4|webm|mov|m4v)$/i.test(url) || /youtube\.com|youtu\.be|rutube\.ru|vk\.com\/video/i.test(url);

  // YouTube embed
  if (/youtu\.?be/i.test(url)) {
    const match = url.match(/(?:youtu\.be\/|youtube\.com\/(?:embed\/|v\/|watch\?v=|watch\?.+&v=))([\w-]{11})/);
    if (match && match[1]) {
      return `
        <div class="mt-2 rounded-xl overflow-hidden border border-white/10 max-w-md aspect-video bg-black shadow-lg">
          <iframe src="https://www.youtube.com/embed/${match[1]}" class="w-full h-full" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>
        </div>
      `;
    }
  }

  // HTML5 Video Player
  if (isVideo) {
    return `
      <div class="mt-2 rounded-xl overflow-hidden border border-white/10 max-w-md bg-black shadow-xl">
        <video src="${url}" controls playsinline preload="metadata" class="w-full max-h-72 object-contain bg-black"></video>
      </div>
    `;
  }

  // Photo
  return `
    <div class="mt-2 rounded-xl overflow-hidden border border-white/10 max-w-sm max-h-64 bg-black">
      <img src="${url}" class="w-full h-full object-cover cursor-pointer hover:scale-105 transition-transform" onclick="window.open('${url}', '_blank')">
    </div>
  `;
}

// Media Attachment State
let currentChatAttachment = null; // { url, mediaType, filename }

async function handleChatFileUpload(inputEl) {
  const file = inputEl.files && inputEl.files[0];
  if (!file) return;

  const statusBox = document.getElementById('chat-upload-status');
  const statusText = document.getElementById('chat-upload-status-text');
  const isVideo = file.type.startsWith('video/') || /\.(mp4|webm|mov|m4v)$/i.test(file.name);

  try {
    if (statusBox && statusText) {
      statusBox.classList.remove('hidden');
      statusText.innerText = `Загрузка ${isVideo ? 'видео' : 'фото'} (${(file.size / (1024 * 1024)).toFixed(1)} МБ)... ⏳`;
    }

    const res = await uploadFileToServer(file);
    if (res && res.url) {
      currentChatAttachment = {
        url: res.url,
        mediaType: res.media_type || (isVideo ? 'video' : 'image'),
        filename: res.filename
      };
      renderChatAttachmentPreview();
      showToast(`${res.media_type === 'video' ? 'Видео' : 'Фото'} прикреплено! ✅`, 'volt');
    }
  } catch (err) {
    showToast(`Ошибка: ${err.message}`, 'red');
  } finally {
    if (statusBox) statusBox.classList.add('hidden');
    inputEl.value = '';
  }
}

function onChatUrlInput(url) {
  url = url.trim();
  if (!url) {
    clearChatAttachment();
    return;
  }
  const isVideo = /\.(mp4|webm|mov|m4v)$/i.test(url) || /youtube\.com|youtu\.be|rutube\.ru|vk\.com\/video/i.test(url);
  currentChatAttachment = {
    url: url,
    mediaType: isVideo ? 'video' : 'image',
    filename: url.split('/').pop() || 'Ссылка на медиа'
  };
  renderChatAttachmentPreview();
}

function renderChatAttachmentPreview() {
  const previewBox = document.getElementById('chat-attachment-preview');
  const container = document.getElementById('chat-preview-media-container');
  if (!previewBox || !container) return;

  if (!currentChatAttachment || !currentChatAttachment.url) {
    previewBox.classList.add('hidden');
    container.innerHTML = '';
    return;
  }

  previewBox.classList.remove('hidden');
  const isVideo = currentChatAttachment.mediaType === 'video';

  container.innerHTML = `
    <div class="w-10 h-10 rounded-lg overflow-hidden bg-white/5 border border-white/10 flex items-center justify-center flex-shrink-0">
      ${isVideo 
        ? `<span class="text-xl">🎥</span>` 
        : `<img src="${currentChatAttachment.url}" class="w-full h-full object-cover">`}
    </div>
    <div class="text-xs font-mono min-w-0">
      <div class="text-white font-bold truncate max-w-[200px]">${currentChatAttachment.filename}</div>
      <div class="text-[10px] text-lime-400 font-bold">${isVideo ? 'Видео прикреплено' : 'Фото прикреплено'}</div>
    </div>
  `;
}

function clearChatAttachment() {
  currentChatAttachment = null;
  const imgInput = document.getElementById('chat-image-input');
  if (imgInput) imgInput.value = '';
  renderChatAttachmentPreview();
}

async function sendChatMessage() {
  const inputEl = document.getElementById('chat-message-input');
  if (!inputEl) return;

  const text = inputEl.value.trim();
  const mediaUrl = currentChatAttachment ? currentChatAttachment.url : (document.getElementById('chat-image-input')?.value.trim() || null);
  const mediaType = currentChatAttachment ? currentChatAttachment.mediaType : 'image';

  if (!text && !mediaUrl) {
    showToast('Введите текст или прикрепите фото/видео!', 'red');
    return;
  }

  const u = KSS.currentUser || { id: 1, callsign: 'Пилот' };
  const userCar = u.car || (KSS.cars ? KSS.cars.find(c => c.user_id === u.id) : null);
  const carStr = userCar ? `${userCar.make} ${userCar.model} (${userCar.hp} hp)` : '';

  const payload = {
    user_id: u.id,
    callsign: u.callsign,
    avatar: u.avatar || 'https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=150',
    car_name: carStr,
    channel: activeChatChannel,
    message: text,
    image_url: mediaUrl || null,
    media_type: mediaType
  };

  try {
    inputEl.value = '';
    clearChatAttachment();
    toggleChatImageInput(false);

    const res = await api('/api/chat', {
      method: 'POST',
      body: JSON.stringify(payload)
    });

    if (res && res.status === 'ok') {
      isChatScrolledToBottom = true;
      await loadChatMessages();
      if (typeof showToast === 'function') {
        showToast('Сообщение отправлено в эфир 📻', 'volt');
      }
    }
  } catch (err) {
    console.error('Failed to send chat message:', err);
    showToast('Ошибка отправки: ' + err.message, 'red');
  }
}

async function likeChatMessage(messageId) {
  try {
    const res = await api('/api/chat/like', {
      method: 'POST',
      body: JSON.stringify({ message_id: messageId })
    });
    if (res && res.status === 'ok') {
      const badge = document.getElementById(`chat-likes-${messageId}`);
      if (badge) badge.innerText = res.likes_count;
    }
  } catch (e) {
    console.error('Failed to like message:', e);
  }
}

async function deleteChatMessage(messageId) {
  if (!confirm('Удалить это сообщение?')) return;
  try {
    const res = await api(`/api/chat/${messageId}`, { method: 'DELETE' });
    if (res && res.status === 'ok') {
      await loadChatMessages();
      showToast('Сообщение удалено', 'cyan');
    }
  } catch (e) {
    console.error('Failed to delete message:', e);
  }
}

function toggleChatImageInput(show = null) {
  const box = document.getElementById('chat-image-input-box');
  if (!box) return;
  if (show === null) {
    box.classList.toggle('hidden');
  } else if (show) {
    box.classList.remove('hidden');
  } else {
    box.classList.add('hidden');
  }
}

function escapeHtml(str) {
  if (!str) return '';
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

// Global exports
window.initChat = initChat;
window.switchChatChannel = switchChatChannel;
window.sendChatMessage = sendChatMessage;
window.likeChatMessage = likeChatMessage;
window.deleteChatMessage = deleteChatMessage;
window.toggleChatImageInput = toggleChatImageInput;
window.loadChatMessages = loadChatMessages;
window.handleChatFileUpload = handleChatFileUpload;
window.onChatUrlInput = onChatUrlInput;
window.clearChatAttachment = clearChatAttachment;
