"""
KubanStreetSpecial - Telegram Bot Engine
Zero-dependency Telegram Bot powered by standard Python urllib.
Features:
- WebApp integration
- Garage & Car Specs lookup
- Spots of Krasnodar Krai with radar/difficulty warnings
- Street Cred Leaderboard
- Quick Battle registration
- Head-to-Head race outcome simulator
- Fallback interactive console simulator if token is not yet configured
"""

import os
import sys
import json
import time
import urllib.request
import urllib.parse
import uuid
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from db.database import get_db, init_db, add_chat_message

# Configuration
CONFIG_PATH = os.path.join(BASE_DIR, 'bot_config.json')

def load_config():
    cfg = {}
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                cfg = json.load(f)
        except Exception:
            pass
    if not cfg:
        cfg = {
            "bot_token": os.environ.get("TELEGRAM_BOT_TOKEN", "8907155757:AAH4tjMlCIZ4pYH_Y5u9ieAB4nRgKNH0d0A"),
            "bot_username": "@Kuban_Streetbot",
            "webapp_url": "http://localhost:8080",
            "channel_link": "https://t.me/kubanstreet",
            "admin_ids": []
        }
    # Auto-detect cloud host URL (Render, Koyeb, Railway)
    cloud_url = os.environ.get("RENDER_EXTERNAL_URL") or os.environ.get("PUBLIC_URL")
    if cloud_url:
        cfg["webapp_url"] = cloud_url.rstrip('/')
    return cfg

def save_config(cfg):
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)

# Global Conversation State Machine for Multi-Step Wizards
USER_STATES = {}

class TelegramBotClient:
    def __init__(self, token):
        self.token = token
        self.api_url = f"https://api.telegram.org/bot{token}"
        self.offset = 0

    def request(self, method, data=None):
        url = f"{self.api_url}/{method}"
        headers = {'Content-Type': 'application/json'}
        req_data = json.dumps(data).encode('utf-8') if data else None
        req = urllib.request.Request(url, data=req_data, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=35) as resp:
                result = json.loads(resp.read().decode('utf-8'))
                if result.get('ok'):
                    return result.get('result')
                return None
        except Exception as e:
            # print(f"API Error [{method}]: {e}")
            return None

    def send_message(self, chat_id, text, reply_markup=None, parse_mode='HTML'):
        payload = {
            'chat_id': chat_id,
            'text': text,
            'parse_mode': parse_mode
        }
        if reply_markup:
            payload['reply_markup'] = reply_markup
        return self.request('sendMessage', payload)

    def answer_callback(self, callback_query_id, text=None):
        payload = {'callback_query_id': callback_query_id}
        if text:
            payload['text'] = text
        return self.request('answerCallbackQuery', payload)

    def get_file(self, file_id):
        res = self.request('getFile', {'file_id': file_id})
        if res and 'file_path' in res:
            return f"https://api.telegram.org/file/bot{self.token}/{res['file_path']}"
    def set_commands(self):

        commands = [
            {"command": "start", "description": "🏁 Главное меню и статус"},
            {"command": "car", "description": "🏎️ Анкета: добавить авто в гараж"},
            {"command": "mycar", "description": "🚗 Мой боевой автомобиль"},
            {"command": "garage", "description": "🏁 Гараж боевых машин Кубани"},
            {"command": "spots", "description": "⛰️ Споты, перевалы и координаты"},
            {"command": "top", "description": "🏆 Рейтинг пилотов Street Cred"},
            {"command": "auth", "description": "🔑 Вход на сайт (код/ссылка)"},
            {"command": "profile", "description": "🪪 Моя лицензия пилота"},
            {"command": "chat", "description": "💬 Уличный эфир & Форум пилотов"},
            {"command": "callsign", "description": "✍️ Сменить позывной"},
            {"command": "sim", "description": "⚔️ Симулятор дуэли 402м/Тоге"},
            {"command": "win", "description": "📝 Вписать победу в заезде"},
            {"command": "cancel", "description": "❌ Отменить заполнение анкеты"},
            {"command": "help", "description": "❓ Справка по всем командам"}
        ]
        res = self.request('setMyCommands', {'commands': commands})
        if res:
            print("✅ Официальные команды бота зарегистрированы в Telegram!")
        return res

    def get_updates(self):
        payload = {
            'offset': self.offset,
            'timeout': 20,
            'allowed_updates': ['message', 'callback_query']
        }
        res = self.request('getUpdates', payload)
        if res and isinstance(res, list):
            updates = []
            for item in res:
                self.offset = item['update_id'] + 1
                updates.append(item)
            return updates
        return []

def save_telegram_file(client, file_id, prefix='tg_file', default_ext='.jpg'):
    """Downloads a photo or video from Telegram Bot API and saves to static/uploads/"""
    try:
        download_url = client.get_file(file_id)
        if not download_url:
            return None
        ext = default_ext
        filename_part = download_url.split('/')[-1]
        if '.' in filename_part:
            parsed_ext = '.' + filename_part.split('.')[-1].lower()
            if parsed_ext in ['.jpg', '.jpeg', '.png', '.webp', '.mp4', '.mov', '.webm', '.m4v']:
                ext = parsed_ext
        filename = f"{prefix}_{int(time.time())}_{uuid.uuid4().hex[:6]}{ext}"
        dest_path = os.path.join(BASE_DIR, 'static', 'uploads', filename)
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        req = urllib.request.Request(download_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=40) as resp:
            with open(dest_path, 'wb') as f:
                f.write(resp.read())
        return f"/uploads/{filename}"
    except Exception as e:
        print("save_telegram_file error:", e)
        return None

# Logic handlers
def get_main_keyboard(webapp_url):
    return {
        "keyboard": [
            [{"text": "🚗 Анкета авто"}, {"text": "🏎️ Моя машина"}],
            [{"text": "🏁 Гараж Кубани"}, {"text": "⛰️ Споты & Карта"}],
            [{"text": "🔑 Вход на сайт"}, {"text": "🏆 Топ пилотов"}],
            [{"text": "🪪 Моя лицензия"}, {"text": "⚔️ Дуэль-симулятор"}],
            [{"text": "❓ Все команды"}, {"text": "🌐 Открыть сайт KSS", "web_app": {"url": webapp_url}}]
        ],
        "resize_keyboard": True
    }

def handle_auth(client, chat_id, telegram_id, username, first_name, webapp_url="http://localhost:8080"):
    import random
    code = f"{random.randint(1000, 9999)}"
    conn = get_db()
    c = conn.cursor()

    # Pre-create or ensure user exists in users table
    c.execute('SELECT id FROM users WHERE auth_id = ? OR telegram_handle = ?', (str(telegram_id), f"@{username}"))
    urow = c.fetchone()
    if not urow:
        c.execute('''
            INSERT INTO users (username, callsign, name, avatar, bio, auth_provider, auth_id, telegram_handle, city, street_cred, wins, losses)
            VALUES (?, ?, ?, 'https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=150', 'Пилот Telegram KSS', 'telegram', ?, ?, 'Краснодар', 1000, 0, 0)
        ''', (f"tg_{telegram_id}", username or first_name, first_name, str(telegram_id), f"@{username}" if username else ""))
        conn.commit()

    c.execute('DELETE FROM auth_codes WHERE telegram_id = ?', (str(telegram_id),))
    c.execute('''
        INSERT OR REPLACE INTO auth_codes (code, telegram_id, username, first_name, photo_url)
        VALUES (?, ?, ?, ?, ?)
    ''', (code, str(telegram_id), username or first_name, first_name, "https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=150"))
    conn.commit()
    conn.close()

    text = (
        f"🔑 <b>ТВОЙ КОД ДЛЯ ВХОДА НА САЙТ:</b>\n\n"
        f"👉 <code>{code}</code> 👈\n\n"
        f"1. Введи этот 4-значный код на сайте в окне авторизации:\n"
        f"👉 <b>{webapp_url}</b>\n\n"
        f"Или нажми на ссылку ниже для мгновенного входа в 1 клик:\n"
        f"🔗 <b>{webapp_url}/?code={code}</b>\n\n"
        f"💡 <i>Также ты можешь просто ввести свой никнейм <b>@{username or first_name}</b> на сайте и войти мгновенно без кода!</i>"
    )
    if client:
        client.send_message(chat_id, text)
    return text

def handle_start(client, chat_id, username, first_name, webapp_url):
    text = (
        f"🏁 <b>ДОБРО ПОЖАЛОВАТЬ В KUBAN STREET SPECIAL (KSS)!</b>\n\n"
        f"Салют, <b>{first_name}</b>! Ты подключился к единой закрытой платформе околоспортивных авто и ночных заездов Краснодарского края.\n\n"
        f"<b>Что умеет KSS:</b>\n"
        f"• 🚗 <b>Реестр боевых авто:</b> Спек-листы, мощности от 200 до 800+ л.с., доработки моторов (1JZ, B58, EA888, 16V Турбо)\n"
        f"• ⚔️ <b>Килл-лист и победы:</b> Фиксация побед в дрэге (402м, ролл) и горном тоге (Шаумян, Семь Ветров)\n"
        f"• 📍 <b>Интерактивные споты:</b> Радары, покрытие, шпильки и время сборов\n"
        f"• 🏅 <b>Street Cred ELO:</b> Рейтинг пилотов и синдикатов Кубани\n\n"
        f"<i>Используй кнопки внизу или запусти полную Web-версию платформы:</i>"
    )
    inline_kb = {
        "inline_keyboard": [
            [{"text": "⚡ Открыть Веб-Платформу KSS", "web_app": {"url": webapp_url}}],
            [{"text": "📢 Наш канал: @kubanstreet", "url": "https://t.me/kubanstreet"}],
            [{"text": "🚗 Каталог Машин", "callback_data": "cmd_garage"}, {"text": "⛰️ Трассы Края", "callback_data": "cmd_spots"}],
            [{"text": "🏆 Топ Пилотов", "callback_data": "cmd_top"}, {"text": "⚔️ Дуэль-калькулятор", "callback_data": "cmd_sim"}]
        ]
    }
    if client:
        client.send_message(chat_id, text, reply_markup=inline_kb)
        client.send_message(chat_id, "Меню быстрого доступа активировано:", reply_markup=get_main_keyboard(webapp_url))
    return text

def handle_garage(client, chat_id):
    conn = get_db()
    c = conn.cursor()
    c.execute('''
        SELECT c.*, u.callsign, u.city, t.tag as team_tag
        FROM cars c
        JOIN users u ON c.user_id = u.id
        LEFT JOIN teams t ON u.team_id = t.id
        ORDER BY c.hp DESC
        LIMIT 6
    ''')
    cars = c.fetchall()
    conn.close()

    text = "🏎️ <b>ГЛАВНЫЙ ГАРАЖ КРАСНОДАРСКОГО КРАЯ:</b>\n\n"
    for car in cars:
        tag_str = f"[{car['team_tag']}] " if car['team_tag'] else ""
        text += (
            f"<b>{car['make']} {car['model']} {car['generation']}</b>\n"
            f"👤 Пилот: <i>{tag_str}{car['callsign']}</i> ({car['city']})\n"
            f"⚡ Мощность: <b>{car['hp']} л.с.</b> | {car['torque']} Нм | {car['drivetrain']} | {car['aspiration']}\n"
            f"⏱️ 0-100: <b>{car['zero_to_hundred']}с</b> | 1/4 мили: <b>{car['quarter_mile']}с</b>\n"
            f"🔧 Мотор: <code>{car['engine_code']}</code>\n"
            f"────────────────────────\n"
        )
    text += "\n<i>Всего зарегистрировано машин в реестре: 6+. Для полной телеметрии открой веб-версию.</i>"
    if client:
        client.send_message(chat_id, text)
    return text

def handle_spots(client, chat_id):
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM spots ORDER BY difficulty DESC')
    spots = c.fetchall()
    conn.close()

    text = "⛰️ <b>КУЛЬТОВЫЕ СПОТЫ И ПЕРЕВАЛЫ КУБАНИ:</b>\n\n"
    for s in spots:
        diff_stars = "⭐" * s['difficulty']
        type_badge = "🏁 ДРЭГ" if s['type'] == 'Дрэг' else ("⛰️ ТОГЕ" if s['type'] == 'Тоге' else "💨 РОЛЛ")
        text += (
            f"📍 <b>{s['name']}</b> ({s['city']})\n"
            f"• Тип: <b>{type_badge}</b> | Сложность: {diff_stars}\n"
            f"• Длина: {s['length_km']} км | Перепад: +{s['elevation_gain_m']}м\n"
            f"• Внимание: ⚠️ <b>{s['danger_level']}</b>\n"
            f"• Время сбора: <i>{s['recommended_time']}</i>\n"
            f"• Покрытие: {s['surface']}\n\n"
        )
    text += "<i>Соблюдайте безопасность, прогревайте резину и не выезжайте на перевал в туман!</i>"
    if client:
        client.send_message(chat_id, text)
    return text

def handle_top(client, chat_id):
    conn = get_db()
    c = conn.cursor()
    c.execute('''
        SELECT u.callsign, u.street_cred, u.wins, u.losses, u.city,
               c.make, c.model, c.hp, t.tag as team_tag
        FROM users u
        LEFT JOIN cars c ON c.user_id = u.id AND c.is_primary = 1
        LEFT JOIN teams t ON u.team_id = t.id
        ORDER BY u.street_cred DESC
        LIMIT 10
    ''')
    pilots = c.fetchall()
    conn.close()

    text = "🏆 <b>ТАБЛИЦА СЛАВЫ: ТОП ПИЛОТОВ КУБАНИ</b>\n\n"
    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣"]
    for idx, p in enumerate(pilots):
        medal = medals[idx] if idx < len(medals) else f"{idx+1}."
        tag = f"[{p['team_tag']}] " if p['team_tag'] else ""
        car_str = f"{p['make']} {p['model']} ({p['hp']} hp)" if p['make'] else "Пешком"
        wr = round((p['wins'] / max(1, p['wins'] + p['losses'])) * 100)
        text += (
            f"{medal} <b>{tag}{p['callsign']}</b> — <b>{p['street_cred']} PTS</b>\n"
            f"   🚗 {car_str}\n"
            f"   📊 Побед: {p['wins']} | Поражений: {p['losses']} | Винрейт: {wr}%\n\n"
        )
    if client:
        client.send_message(chat_id, text)
    return text

def handle_sim(client, chat_id):
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT id, make, model, hp, weight, drivetrain FROM cars ORDER BY hp DESC LIMIT 2')
    cars = c.fetchall()
    conn.close()

    if len(cars) < 2:
        return "Недостаточно авто для симуляции."

    car1 = cars[0]
    car2 = cars[1]

    ptw1 = round((car1['hp'] / car1['weight']) * 1000, 1)
    ptw2 = round((car2['hp'] / car2['weight']) * 1000, 1)

    text = (
        f"⚔️ <b>СИМУЛЯТОР УЛИЧНОЙ ДУЭЛИ</b>\n\n"
        f"🔴 <b>{car1['make']} {car1['model']}</b>: {car1['hp']} hp, {car1['weight']} кг ({ptw1} л.с./т)\n"
        f"🔵 <b>{car2['make']} {car2['model']}</b>: {car2['hp']} hp, {car2['weight']} кг ({ptw2} л.с./т)\n\n"
        f"<b>Прогноз на 402 метра (Дрэг):</b>\n"
        f"Благодаря полному приводу и стабильному лаунчу преимущество на первых 100 метрах. "
        f"Прогноз исхода: <b>{car2['make']} {car2['model']}</b> навезет 1-1.5 корпуса на старте!\n\n"
        f"<i>Для выбора любой пары автомобилей используй симулятор на сайте!</i>"
    )
    if client:
        client.send_message(chat_id, text)
    return text

def handle_profile(client, chat_id, username, first_name):
    conn = get_db()
    c = conn.cursor()
    # Find user by tg handle or first pilot
    c.execute('SELECT * FROM users WHERE telegram_handle LIKE ? OR username LIKE ? LIMIT 1', (f"%{username}%", f"%{username}%"))
    user = c.fetchone()
    if not user:
        c.execute('SELECT * FROM users ORDER BY street_cred DESC LIMIT 1')
        user = c.fetchone()

    # Find user's primary car
    car = None
    if user:
        c.execute('SELECT * FROM cars WHERE user_id = ? AND is_primary = 1 LIMIT 1', (user['id'],))
        car = c.fetchone()

    conn.close()

    car_str = f"{car['make']} {car['model']} ({car['hp']} hp, {car['drivetrain']})" if car else "Машина на сборке в боксе"
    wr = round((user['wins'] / max(1, user['wins'] + user['losses'])) * 100) if user else 0

    text = (
        f"🪪 <b>KUBAN STREET SPECIAL — ЛИЦЕНЗИЯ ПИЛОТА</b>\n\n"
        f"👤 Позывной: <b>{user['callsign'] if user else first_name}</b>\n"
        f"📍 Регион: <b>{user['city'] if user else 'Краснодарский край'} (93/123/23)</b>\n"
        f"🏎️ Боевой аппарат: <b>{car_str}</b>\n\n"
        f"📊 <b>СТАТИСТИКА БАТАЛИЙ:</b>\n"
        f"• Рейтинг авторитета: <b>{user['street_cred'] if user else 1000} PTS</b>\n"
        f"• Победы / Поражения: <b>{user['wins'] if user else 0} W / {user['losses'] if user else 0} L</b>\n"
        f"• Винрейт: <b>{wr}%</b>\n\n"
        f"<i>Номер в закрытом реестре: #KSS-93-{1000 + (user['id'] if user else 1)}</i>"
    )
    if client:
        client.send_message(chat_id, text)
    return text

def handle_register_battle_bot(client, chat_id):
    text = (
        f"📝 <b>РЕГИСТРАЦИЯ ПОБЕДЫ В ЗАЕЗДЕ ЧЕРЕЗ БОТА</b>\n\n"
        f"Чтобы зафиксировать заезд прямо из чата, отправь сообщение в формате:\n\n"
        f"<code>/win [Дисциплина] [Спот] [Кого объехал] [Разрыв]</code>\n\n"
        f"<b>Пример:</b>\n"
        f"<code>/win Дрэг OZ_Mall BMW_M5 2_корпуса</code>\n"
        f"<code>/win Тоге Семь_Ветров Silvia_S15 40_метров</code>\n\n"
        f"<i>Либо нажми кнопку 'Открыть KubanStreetSpecial' внизу и внеси заезд через удобную форму на сайте!</i>"
    )
    if client:
        client.send_message(chat_id, text)
    return text

def handle_car_search(client, chat_id, query):
    conn = get_db()
    c = conn.cursor()
    q = f"%{query.strip()}%"
    c.execute('''
        SELECT c.*, u.callsign, u.city, t.tag as team_tag
        FROM cars c
        JOIN users u ON c.user_id = u.id
        LEFT JOIN teams t ON u.team_id = t.id
        WHERE c.make LIKE ? OR c.model LIKE ? OR c.engine_code LIKE ? OR u.callsign LIKE ?
        LIMIT 3
    ''', (q, q, q, q))
    cars = c.fetchall()
    conn.close()

    if not cars:
        return None

    text = f"🔍 <b>РЕЗУЛЬТАТЫ ПОИСКА ПО ГАРАЖУ («{query}»):</b>\n\n"
    for car in cars:
        tag_str = f"[{car['team_tag']}] " if car['team_tag'] else ""
        ptw = round((car['hp'] / car['weight']) * 1000)
        text += (
            f"🏎️ <b>{car['make']} {car['model']} {car['generation']}</b>\n"
            f"👤 Пилот: <i>{tag_str}{car['callsign']}</i> ({car['city']})\n"
            f"⚡ Мощность: <b>{car['hp']} л.с.</b> | {car['weight']} кг ({ptw} л.с./т)\n"
            f"⏱️ 0-100: <b>{car['zero_to_hundred']}с</b> | 1/4 мили: <b>{car['quarter_mile']}с</b>\n"
            f"🔧 Мотор: <code>{car['engine_code']}</code> | {car['drivetrain']} | {car['aspiration']}\n"
            f"────────────────────────\n"
        )
    if client:
        client.send_message(chat_id, text)
    return text

def handle_start_car_wizard(client, chat_id, webapp_url):
    USER_STATES[chat_id] = {
        'step': 'WAITING_MAKE_MODEL',
        'data': {}
    }
    cancel_kb = {
        "keyboard": [
            [{"text": "❌ Отменить анкету"}]
        ],
        "resize_keyboard": True
    }
    text = (
        "🏎️ <b>АНКЕТА РЕГИСТРАЦИИ АВТОМОБИЛЯ (Шаг 1 из 5)</b>\n\n"
        "Напишите <b>Марку и Модель</b> вашего автомобиля:\n"
        "<i>Например: Toyota Mark II, BMW M5, ВАЗ 2107, Golf R, Nissan Silvia</i>\n\n"
        "💡 <i>(Для отмены в любой момент напишите /cancel или нажмите кнопку внизу)</i>"
    )
    if client:
        client.send_message(chat_id, text, reply_markup=cancel_kb)
    return text

def handle_car_wizard_step(client, chat_id, user_id, username, first_name, text, photo_list=None, video_obj=None, webapp_url="http://localhost:8080"):
    state = USER_STATES.get(chat_id)
    if not state:
        return False

    clean_text = (text or '').strip()

    # Cancel check
    if clean_text in ['/cancel', '❌ Отменить анкету', 'отмена', 'cancel']:
        USER_STATES.pop(chat_id, None)
        msg = "❌ <b>Заполнение анкеты отменено.</b> Вы можете начать заново в любой момент командой /car."
        if client:
            client.send_message(chat_id, msg, reply_markup=get_main_keyboard(webapp_url))
        return True

    step = state.get('step')

    # STEP 1: MAKE & MODEL
    if step == 'WAITING_MAKE_MODEL':
        if not clean_text:
            client.send_message(chat_id, "Пожалуйста, введите марку и модель текстом (например: <i>Toyota Mark II</i>):")
            return True
        
        parts = clean_text.split(maxsplit=1)
        make = parts[0]
        model = parts[1] if len(parts) > 1 else 'Custom'
        state['data']['make'] = make
        state['data']['model'] = model
        state['step'] = 'WAITING_HP'

        msg = (
            f"✅ Автомобиль: <b>{make} {model}</b>\n\n"
            f"⚡ <b>Шаг 2 из 5: Мощность двигателя</b>\n"
            f"Сколько реальных <b>лошадиных сил (л.с.)</b> под капотом?\n"
            f"<i>Напишите число (например: <b>380</b> или <b>500</b>):</i>"
        )
        if client:
            client.send_message(chat_id, msg)
        return True

    # STEP 2: HORSEPOWER (HP)
    elif step == 'WAITING_HP':
        import re
        nums = re.findall(r'\d+', clean_text)
        if not nums:
            client.send_message(chat_id, "⚠️ Укажите мощность числом (например: <code>420</code>):")
            return True
        hp = int(nums[0])
        state['data']['hp'] = hp
        state['step'] = 'WAITING_DRIVETRAIN'

        dt_kb = {
            "keyboard": [
                [{"text": "RWD (Задний)"}, {"text": "AWD (Полный)"}],
                [{"text": "FWD (Передний)"}, {"text": "❌ Отменить анкету"}]
            ],
            "resize_keyboard": True
        }
        msg = (
            f"✅ Мощность зафиксирована: <b>{hp} л.с.</b>\n\n"
            f"⚙️ <b>Шаг 3 из 5: Тип привода</b>\n"
            f"Какой привод установлен на автомобиле? (нажмите кнопку или напишите):"
        )
        if client:
            client.send_message(chat_id, msg, reply_markup=dt_kb)
        return True

    # STEP 3: DRIVETRAIN
    elif step == 'WAITING_DRIVETRAIN':
        up = clean_text.upper()
        if 'AWD' in up or 'ПОЛН' in up:
            dt = 'AWD'
        elif 'FWD' in up or 'ПЕРЕД' in up:
            dt = 'FWD'
        else:
            dt = 'RWD'
        state['data']['drivetrain'] = dt
        state['step'] = 'WAITING_CITY'

        city_kb = {
            "keyboard": [
                [{"text": "Краснодар"}, {"text": "Новороссийск"}],
                [{"text": "Сочи"}, {"text": "Армавир"}],
                [{"text": "Анапа"}, {"text": "❌ Отменить анкету"}]
            ],
            "resize_keyboard": True
        }
        msg = (
            f"✅ Привод: <b>{dt}</b>\n\n"
            f"📍 <b>Шаг 4 из 5: Город базирования</b>\n"
            f"В каком городе Краснодарского края обитает боевой аппарат?\n"
            f"<i>Выберите город или впишите свой:</i>"
        )
        if client:
            client.send_message(chat_id, msg, reply_markup=city_kb)
        return True

    # STEP 4: CITY
    elif step == 'WAITING_CITY':
        city = clean_text or 'Краснодар'
        state['data']['city'] = city
        state['step'] = 'WAITING_PHOTO'

        skip_kb = {
            "keyboard": [
                [{"text": "Пропустить фото"}, {"text": "❌ Отменить анкету"}]
            ],
            "resize_keyboard": True
        }
        msg = (
            f"✅ Город: <b>{city}</b>\n\n"
            f"📸 <b>Шаг 5 из 5: Фотография или видео автомобиля</b>\n"
            f"Отправьте фото или видеоролик вашего автомобиля в чат прямо сейчас!\n\n"
            f"<i>💡 Если фото/видео нет под рукой, нажмите 'Пропустить фото', и мы поставим стильное изображение!</i>"
        )
        if client:
            client.send_message(chat_id, msg, reply_markup=skip_kb)
        return True

    # STEP 5: PHOTO OR VIDEO
    elif step == 'WAITING_PHOTO':
        photo_url = "https://images.unsplash.com/photo-1503376780353-7e6692767b70?w=800"
        if video_obj and client:
            saved = save_telegram_file(client, video_obj['file_id'], prefix=f"tg_car_{user_id}", default_ext='.mp4')
            if saved:
                photo_url = saved
        elif photo_list and client:
            saved = save_telegram_file(client, photo_list[-1]['file_id'], prefix=f"tg_car_{user_id}", default_ext='.jpg')
            if saved:
                photo_url = saved

        data = state['data']
        make = data.get('make', 'Кубанский')
        model = data.get('model', 'Болид')
        hp = data.get('hp', 300)
        drivetrain = data.get('drivetrain', 'RWD')
        city = data.get('city', 'Краснодар')

        # Estimate performance
        zero_hundred = round(max(3.2, 7.5 - (hp / 140.0)), 1)
        quarter = round(max(10.5, 15.5 - (hp / 95.0)), 1)

        conn = get_db()
        c = conn.cursor()
        c.execute('SELECT id FROM users WHERE auth_id = ? OR telegram_handle = ?', (str(user_id), f"@{username}"))
        urow = c.fetchone()
        if not urow:
            c.execute('''
                INSERT INTO users (username, callsign, name, avatar, bio, auth_provider, auth_id, telegram_handle, city, street_cred, wins, losses)
                VALUES (?, ?, ?, 'https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=150', 'Пилот Telegram KSS', 'telegram', ?, ?, ?, 1000, 0, 0)
            ''', (f"tg_{user_id}", username or first_name, first_name, str(user_id), f"@{username}" if username else "", city))
            conn.commit()
            db_user_id = c.lastrowid
        else:
            db_user_id = urow['id']
            c.execute('UPDATE users SET city = ? WHERE id = ?', (city, db_user_id))
            conn.commit()

        # Update primary car flag
        c.execute('UPDATE cars SET is_primary = 0 WHERE user_id = ?', (db_user_id,))
        c.execute('''
            INSERT INTO cars (user_id, make, model, hp, drivetrain, zero_to_hundred, quarter_mile, photo_url, aspiration, weight, is_primary)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'Турбо', 1420, 1)
        ''', (db_user_id, make, model, hp, drivetrain, zero_hundred, quarter, photo_url))
        conn.commit()
        conn.close()

        # Finish questionnaire
        USER_STATES.pop(chat_id, None)

        success_msg = (
            f"🎉 <b>ПОЗДРАВЛЯЕМ! АВТОМОБИЛЬ ЗАРЕГИСТРИРОВАН В РЕЕСТРЕ KSS!</b>\n\n"
            f"🏎️ <b>{make} {model}</b>\n"
            f"⚡ Мощность: <b>{hp} л.с.</b> | Привод: <b>{drivetrain}</b>\n"
            f"⏱️ 0-100: <b>{zero_hundred}с</b> | 1/4 мили: <b>{quarter}с</b>\n"
            f"📍 Базирование: <b>{city} (Краснодарский край)</b>\n"
            f"👤 Пилот: <b>{first_name} (@{username})</b>\n\n"
            f"🌐 <b>Твоя машина уже красуется в Гараже на сайте!</b>\n"
            f"👉 Ссылка: <b>{webapp_url}/?tab=garage</b>"
        )
        if client:
            client.send_message(chat_id, success_msg, reply_markup=get_main_keyboard(webapp_url))
        return True

    return False

def handle_my_car(client, chat_id, user_id, username, first_name, webapp_url):
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT id FROM users WHERE auth_id = ? OR telegram_handle = ?', (str(user_id), f"@{username}"))
    urow = c.fetchone()
    car = None
    if urow:
        c.execute('SELECT * FROM cars WHERE user_id = ? ORDER BY is_primary DESC, id DESC LIMIT 1', (urow['id'],))
        car = c.fetchone()
    conn.close()

    if not car:
        msg = (
            f"🏎️ <b>У тебя пока нет зарегистрированного автомобиля в KSS.</b>\n\n"
            f"Заполни простую анкету прямо сейчас — напиши /car или нажми кнопку '🚗 Анкета авто' внизу!"
        )
        if client:
            client.send_message(chat_id, msg)
        return msg

    ptw = round((car['hp'] / max(car['weight'] or 1400, 500)) * 1000)
    text = (
        f"🏎️ <b>ТВОЙ БОЕВОЙ АППАРАТ В KSS:</b>\n\n"
        f"<b>{car['make']} {car['model']} {car['generation'] or ''}</b>\n"
        f"⚡ Мощность: <b>{car['hp']} л.с.</b> ({ptw} л.с./тонну)\n"
        f"⚙️ Привод: <b>{car['drivetrain']}</b> | Наддув: <b>{car['aspiration']}</b>\n"
        f"⏱️ 0-100: <b>{car['zero_to_hundred'] or 5.0}с</b> | 1/4 мили: <b>{car['quarter_mile'] or 13.0}с</b>\n"
        f"🔧 Двигатель: <code>{car['engine_code'] or 'Custom'}</code>\n\n"
        f"🌐 Карточка доступна на сайте:\n"
        f"👉 <b>{webapp_url}/?tab=garage</b>"
    )
    if client:
        client.send_message(chat_id, text)
    return text

def handle_help(client, chat_id):
    text = (
        "📖 <b>ПОЛНОЕ РУКОВОДСТВО ПО КОМАНДАМ @Kuban_Streetbot</b>\n\n"
        "🏎️ <b>АВТОМОБИЛИ И ГАРАЖ:</b>\n"
        "• <code>/car</code> — Пошаговая анкета добавления авто на сайт\n"
        "• <code>/mycar</code> — Посмотреть свой текущий зарегистрированный авто\n"
        "• <code>/garage</code> — Топ заряженных боевых тачек края\n\n"
        "🪪 <b>ПРОФИЛЬ И АВТОРИЗАЦИЯ:</b>\n"
        "• <code>/auth</code> — Получить 4-значный код и ссылку для входа на сайт\n"
        "• <code>/profile</code> — Моя лицензия пилота и статистика побед\n"
        "• <code>/chat</code> — Свежие сообщения в уличном эфире пилотов\n"
        "• <code>/callsign [имя]</code> — Сменить позывной (например: <code>/callsign Ночной_Буст</code>)\n\n"
        "⛰️ <b>ТРАССЫ И ЛОКАЦИИ:</b>\n"
        "• <code>/spots</code> — Список спотов с координатами и сложностью\n\n"
        "⚔️ <b>ЗАЕЗДЫ И РЕЙТИНГ:</b>\n"
        "• <code>/top</code> — Топ-10 пилотов края по рейтингу Street Cred\n"
        "• <code>/sim</code> — Симулятор дуэли двух автомобилей\n"
        "• <code>/win</code> — Формат фиксации победы в заезде\n\n"
        "❌ <code>/cancel</code> — Прервать заполнение анкеты"
    )
    if client:
        client.send_message(chat_id, text)
    return text

def handle_chat_bot(client, chat_id, webapp_url):
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM chat_messages ORDER BY created_at DESC LIMIT 4')
    msgs = c.fetchall()
    conn.close()

    lines = ["📻 <b>ПОСЛЕДНИЕ СООБЩЕНИЯ В ЭФИРЕ KUBAN STREET SPECIAL:</b>\n"]
    if msgs:
        for m in reversed(msgs):
            time_str = m['created_at'].split()[1][:5] if m['created_at'] and ' ' in m['created_at'] else ''
            car_badge = f" [{m['car_name']}]" if m.get('car_name') else ""
            lines.append(f"💬 <b>{m['callsign']}</b>{car_badge} <i>({time_str})</i>:\n«{m['message']}»\n")
    else:
        lines.append("<i>В эфире пока тихо. Будьте первыми!</i>\n")

    lines.append(f"👉 <b>Открыть живой чат-форум на сайте:</b>\n{webapp_url}/?tab=chat")
    full_text = "\n".join(lines)
    if client:
        client.send_message(chat_id, full_text)
    return full_text

def handle_post_chat_from_bot(client, chat_id, user_id, username, first_name, message_text, photo_list=None, video_obj=None, webapp_url="http://localhost:8080"):
    media_url = None
    media_type = 'image'

    if video_obj:
        media_url = save_telegram_file(client, video_obj['file_id'], prefix=f"tg_video_{user_id}", default_ext='.mp4')
        media_type = 'video'
    elif photo_list:
        media_url = save_telegram_file(client, photo_list[-1]['file_id'], prefix=f"tg_photo_{user_id}", default_ext='.jpg')
        media_type = 'image'

    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE auth_id = ? OR telegram_handle = ?', (str(user_id), f"@{username}"))
    urow = c.fetchone()

    if not urow:
        callsign = username or first_name or f"Пилот_{user_id}"
        avatar = "https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=150"
        c.execute('''
            INSERT INTO users (username, callsign, name, avatar, bio, auth_provider, auth_id, telegram_handle, city, street_cred, wins, losses)
            VALUES (?, ?, ?, ?, 'Пилот Telegram KSS', 'telegram', ?, ?, 'Краснодар', 1000, 0, 0)
        ''', (f"tg_{user_id}", callsign, first_name, avatar, str(user_id), f"@{username}" if username else ""))
        conn.commit()
        db_user_id = c.lastrowid
        car_name = None
    else:
        db_user_id = urow['id']
        callsign = urow['callsign'] or username or first_name
        avatar = urow['avatar'] or "https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=150"
        c.execute('SELECT make, model, hp FROM cars WHERE user_id = ? ORDER BY is_primary DESC, id DESC LIMIT 1', (db_user_id,))
        car = c.fetchone()
        car_name = f"{car['make']} {car['model']} ({car['hp']} hp)" if car else None

    conn.close()

    text_to_post = message_text.strip() if message_text else ""
    if not text_to_post:
        text_to_post = "🎥 [Видеозапись из эфира]" if media_type == 'video' else "📷 [Фотография из эфира]"

    result = add_chat_message(
        user_id=db_user_id,
        callsign=callsign,
        avatar=avatar,
        car_name=car_name,
        channel='general',
        message=text_to_post,
        image_url=media_url,
        media_type=media_type
    )

    if result:
        media_notice = f"\n📎 Прикреплен медиафайл: <b>{media_type.upper()}</b>" if media_url else ""
        resp_msg = (
            f"📻 <b>ОПУБЛИКОВАНО В ЭФИРЕ KUBAN STREET SPECIAL!</b>\n\n"
            f"👤 <b>{callsign}</b>{f' [{car_name}]' if car_name else ''}:\n"
            f"«{text_to_post}»{media_notice}\n\n"
            f"👉 <b>Смотри в чате на сайте:</b> {webapp_url}/?tab=chat"
        )
        if client:
            client.send_message(chat_id, resp_msg, reply_markup=get_main_keyboard(webapp_url))
        return True
    else:
        if client:
            client.send_message(chat_id, "⚠️ Ошибка публикации сообщения. Попробуйте еще раз.")
        return False

def handle_add_car_fast(client, chat_id, user_id, username, first_name, text, photo_list=None, video_obj=None, webapp_url="http://localhost:8080"):
    clean_text = text.replace('/car', '').replace('/addcar', '').strip()
    parts = clean_text.split()
    if len(parts) < 2:
        return handle_start_car_wizard(client, chat_id, webapp_url)

    make = parts[0]
    model = parts[1]
    hp = 300
    drivetrain = 'RWD'
    for p in parts[2:]:
        if p.isdigit():
            hp = int(p)
        elif p.upper() in ['RWD', 'AWD', 'FWD', 'ЗАДНИЙ', 'ПОЛНЫЙ', 'ПЕРЕДНИЙ']:
            if 'AWD' in p.upper() or 'ПОЛН' in p.upper():
                drivetrain = 'AWD'
            elif 'FWD' in p.upper() or 'ПЕРЕД' in p.upper():
                drivetrain = 'FWD'
            else:
                drivetrain = 'RWD'

    photo_url = "https://images.unsplash.com/photo-1503376780353-7e6692767b70?w=800"
    if video_obj and client:
        saved = save_telegram_file(client, video_obj['file_id'], prefix=f"tg_car_{user_id}", default_ext='.mp4')
        if saved:
            photo_url = saved
    elif photo_list and client:
        saved = save_telegram_file(client, photo_list[-1]['file_id'], prefix=f"tg_car_{user_id}", default_ext='.jpg')
        if saved:
            photo_url = saved

    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT id FROM users WHERE auth_id = ? OR telegram_handle = ?', (str(user_id), f"@{username}"))
    urow = c.fetchone()
    if not urow:
        c.execute('''
            INSERT INTO users (username, callsign, name, avatar, bio, auth_provider, auth_id, telegram_handle, city, street_cred, wins, losses)
            VALUES (?, ?, ?, 'https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=150', 'Пилот Telegram KSS', 'telegram', ?, ?, 'Краснодар', 1000, 0, 0)
        ''', (f"tg_{user_id}", username or first_name, first_name, str(user_id), f"@{username}" if username else ""))
        conn.commit()
        db_user_id = c.lastrowid
    else:
        db_user_id = urow['id']

    c.execute('UPDATE cars SET is_primary = 0 WHERE user_id = ?', (db_user_id,))
    c.execute('''
        INSERT INTO cars (user_id, make, model, hp, drivetrain, photo_url, aspiration, weight, is_primary)
        VALUES (?, ?, ?, ?, ?, ?, 'Турбо', 1450, 1)
    ''', (db_user_id, make, model, hp, drivetrain, photo_url))
    conn.commit()
    conn.close()

    success_msg = (
        f"✅ <b>АВТОМОБИЛЬ СОХРАНЕН В БАЗЕ!</b>\n\n"
        f"🏎️ <b>{make} {model}</b>\n"
        f"⚡ Мощность: <b>{hp} л.с.</b> | Привод: <b>{drivetrain}</b>\n"
        f"👤 Пилот: <b>{first_name} (@{username})</b>\n\n"
        f"🌐 Твоя тачка уже доступна в Гараже на сайте:\n"
        f"👉 <b>{webapp_url}/?tab=garage</b>"
    )
    if client:
        client.send_message(chat_id, success_msg)
    return success_msg

def handle_set_callsign(client, chat_id, user_id, username, first_name, text):
    parts = text.replace('/callsign', '').strip().split()
    if not parts:
        client.send_message(chat_id, "Введи свой позывной:\n<code>/callsign Твой_Позывной</code>\nНапример: <code>/callsign Ночной_Буст</code>")
        return
    new_callsign = parts[0]
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT id FROM users WHERE auth_id = ? OR telegram_handle = ?', (str(user_id), f"@{username}"))
    urow = c.fetchone()
    if urow:
        c.execute('UPDATE users SET callsign = ? WHERE id = ?', (new_callsign, urow['id']))
    else:
        c.execute('''
            INSERT INTO users (username, callsign, name, avatar, bio, auth_provider, auth_id, telegram_handle, city, street_cred, wins, losses)
            VALUES (?, ?, ?, 'https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=150', 'Пилот Telegram KSS', 'telegram', ?, ?, 'Краснодар', 1000, 0, 0)
        ''', (f"tg_{user_id}", new_callsign, first_name, str(user_id), f"@{username}" if username else ""))
    conn.commit()
    conn.close()
    if client:
        client.send_message(chat_id, f"✅ Твой позывной обновлен на: <b>{new_callsign}</b>! Отображается в профиле на сайте.")


def run_bot_service():
    init_db()
    cfg = load_config()
    token = cfg.get("bot_token")
    webapp_url = cfg.get("webapp_url", "http://localhost:8080")

    print("=" * 65)
    print("🤖 KUBAN STREET SPECIAL (KSS) — TELEGRAM BOT SERVICE")
    print(f"📍 WebApp URL: {webapp_url}")
    print("=" * 65)

    if not token or token == "YOUR_TELEGRAM_BOT_TOKEN_HERE":
        print("\n⚠️ ВНИМАНИЕ: TELEGRAM BOT TOKEN НЕ УСТАНОВЛЕН В bot_config.json!")
        print("Чтобы бот отвечал в реальном Telegram:")
        print("1. Напишите @BotFather в Telegram и создайте бота (получите токен вида 123456:ABC-DEF...)")
        print("2. Вставьте его в файл 'bot_config.json' в поле 'bot_token'")
        print("3. Перезапустите bot.py\n")
        print("Сейчас бот запускается в режиме ИНТЕРАКТИВНОГО ТЕСТИРОВАНИЯ (Console CLI).")
        print("Вы можете вводить команды прямо сюда: /start, /garage, /spots, /top, /sim, /quit\n")

        # Interactive loop
        while True:
            try:
                cmd = input("KSS_Bot > ").strip()
                if not cmd:
                    continue
                if cmd in ['/quit', 'exit', 'q']:
                    print("Бот остановлен.")
                    break
                elif cmd == '/start':
                    print("\n" + handle_start(None, 0, "pilot_krd", "Пилот", webapp_url) + "\n")
                elif cmd.startswith('/car'):
                    parts = cmd.split()
                    if len(parts) >= 3:
                        print("\n" + handle_add_car_fast(None, 0, 1, "marko_krd", "Марк", cmd, webapp_url=webapp_url) + "\n")
                    else:
                        print("\n" + handle_start_car_wizard(None, 0, webapp_url) + "\n")
                elif cmd in ['/mycar', '🏎️ Моя машина']:
                    print("\n" + handle_my_car(None, 0, 1, "marko_krd", "Марк", webapp_url) + "\n")
                elif cmd in ['/auth', '🔑 Вход на сайт']:
                    print("\n" + handle_auth(None, 0, 1, "marko_krd", "Марк", webapp_url=webapp_url) + "\n")
                elif cmd in ['/garage', '🏁 Гараж Кубани']:
                    print("\n" + handle_garage(None, 0) + "\n")
                elif cmd in ['/spots', '⛰️ Споты & Карта']:
                    print("\n" + handle_spots(None, 0) + "\n")
                elif cmd in ['/top', '🏆 Топ пилотов']:
                    print("\n" + handle_top(None, 0) + "\n")
                elif cmd in ['/sim', '⚔️ Дуэль-симулятор']:
                    print("\n" + handle_sim(None, 0) + "\n")
                elif cmd in ['/profile', '🪪 Моя лицензия']:
                    print("\n" + handle_profile(None, 0, "marko_krd", "Марк") + "\n")
                elif cmd in ['/chat', '/radio', '💬 Эфир']:
                    print("\n" + handle_chat_bot(None, 0, webapp_url) + "\n")
                elif cmd in ['/battle', '/win', '📝 Зарегистрировать заезд']:
                    print("\n" + handle_register_battle_bot(None, 0) + "\n")
                elif cmd in ['/help', '❓ Все команды']:
                    print("\n" + handle_help(None, 0) + "\n")
                else:
                    search_res = handle_car_search(None, 0, cmd)
                    if search_res:
                        print("\n" + search_res + "\n")
                    else:
                        print(f"Неизвестная команда или авто не найдено: {cmd}. Введите /help для списка команд.")

            except (KeyboardInterrupt, EOFError):
                print("\nБот остановлен.")
                break
        return

    # Real Polling Mode
    client = TelegramBotClient(token)
    me = client.request('getMe')
    if me:
        bot_user = me.get('username', 'Kuban_Streetbot')
        bot_title = me.get('first_name', 'Kuban Street Special')
        print(f"✅ УСПЕШНОЕ ПОДКЛЮЧЕНИЕ К TELEGRAM BOT API!")
        print(f"🤖 Бот в сети: @{bot_user} ({bot_title})")
        print(f"🔗 Ссылка: https://t.me/{bot_user}")
        client.set_commands()
        print(f"⚡ Бот слушает команды и сообщения (Polling активен)...\n")
    else:
        print(f"✅ Токен загружен! Запуск Polling...")
        client.set_commands()

    last_cfg_check = time.time()
    while True:
        try:
            # Dynamically reload webapp_url from config every 5 seconds
            if time.time() - last_cfg_check > 5:
                cfg_dynamic = load_config()
                webapp_url = cfg_dynamic.get("webapp_url", webapp_url)
                last_cfg_check = time.time()

            updates = client.get_updates()
            for update in updates:
                # Handle message
                if 'message' in update:
                    msg = update['message']
                    chat_id = msg['chat']['id']
                    user_id = msg['from'].get('id', chat_id)
                    photo_list = msg.get('photo')
                    video_obj = msg.get('video') or msg.get('animation') or msg.get('video_note')
                    doc_obj = msg.get('document')
                    if doc_obj:
                        mime = doc_obj.get('mime_type', '').lower()
                        fname = doc_obj.get('file_name', '').lower()
                        if mime.startswith('video/') or any(fname.endswith(x) for x in ['.mp4', '.mov', '.webm', '.m4v']):
                            video_obj = doc_obj
                        elif mime.startswith('image/') or any(fname.endswith(x) for x in ['.jpg', '.jpeg', '.png', '.webp']):
                            photo_list = [{'file_id': doc_obj['file_id']}]

                    text = (msg.get('text') or msg.get('caption') or '').strip()
                    first_name = msg['from'].get('first_name', 'Пилот')
                    username = msg['from'].get('username', '')

                    # 1. Active Questionnaire Wizard Check
                    if chat_id in USER_STATES:
                        handled = handle_car_wizard_step(client, chat_id, user_id, username, first_name, text, photo_list, video_obj, webapp_url)
                        if handled:
                            continue

                    lower_text = text.lower()

                    if text.startswith('/start auth') or text.startswith('/auth') or text.startswith('/login') or '🔑 вход' in lower_text or 'код' in lower_text:
                        handle_auth(client, chat_id, user_id, username, first_name, webapp_url)
                    elif text.startswith('/start'):
                        handle_start(client, chat_id, username, first_name, webapp_url)
                    elif text.startswith('/cancel') or lower_text == 'отмена':
                        USER_STATES.pop(chat_id, None)
                        client.send_message(chat_id, "Действие отменено.", reply_markup=get_main_keyboard(webapp_url))
                    elif text.startswith('/mycar') or 'моя машина' in lower_text:
                        handle_my_car(client, chat_id, user_id, username, first_name, webapp_url)
                    elif text.startswith('/car') or text.startswith('/addcar') or 'анкета авто' in lower_text or ('добавить' in lower_text and 'авто' in lower_text):
                        clean_cmd = text.replace('/car', '').replace('/addcar', '').strip()
                        if len(clean_cmd.split()) >= 2:
                            handle_add_car_fast(client, chat_id, user_id, username, first_name, text, photo_list, video_obj, webapp_url)
                        else:
                            handle_start_car_wizard(client, chat_id, webapp_url)
                    elif text.startswith('/callsign') or 'позывн' in lower_text:
                        handle_set_callsign(client, chat_id, user_id, username, first_name, text)
                    elif text.startswith('/garage') or 'гараж' in lower_text:
                        handle_garage(client, chat_id)
                    elif text.startswith('/spots') or 'спот' in lower_text or 'трасс' in lower_text:
                        handle_spots(client, chat_id)
                    elif text.startswith('/top') or 'рейтинг' in lower_text or 'топ' in lower_text:
                        handle_top(client, chat_id)
                    elif text.startswith('/sim') or 'дуэл' in lower_text or 'симулят' in lower_text:
                        handle_sim(client, chat_id)
                    elif text.startswith('/profile') or 'профиль' in lower_text or 'лицензия' in lower_text:
                        handle_profile(client, chat_id, username, first_name)
                    elif text.startswith('/chat') or text.startswith('/radio') or 'эфир' in lower_text or 'чат' in lower_text:
                        clean_chat_text = text.replace('/chat', '').replace('/radio', '').replace('эфир', '').replace('чат', '').strip()
                        if clean_chat_text or photo_list or video_obj:
                            handle_post_chat_from_bot(client, chat_id, user_id, username, first_name, clean_chat_text, photo_list, video_obj, webapp_url)
                        else:
                            handle_chat_bot(client, chat_id, webapp_url)
                    elif text.startswith('/win') or text.startswith('/battle') or 'побед' in lower_text or 'заезд' in lower_text:
                        handle_register_battle_bot(client, chat_id)
                    elif text.startswith('/help') or 'команд' in lower_text or 'справка' in lower_text:
                        handle_help(client, chat_id)
                    elif (photo_list or video_obj) and text:
                        # Photo or video with text caption -> post directly to street chat!
                        handle_post_chat_from_bot(client, chat_id, user_id, username, first_name, text, photo_list, video_obj, webapp_url)
                    elif photo_list and not text:
                        saved_url = save_telegram_file(client, photo_list[-1]['file_id'], prefix=f"tg_photo_{user_id}", default_ext='.jpg')
                        msg = (
                            "📷 <b>Фотография сохранена на сервере KSS!</b>\n\n"
                            "• Чтобы зарегистрировать с ней автомобиль в гараже: <code>/car</code>\n"
                            "• Чтобы опубликовать фото в уличный эфир сайта: отправьте его с подписью или используйте <code>/chat [сообщение]</code>\n\n"
                            f"🌐 <i>Прямая ссылка: {webapp_url}{saved_url if saved_url else ''}</i>"
                        )
                        client.send_message(chat_id, msg, reply_markup=get_main_keyboard(webapp_url))
                    elif video_obj and not text:
                        saved_url = save_telegram_file(client, video_obj['file_id'], prefix=f"tg_video_{user_id}", default_ext='.mp4')
                        msg = (
                            "🎥 <b>Видеозапись сохранена на сервере KSS!</b>\n\n"
                            "• Чтобы опубликовать клип в уличный эфир пилотов: отправьте видео с подписью или используйте <code>/chat [сообщение]</code>\n"
                            "• Чтобы использовать как видео-доказательство заезда Dragy/Onboard: укажите ссылку при регистрации заезда на сайте!\n\n"
                            f"🌐 <i>Прямая ссылка на видео: {webapp_url}{saved_url if saved_url else ''}</i>"
                        )
                        client.send_message(chat_id, msg, reply_markup=get_main_keyboard(webapp_url))
                    else:
                        # Try car search first
                        search_res = handle_car_search(client, chat_id, text)
                        if not search_res:
                            client.send_message(chat_id, "Выберите действие в меню внизу или введите марку авто (например: <i>Чайзер, Supra, 2107, Golf</i>):", reply_markup=get_main_keyboard(webapp_url))

                # Handle callback queries
                elif 'callback_query' in update:
                    cb = update['callback_query']
                    cb_id = cb['id']
                    data = cb.get('data')
                    chat_id = cb['message']['chat']['id']

                    client.answer_callback(cb_id)
                    if data == 'cmd_garage':
                        handle_garage(client, chat_id)
                    elif data == 'cmd_spots':
                        handle_spots(client, chat_id)
                    elif data == 'cmd_top':
                        handle_top(client, chat_id)
                    elif data == 'cmd_sim':
                        handle_sim(client, chat_id)

            time.sleep(0.5)
        except KeyboardInterrupt:
            print("\nБот остановлен пользователем.")
            break
        except Exception as e:
            time.sleep(3)

if __name__ == '__main__':
    run_bot_service()
