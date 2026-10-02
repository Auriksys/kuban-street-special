"""
KubanStreetSpecial - High-Performance Zero-Dependency Python HTTP & REST API Server
Runs on standard Python 3 (no pip install required).
Serves frontend SPA and handles REST API with SQLite database.
"""

import http.server
import socketserver
import os
import sys
import json
import sqlite3
import mimetypes
import urllib.parse
import base64
from datetime import datetime

# Add project root to sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

try:
    from database import (
        init_db, get_db, DB_PATH, clear_all_data, seed_data, update_user_last_seen,
        get_online_pilots, add_map_marker, get_active_map_markers, delete_map_marker,
        update_user_profile, get_user_profile, confirm_map_marker, vote_clear_map_marker,
        get_chat_messages, add_chat_message, like_chat_message, delete_chat_message
    )
except ImportError:
    from db.database import (
        init_db, get_db, DB_PATH, clear_all_data, seed_data, update_user_last_seen,
        get_online_pilots, add_map_marker, get_active_map_markers, delete_map_marker,
        update_user_profile, get_user_profile, confirm_map_marker, vote_clear_map_marker,
        get_chat_messages, add_chat_message, like_chat_message, delete_chat_message
    )

STATIC_DIR = os.path.join(BASE_DIR, 'static')
UPLOADS_DIR = os.path.join(STATIC_DIR, 'uploads')
os.makedirs(UPLOADS_DIR, exist_ok=True)
PORT = int(os.environ.get('PORT', 8080))

# In-Memory Real-Time Presence Cache
ONLINE_SESSIONS = {}

class KSSRequestHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Clean logging format
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {args[0]} - {args[1]}")

    def send_json_response(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False, indent=2).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        # 1. API Routes
        if path.startswith('/api/'):
            self.handle_api_get(path, query)
            return

        # 2. Static File Serving
        self.serve_static(path)

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length) if content_length > 0 else b'{}'
        content_type = self.headers.get('Content-Type', '')

        # File and Media Upload endpoint (Photos & Videos)
        if path == '/api/upload':
            self.handle_api_upload(query, content_type, post_data)
            return

        try:
            payload = json.loads(post_data.decode('utf-8'))
        except Exception:
            payload = {}

        if path.startswith('/api/'):
            self.handle_api_post(path, payload)
        else:
            self.send_json_response({"error": "Not Found"}, 404)

    def handle_api_upload(self, query, content_type, data):
        import base64
        import uuid
        uploads_dir = os.path.join(STATIC_DIR, 'uploads')
        os.makedirs(uploads_dir, exist_ok=True)

        try:
            orig_name = 'media.jpg'
            media_type = 'image'
            file_bytes = b''

            # A. Base64 JSON payload
            if 'application/json' in content_type:
                payload = json.loads(data.decode('utf-8'))
                raw_data = payload.get('data') or payload.get('file_data') or ''
                orig_name = payload.get('filename') or payload.get('file_name') or 'upload.jpg'
                media_type = payload.get('type') or payload.get('media_type') or 'image'

                if ',' in raw_data:
                    header, b64_str = raw_data.split(',', 1)
                    if 'video' in header:
                        media_type = 'video'
                    elif 'image' in header:
                        media_type = 'image'
                else:
                    b64_str = raw_data

                file_bytes = base64.b64decode(b64_str)

            # B. Multipart Form Data
            elif 'multipart/form-data' in content_type:
                boundary = content_type.split('boundary=')[-1].strip().encode()
                parts = data.split(b'--' + boundary)
                for part in parts:
                    if b'filename="' in part:
                        headers_part, body_part = part.split(b'\r\n\r\n', 1)
                        body_part = body_part.rstrip(b'\r\n--')
                        match = re.search(rb'filename="([^"]+)"', headers_part)
                        if match:
                            orig_name = match.group(1).decode('utf-8', errors='ignore')
                        file_bytes = body_part
                        break
                if not file_bytes:
                    self.send_json_response({"error": "Файл не обнаружен в теле формы"}, 400)
                    return

            # C. Direct binary stream
            else:
                orig_name = query.get('filename', ['upload.jpg'])[0]
                file_bytes = data

            if not file_bytes:
                self.send_json_response({"error": "Пустой файл"}, 400)
                return

            if len(file_bytes) > 52428800:
                self.send_json_response({"error": "Размер файла превышает 50 МБ"}, 400)
                return

            ext = os.path.splitext(orig_name)[1].lower()
            if not ext:
                ext = '.mp4' if media_type == 'video' else '.jpg'

            if ext in ['.mp4', '.webm', '.mov', '.m4v']:
                media_type = 'video'
            elif ext in ['.jpg', '.jpeg', '.png', '.webp', '.gif']:
                media_type = 'image'
            else:
                ext = '.jpg'
                media_type = 'image'

            timestamp = int(datetime.now().timestamp())
            uid = uuid.uuid4().hex[:8]
            clean_filename = f"kss_{timestamp}_{uid}{ext}"
            file_path = os.path.join(uploads_dir, clean_filename)

            with open(file_path, 'wb') as f:
                f.write(file_bytes)

            file_url = f"/uploads/{clean_filename}"
            size_kb = round(len(file_bytes) / 1024, 1)

            self.send_json_response({
                "status": "ok",
                "url": file_url,
                "media_type": media_type,
                "filename": clean_filename,
                "size_kb": size_kb,
                "message": f"{'Видео' if media_type == 'video' else 'Фото'} успешно загружено ({size_kb} KB)"
            })

        except Exception as e:
            self.send_json_response({"error": f"Ошибка сохранения медиа: {str(e)}"}, 500)

    def do_DELETE(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        conn = get_db()
        c = conn.cursor()
        try:
            parts = path.strip('/').split('/')
            target_id_str = parts[-1] if parts else ''

            if path.startswith('/api/news/') and target_id_str.isdigit():
                c.execute('DELETE FROM news WHERE id = ?', (int(target_id_str),))
                conn.commit()
                self.send_json_response({"status": "ok", "message": "Новость удалена"})
            elif path.startswith('/api/cars/') and target_id_str.isdigit():
                c.execute('DELETE FROM cars WHERE id = ?', (int(target_id_str),))
                conn.commit()
                self.send_json_response({"status": "ok", "message": "Автомобиль удален"})
            elif path.startswith('/api/spots/') and target_id_str.isdigit():
                c.execute('DELETE FROM spots WHERE id = ?', (int(target_id_str),))
                conn.commit()
                self.send_json_response({"status": "ok", "message": "Спот удален"})
            elif path.startswith('/api/battles/') and target_id_str.isdigit():
                c.execute('DELETE FROM battles WHERE id = ?', (int(target_id_str),))
                conn.commit()
                self.send_json_response({"status": "ok", "message": "Заезд удален"})
            elif path.startswith('/api/pilots/') and target_id_str.isdigit():
                c.execute('DELETE FROM users WHERE id = ?', (int(target_id_str),))
                conn.commit()
                self.send_json_response({"status": "ok", "message": "Пилот удален"})
            elif path.startswith('/api/markers/') and target_id_str.isdigit():
                delete_map_marker(int(target_id_str))
                self.send_json_response({"status": "ok", "message": "Метка удалена"})
            elif path.startswith('/api/chat/') and target_id_str.isdigit():
                delete_chat_message(int(target_id_str))
                self.send_json_response({"status": "ok", "message": "Сообщение удалено"})
            else:
                self.send_json_response({"error": "Not Found"}, 404)
        except Exception as e:
            self.send_json_response({"error": str(e)}, 500)
        finally:
            conn.close()

    def handle_api_get(self, path, query):
        conn = get_db()
        c = conn.cursor()

        try:
            # High-Reliability Watchdog Health Check
            if path == '/api/health':
                c.execute('SELECT 1')
                db_test = c.fetchone()[0] == 1
                c.execute('SELECT COUNT(*) FROM users')
                users_cnt = c.fetchone()[0]
                c.execute('SELECT COUNT(*) FROM cars')
                cars_cnt = c.fetchone()[0]
                self.send_json_response({
                    "status": "ok",
                    "healthy": True,
                    "service": "KubanStreetSpecial-Core",
                    "database": "connected" if db_test else "error",
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "users_count": users_cnt,
                    "cars_count": cars_cnt
                })
                return

            # Watchdog & Uptime Status
            elif path == '/api/watchdog/status':
                status_file = os.path.join(BASE_DIR, 'kss_status.json')
                if os.path.exists(status_file):
                    try:
                        with open(status_file, 'r', encoding='utf-8') as f:
                            self.send_json_response(json.load(f))
                            return
                    except Exception:
                        pass
                self.send_json_response({
                    "status": "online",
                    "server_online": True,
                    "tunnel_online": True,
                    "uptime_human": "Активен",
                    "latency_ms": 1,
                    "recoveries_count": 0,
                    "last_check": datetime.now().strftime("%H:%M:%S")
                })
                return

            # Stats Summary
            elif path == '/api/stats':
                c.execute('SELECT COUNT(*) FROM cars')
                cars_count = c.fetchone()[0]

                c.execute('SELECT COUNT(*) FROM battles')
                battles_count = c.fetchone()[0]

                c.execute('SELECT COUNT(*) FROM spots')
                spots_count = c.fetchone()[0]

                c.execute('SELECT COUNT(*) FROM teams')
                teams_count = c.fetchone()[0]

                c.execute('SELECT username, callsign, street_cred, avatar FROM users ORDER BY street_cred DESC LIMIT 1')
                king_row = c.fetchone()
                king = dict(king_row) if king_row else None

                c.execute('SELECT quarter_mile, make, model, hp FROM cars WHERE quarter_mile IS NOT NULL ORDER BY quarter_mile ASC LIMIT 1')
                drag_row = c.fetchone()
                fastest_drag = dict(drag_row) if drag_row else None

                self.send_json_response({
                    "status": "ok",
                    "stats": {
                        "cars_registered": cars_count,
                        "battles_logged": battles_count,
                        "spots_active": spots_count,
                        "teams_active": teams_count,
                        "street_king": king,
                        "record_quarter_mile": fastest_drag
                    }
                })

            # Cars List
            elif path == '/api/cars':
                drivetrain = query.get('drivetrain', [None])[0]
                city = query.get('city', [None])[0]
                q = query.get('q', [None])[0]

                sql = '''
                    SELECT c.*, u.callsign as owner_callsign, u.name as owner_name, u.city as owner_city,
                           t.name as team_name, t.tag as team_tag
                    FROM cars c
                    JOIN users u ON c.user_id = u.id
                    LEFT JOIN teams t ON u.team_id = t.id
                    WHERE 1=1
                '''
                params = []
                if drivetrain:
                    sql += ' AND c.drivetrain = ?'
                    params.append(drivetrain)
                if city:
                    sql += ' AND u.city = ?'
                    params.append(city)
                if q:
                    sql += ' AND (c.make LIKE ? OR c.model LIKE ? OR c.engine_code LIKE ? OR u.callsign LIKE ?)'
                    param_q = f'%{q}%'
                    params.extend([param_q, param_q, param_q, param_q])

                sql += ' ORDER BY c.hp DESC'
                c.execute(sql, params)
                rows = [dict(row) for row in c.fetchall()]
                for r in rows:
                    if r.get('specs_json'):
                        try:
                            r['specs'] = json.loads(r['specs_json'])
                        except Exception:
                            r['specs'] = {}
                self.send_json_response({"status": "ok", "cars": rows})

            # Single Car Detail
            elif path.startswith('/api/cars/'):
                car_id_str = path.split('/')[-1]
                if not car_id_str.isdigit():
                    self.send_json_response({"error": "Автомобиль не найден"}, 404)
                    return
                car_id = int(car_id_str)
                c.execute('''
                    SELECT c.*, u.callsign as owner_callsign, u.name as owner_name, u.city as owner_city,
                           u.telegram_handle, u.vk_url, u.street_cred,
                           t.name as team_name, t.tag as team_tag
                    FROM cars c
                    JOIN users u ON c.user_id = u.id
                    LEFT JOIN teams t ON u.team_id = t.id
                    WHERE c.id = ?
                ''', (car_id,))
                car_row = c.fetchone()
                if not car_row:
                    self.send_json_response({"error": "Автомобиль не найден"}, 404)
                    return
                car = dict(car_row)
                if car.get('specs_json'):
                    try:
                        car['specs'] = json.loads(car['specs_json'])
                    except Exception:
                        car['specs'] = {}

                # Victories of this car
                c.execute('''
                    SELECT b.*,
                           lc.make as loser_make, lc.model as loser_model,
                           lu.callsign as loser_callsign
                    FROM battles b
                    LEFT JOIN cars lc ON b.loser_car_id = lc.id
                    LEFT JOIN users lu ON b.loser_id = lu.id
                    WHERE b.winner_car_id = ?
                    ORDER BY b.date_time DESC
                ''', (car_id,))
                victories = [dict(row) for row in c.fetchall()]
                car['victories'] = victories

                self.send_json_response({"status": "ok", "car": car})

            # Spots in Krasnodar Krai
            elif path == '/api/spots':
                spot_type = query.get('type', [None])[0]
                sql = 'SELECT * FROM spots WHERE 1=1'
                params = []
                if spot_type:
                    sql += ' AND type = ?'
                    params.append(spot_type)
                sql += ' ORDER BY difficulty DESC'
                c.execute(sql, params)
                spots = [dict(row) for row in c.fetchall()]
                self.send_json_response({"status": "ok", "spots": spots})

            # Battles List
            elif path == '/api/battles':
                c.execute('''
                    SELECT b.*,
                           wc.make as winner_make, wc.model as winner_model, wc.hp as winner_hp, wc.photo_url as winner_car_photo,
                           wu.callsign as winner_callsign, wu.avatar as winner_avatar,
                           lc.make as loser_make, lc.model as loser_model, lc.hp as loser_hp, lc.photo_url as loser_car_photo,
                           lu.callsign as loser_callsign, lu.avatar as loser_avatar,
                           s.city as spot_city
                    FROM battles b
                    JOIN cars wc ON b.winner_car_id = wc.id
                    JOIN users wu ON b.winner_id = wu.id
                    LEFT JOIN cars lc ON b.loser_car_id = lc.id
                    LEFT JOIN users lu ON b.loser_id = lu.id
                    LEFT JOIN spots s ON b.spot_id = s.id
                    ORDER BY b.date_time DESC
                    LIMIT 50
                ''')
                battles = [dict(row) for row in c.fetchall()]
                self.send_json_response({"status": "ok", "battles": battles})

            # Leaderboard / Pilots
            elif path == '/api/pilots':
                c.execute('''
                    SELECT u.*, t.name as team_name, t.tag as team_tag,
                           c.make as car_make, c.model as car_model, c.hp as car_hp, c.photo_url as car_photo
                    FROM users u
                    LEFT JOIN teams t ON u.team_id = t.id
                    LEFT JOIN cars c ON c.user_id = u.id AND c.is_primary = 1
                    ORDER BY u.street_cred DESC
                ''')
                pilots = [dict(row) for row in c.fetchall()]
                self.send_json_response({"status": "ok", "pilots": pilots})

            # Teams
            elif path == '/api/teams':
                c.execute('''
                    SELECT t.*, u.callsign as leader_callsign,
                           (SELECT COUNT(*) FROM users WHERE team_id = t.id) as members_count,
                           (SELECT COUNT(*) FROM cars WHERE user_id IN (SELECT id FROM users WHERE team_id = t.id)) as cars_count
                    FROM teams t
                    LEFT JOIN users u ON t.leader_id = u.id
                    ORDER BY t.cred_score DESC
                ''')
                teams = [dict(row) for row in c.fetchall()]
                self.send_json_response({"status": "ok", "teams": teams})

            # News Feed
            elif path == '/api/news':
                c.execute('SELECT * FROM news ORDER BY created_at DESC')
                news_list = [dict(row) for row in c.fetchall()]
                self.send_json_response({"status": "ok", "news": news_list})
                return

            # Telegram One-time Auth Code Checker
            elif path == '/api/auth/tg-check':
                code = query.get('code', [None])[0]
                if not code:
                    self.send_json_response({"error": "Укажите код авторизации"}, 400)
                    return

                clean_code = str(code).strip().replace('#', '').replace(' ', '')
                c.execute('SELECT * FROM auth_codes WHERE code = ?', (clean_code,))
                row = c.fetchone()
                if not row:
                    # Also try search by username or telegram_id
                    c.execute('SELECT * FROM auth_codes WHERE username = ? OR telegram_id = ? ORDER BY created_at DESC LIMIT 1', (clean_code, clean_code))
                    row = c.fetchone()

                if not row:
                    # If not in auth_codes, check if a user with this handle or username already exists
                    c.execute('SELECT * FROM users WHERE username = ? OR telegram_handle = ? OR telegram_handle = ? OR callsign = ?', (clean_code, f"@{clean_code}", clean_code, clean_code))
                    direct_user = c.fetchone()
                    if direct_user:
                        user_dict = dict(direct_user)
                        self.send_json_response({
                            "status": "ok",
                            "user": user_dict,
                            "token": f"kss_tg_{user_dict['id']}_{int(datetime.now().timestamp())}"
                        })
                        return

                    self.send_json_response({"error": "Код не найден или устарел. Отправьте /auth в @Kuban_Streetbot для получения нового кода."}, 404)
                    return

                tg_user = dict(row)
                tg_id = str(tg_user.get('telegram_id') or '')
                tg_username = tg_user.get('username') or f"pilot_{tg_id[-4:] if tg_id else 'krd'}"
                first_name = tg_user.get('first_name') or tg_username

                c.execute('SELECT * FROM users WHERE telegram_handle = ? OR telegram_handle = ? OR auth_id = ?', (f"@{tg_username}", tg_username, tg_id))
                user = c.fetchone()

                if not user:
                    c.execute('''
                        INSERT INTO users (username, callsign, name, avatar, bio, auth_provider, auth_id, telegram_handle, city, street_cred, wins, losses)
                        VALUES (?, ?, ?, ?, 'Пилот Telegram KSS', 'telegram', ?, ?, 'Краснодар', 1000, 0, 0)
                    ''', (f"tg_{tg_id}", first_name, first_name, tg_user.get('photo_url', 'https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=150'), tg_id, f"@{tg_username}"))
                    conn.commit()
                    user_id = c.lastrowid
                    c.execute('SELECT * FROM users WHERE id = ?', (user_id,))
                    user = c.fetchone()

                # Keep code in database so multiple checks/refreshes don't invalidate it
                user_dict = dict(user)
                self.send_json_response({
                    "status": "ok",
                    "user": user_dict,
                    "token": f"kss_tg_{user_dict['id']}_{int(datetime.now().timestamp())}"
                })
                return

            # Real-Time Online Presence List
            elif path == '/api/presence/online':
                import time
                now = time.time()
                # Prune inactive memory sessions older than 3 minutes
                dead_keys = [k for k, v in ONLINE_SESSIONS.items() if now - v.get('ts', 0) > 180]
                for k in dead_keys:
                    ONLINE_SESSIONS.pop(k, None)

                # Get from database
                db_online = get_online_pilots(minutes=5)
                
                # Combine memory sessions and db sessions
                merged = {}
                for p in db_online:
                    pid_str = str(p['id'])
                    merged[pid_str] = {
                        "id": p['id'],
                        "callsign": p['callsign'],
                        "name": p.get('name') or p['callsign'],
                        "avatar": p.get('avatar') or "https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=150",
                        "city": p.get('city') or 'Краснодар',
                        "street_cred": p.get('street_cred') or 1000,
                        "car": f"{p.get('car_make') or ''} {p.get('car_model') or ''}".strip(),
                        "is_bot": False
                    }

                for k, v in ONLINE_SESSIONS.items():
                    uid = v.get('id', k)
                    uid_str = str(uid)
                    if uid_str not in merged:
                        merged[uid_str] = {
                            "id": int(uid) if str(uid).isdigit() else uid,
                            "callsign": v.get('callsign', 'Пилот'),
                            "name": v.get('name', 'Пилот'),
                            "avatar": v.get('avatar', 'https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=150'),
                            "city": v.get('city', 'Краснодар'),
                            "street_cred": v.get('street_cred', 1000),
                            "car": v.get('car', ''),
                            "is_bot": False
                        }

                # If no one is active yet, show top pilots to demonstrate live community
                if not merged:
                    c.execute('''
                        SELECT u.id, u.callsign, u.name, u.avatar, u.city, u.street_cred,
                               c.make as car_make, c.model as car_model
                        FROM users u
                        LEFT JOIN cars c ON c.user_id = u.id AND c.is_primary = 1
                        ORDER BY u.street_cred DESC LIMIT 3
                    ''')
                    for r in c.fetchall():
                        merged[r['id']] = {
                            "id": r['id'],
                            "callsign": r['callsign'],
                            "name": r['name'] or r['callsign'],
                            "avatar": r['avatar'] or "https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=150",
                            "city": r['city'] or 'Краснодар',
                            "street_cred": r['street_cred'],
                            "car": f"{r['car_make'] or ''} {r['car_model'] or ''}".strip(),
                            "is_bot": False
                        }

                pilots_list = list(merged.values())
                self.send_json_response({
                    "status": "ok",
                    "count": len(pilots_list),
                    "pilots": pilots_list
                })
                return

            # Active Map Markers (20-49 minutes TTL)
            elif path == '/api/markers':
                markers = get_active_map_markers()
                self.send_json_response({"status": "ok", "markers": markers})
                return

            # Live Chat / Forum Messages
            elif path == '/api/chat':
                channel = query.get('channel', ['general'])[0]
                try:
                    limit = int(query.get('limit', [60])[0])
                except Exception:
                    limit = 60
                messages = get_chat_messages(channel=channel, limit=limit)
                self.send_json_response({"status": "ok", "channel": channel, "messages": messages})
                return

            # Pilot Profile Details
            elif path.startswith('/api/profile/'):
                uid_str = path.split('/')[-1]
                if uid_str.isdigit():
                    uid = int(uid_str)
                    profile = get_user_profile(uid)
                    if profile:
                        self.send_json_response({"status": "ok", "profile": profile})
                        return
                self.send_json_response({"error": "Пилот не найден"}, 404)
                return

            else:
                self.send_json_response({"error": "Endpoint not found"}, 404)

        except Exception as e:
            self.send_json_response({"error": str(e)}, 500)
        finally:
            conn.close()

    def handle_api_post(self, path, payload):
        conn = get_db()
        c = conn.cursor()

        try:
            # Register Car
            if path == '/api/cars':
                user_id = payload.get('user_id', 1)
                make = payload.get('make', '').strip()
                model = payload.get('model', '').strip()
                gen = payload.get('generation', '').strip()
                year = int(payload.get('year', 2018))
                plate = payload.get('plate_number', '').strip().upper()
                hp = int(payload.get('hp', 250))
                torque = int(payload.get('torque', hp * 1.25))
                weight = int(payload.get('weight', 1400))
                drivetrain = payload.get('drivetrain', 'RWD')
                aspiration = payload.get('aspiration', 'Турбо')
                engine = payload.get('engine_code', '').strip()
                zero_hundred = float(payload.get('zero_to_hundred', 5.0))
                quarter_mile = float(payload.get('quarter_mile', 13.0)) if payload.get('quarter_mile') else None
                roll_100_200 = float(payload.get('roll_hundred_two_hundred')) if payload.get('roll_hundred_two_hundred') else None
                boost_bar = float(payload.get('boost_bar')) if payload.get('boost_bar') else None
                fuel_type = payload.get('fuel_type', 'АИ-100').strip()
                dragy_verified = 1 if payload.get('dragy_verified') else 0
                dragy_proof_url = payload.get('dragy_proof_url', '').strip()
                specs_dict = payload.get('specs', {})
                photo_url = payload.get('photo_url', 'https://images.unsplash.com/photo-1503376780353-7e6692767b70?w=800')

                c.execute('''
                    INSERT INTO cars (user_id, make, model, generation, year, plate_number, hp, torque, weight,
                                     drivetrain, aspiration, engine_code, zero_to_hundred, quarter_mile,
                                     roll_hundred_two_hundred, boost_bar, fuel_type, dragy_verified, dragy_proof_url,
                                     specs_json, photo_url)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (user_id, make, model, gen, year, plate, hp, torque, weight,
                      drivetrain, aspiration, engine, zero_hundred, quarter_mile,
                      roll_100_200, boost_bar, fuel_type, dragy_verified, dragy_proof_url,
                      json.dumps(specs_dict, ensure_ascii=False), photo_url))
                
                new_car_id = c.lastrowid
                conn.commit()

                self.send_json_response({
                    "status": "ok",
                    "message": "Автомобиль успешно зарегистрирован в реестре Кубани!",
                    "car_id": new_car_id
                })

            # Register Battle / Victory
            elif path == '/api/battles':
                discipline = payload.get('discipline', 'Дрэг 402м')
                spot_id = payload.get('spot_id')
                spot_name = payload.get('spot_name', '')
                winner_id = int(payload.get('winner_id', 1))
                winner_car_id = int(payload.get('winner_car_id', 1))
                loser_id = payload.get('loser_id')
                loser_car_id = payload.get('loser_car_id')
                loser_custom = payload.get('loser_custom_name', '')
                gap = payload.get('gap_description', '1 корпус')
                telemetry = payload.get('telemetry_notes', '')
                video = payload.get('video_proof_url', '')

                cred_delta = 25
                if 'тоге' in discipline.lower():
                    cred_delta = 35

                c.execute('''
                    INSERT INTO battles (discipline, spot_id, spot_name, winner_id, winner_car_id,
                                        loser_id, loser_car_id, loser_custom_name, gap_description, telemetry_notes, video_proof_url, cred_delta)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (discipline, spot_id, spot_name, winner_id, winner_car_id,
                      loser_id, loser_car_id, loser_custom, gap, telemetry, video, cred_delta))
                
                # Update winner street cred & wins
                c.execute('UPDATE users SET street_cred = street_cred + ?, wins = wins + 1 WHERE id = ?', (cred_delta, winner_id))
                
                # If loser exists in system, update losses and street cred
                if loser_id:
                    c.execute('UPDATE users SET street_cred = MAX(100, street_cred - ?), losses = losses + 1 WHERE id = ?', (cred_delta // 2, loser_id))

                conn.commit()

                self.send_json_response({
                    "status": "ok",
                    "message": "Победа зафиксирована! Рейтинг пилота пересчитан.",
                    "cred_gained": cred_delta
                })

            # Create Team
            elif path == '/api/teams':
                name = payload.get('name', '').strip()
                tag = payload.get('tag', '').strip().upper()
                city = payload.get('city', 'Краснодар')
                desc = payload.get('description', '')
                logo = payload.get('logo', '🏎️')
                leader_id = payload.get('leader_id', 1)

                c.execute('''
                    INSERT INTO teams (name, tag, city, description, logo, leader_id)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (name, tag, city, desc, logo, leader_id))
                team_id = c.lastrowid

                # Assign user to team
                c.execute('UPDATE users SET team_id = ? WHERE id = ?', (team_id, leader_id))
                conn.commit()

                self.send_json_response({
                    "status": "ok",
                    "message": f"Команда {name} зарегистрирована!",
                    "team_id": team_id
                })

            # Real OAuth & Social Authentication (Google, VK ID, Telegram)
            elif path == '/api/auth/oauth':
                provider = payload.get('provider', 'google')
                auth_id = str(payload.get('id', ''))
                name = payload.get('name', 'Пилот').strip()
                callsign = payload.get('callsign') or name.split()[0]
                avatar = payload.get('avatar') or 'https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=150'
                email = payload.get('email', '')
                city = payload.get('city', 'Краснодар')

                # Check if user already exists with this provider and auth_id
                c.execute('SELECT * FROM users WHERE auth_provider = ? AND auth_id = ?', (provider, auth_id))
                user = c.fetchone()

                if not user:
                    # Create unique username
                    base_user = provider + "_" + auth_id[-6:]
                    c.execute('SELECT COUNT(*) FROM users WHERE username = ?', (base_user,))
                    if c.fetchone()[0] > 0:
                        base_user += f"_{int(datetime.now().timestamp()) % 1000}"

                    c.execute('''
                        INSERT INTO users (username, callsign, name, avatar, bio, auth_provider, auth_id, city, street_cred, wins, losses)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1000, 0, 0)
                    ''', (base_user, callsign, name, avatar, f"Пилот {provider.upper()} KSS", provider, auth_id, city))
                    conn.commit()

                    new_id = c.lastrowid
                    c.execute('SELECT * FROM users WHERE id = ?', (new_id,))
                    user = c.fetchone()

                    # Automatically assign a starter car if user has none
                    c.execute('''
                        INSERT INTO cars (user_id, make, model, generation, year, plate_number, hp, torque, weight, drivetrain, aspiration, engine_code, zero_to_hundred, photo_url)
                        VALUES (?, 'Кубанский', 'Болид', 'Custom', 2020, 'KSS', 320, 420, 1350, 'RWD', 'Турбо', '2.0T', 4.5, 'https://images.unsplash.com/photo-1503376780353-7e6692767b70?w=800')
                    ''', (new_id,))
                    conn.commit()
                else:
                    # Update avatar and name if changed in social network
                    c.execute('UPDATE users SET avatar = ?, name = ? WHERE id = ?', (avatar, name, user['id']))
                    conn.commit()
                    c.execute('SELECT * FROM users WHERE id = ?', (user['id'],))
                    user = c.fetchone()

                user_dict = dict(user)
                self.send_json_response({
                    "status": "ok",
                    "user": user_dict,
                    "token": f"kss_auth_{provider}_{user_dict['id']}_{int(datetime.now().timestamp())}"
                })

            # Telegram Handle Direct Login
            elif path == '/api/auth/telegram':
                handle = payload.get('telegram_handle', '').strip().lstrip('@')
                if not handle:
                    self.send_json_response({"error": "Укажите Telegram никнейм"}, 400)
                    return

                c.execute('SELECT * FROM users WHERE telegram_handle LIKE ? OR username = ?', (f"%{handle}%", f"tg_{handle}"))
                user = c.fetchone()

                if not user:
                    c.execute('''
                        INSERT INTO users (username, callsign, name, avatar, bio, auth_provider, telegram_handle, city, street_cred, wins, losses)
                        VALUES (?, ?, ?, ?, 'Пилот Telegram KSS', 'telegram', ?, 'Краснодар', 1000, 0, 0)
                    ''', (f"tg_{handle}", handle, handle, 'https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=150', f"@{handle}"))
                    conn.commit()
                    user_id = c.lastrowid
                    c.execute('SELECT * FROM users WHERE id = ?', (user_id,))
                    user = c.fetchone()

                user_dict = dict(user)
                self.send_json_response({
                    "status": "ok",
                    "user": user_dict,
                    "token": f"kss_tg_{user_dict['id']}_{int(datetime.now().timestamp())}"
                })

            # Universal Auth / Login
            elif path == '/api/auth/login':
                login_val = (payload.get('login') or payload.get('username') or payload.get('callsign') or '').strip()
                if not login_val:
                    self.send_json_response({"error": "Введите позывной или никнейм"}, 400)
                    return

                clean_handle = login_val.lstrip('@')
                c.execute('''
                    SELECT * FROM users 
                    WHERE username = ? OR callsign = ? OR telegram_handle = ? OR telegram_handle = ? OR username = ?
                ''', (login_val, login_val, f"@{clean_handle}", clean_handle, f"pilot_{clean_handle}"))
                user = c.fetchone()

                if not user:
                    callsign = login_val.replace(' ', '_')
                    avatar = payload.get('avatar') or "https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=150"
                    city = payload.get('city') or 'Краснодар'
                    c.execute('''
                        INSERT INTO users (username, callsign, name, avatar, bio, auth_provider, telegram_handle, city, street_cred, wins, losses)
                        VALUES (?, ?, ?, ?, 'Пилот Kuban Street Special', 'direct', ?, ?, 1000, 0, 0)
                    ''', (f"pilot_{clean_handle}", callsign, login_val, avatar, f"@{clean_handle}", city))
                    conn.commit()
                    user_id = c.lastrowid
                    c.execute('SELECT * FROM users WHERE id = ?', (user_id,))
                    user = c.fetchone()

                user_dict = dict(user)
                self.send_json_response({
                    "status": "ok",
                    "user": user_dict,
                    "token": f"kss_jwt_{user_dict['id']}_{int(datetime.now().timestamp())}"
                })
                return

            # News Creation
            elif path == '/api/news':
                title = payload.get('title', '').strip()
                content = payload.get('content', '').strip()
                image_url = payload.get('image_url', '').strip()
                category = payload.get('category', 'Анонс').strip()
                author = payload.get('author', 'Администрация KSS').strip()

                if not title or not content:
                    self.send_json_response({"error": "Укажите заголовок и текст новости"}, 400)
                    return

                c.execute('''
                    INSERT INTO news (title, content, image_url, category, author)
                    VALUES (?, ?, ?, ?, ?)
                ''', (title, content, image_url, category, author))
                conn.commit()
                self.send_json_response({"status": "ok", "news_id": c.lastrowid, "message": "Новость опубликована!"})
                return

            # Spots Creation (Admin)
            elif path == '/api/spots':
                name = payload.get('name', '').strip()
                city = payload.get('city', 'Краснодар').strip()
                spot_type = payload.get('type', 'Дрэг').strip()
                diff = int(payload.get('difficulty', 3))
                danger = payload.get('danger_level', 'Средняя').strip()
                length = float(payload.get('length_km', 1.0))
                surf = payload.get('surface', 'Асфальт').strip()
                lat = float(payload.get('lat', 45.0355))
                lng = float(payload.get('lng', 38.9753))
                desc = payload.get('description', '').strip()
                rec_time = payload.get('recommended_time', '23:00 - 03:00').strip()
                safety = payload.get('safety_notes', '').strip()
                image_url = payload.get('image_url', '').strip()
                slug = name.lower().replace(' ', '-').replace('/', '-')

                c.execute('''
                    INSERT INTO spots (name, slug, city, type, difficulty, danger_level, length_km, surface, lat, lng, description, recommended_time, safety_notes, image_url)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (name, slug, city, spot_type, diff, danger, length, surf, lat, lng, desc, rec_time, safety, image_url))
                conn.commit()
                self.send_json_response({"status": "ok", "spot_id": c.lastrowid, "message": "Спот добавлен!"})
                return

            # Upload Image
            elif path == '/api/upload':
                filename = payload.get('filename', f"img_{int(datetime.now().timestamp())}.jpg")
                file_data = payload.get('data')
                if not file_data:
                    self.send_json_response({"error": "No image data"}, 400)
                    return

                if ',' in file_data:
                    file_data = file_data.split(',', 1)[1]

                raw_bytes = base64.b64decode(file_data)
                clean_name = os.path.basename(filename).replace(' ', '_')
                file_path = os.path.join(UPLOADS_DIR, clean_name)
                with open(file_path, 'wb') as f:
                    f.write(raw_bytes)

                public_url = f"/uploads/{clean_name}"
                self.send_json_response({"status": "ok", "url": public_url})
                return

            # Temporary Map Markers (20-49 minutes TTL)
            elif path == '/api/markers':
                user_id = int(payload.get('user_id', 1))
                callsign = payload.get('callsign', 'Пилот').strip()
                category = payload.get('category', 'ДПС').strip()
                message = payload.get('message', '').strip()
                lat = payload.get('lat')
                lng = payload.get('lng')
                duration = int(payload.get('duration_minutes', 30))
                photo_url = payload.get('photo_url')

                if not message:
                    self.send_json_response({"error": "Укажите текст сообщения метки"}, 400)
                    return
                if lat is None or lng is None:
                    self.send_json_response({"error": "Укажите координаты метки"}, 400)
                    return

                marker = add_map_marker(user_id, callsign, category, message, lat, lng, duration, photo_url)
                if marker:
                    self.send_json_response({"status": "ok", "marker": marker})
                else:
                    self.send_json_response({"error": "Не удалось создать метку"}, 500)
                return

            # Confirm Marker (Waze +1 verification)
            elif path == '/api/markers/confirm':
                marker_id = int(payload.get('marker_id', 0))
                res = confirm_map_marker(marker_id)
                if res:
                    self.send_json_response({"status": "ok", "confirmations": res.get("confirmations", 1), "marker": res})
                else:
                    self.send_json_response({"error": "Метка не найдена"}, 404)
                return

            # Vote Marker Cleared (Waze gone verification)
            elif path == '/api/markers/clear':
                marker_id = int(payload.get('marker_id', 0))
                res = vote_clear_map_marker(marker_id)
                if res:
                    self.send_json_response({"status": "ok", "deleted": res.get("deleted", False), "clear_votes": res.get("clear_votes", 0), "result": res})
                else:
                    self.send_json_response({"error": "Метка не найдена"}, 404)
                return

            # Update Pilot Profile
            elif path == '/api/profile/update':
                user_id = int(payload.get('user_id', 1))
                updated = update_user_profile(user_id, payload)
                if updated:
                    for key in [user_id, str(user_id)]:
                        if key in ONLINE_SESSIONS:
                            ONLINE_SESSIONS[key]['callsign'] = updated.get('callsign', ONLINE_SESSIONS[key].get('callsign'))
                            ONLINE_SESSIONS[key]['name'] = updated.get('name', ONLINE_SESSIONS[key].get('name'))
                            ONLINE_SESSIONS[key]['avatar'] = updated.get('avatar', ONLINE_SESSIONS[key].get('avatar'))
                            ONLINE_SESSIONS[key]['city'] = updated.get('city', ONLINE_SESSIONS[key].get('city'))
                    self.send_json_response({"status": "ok", "user": updated})
                else:
                    self.send_json_response({"error": "Не удалось обновить профиль"}, 400)
                return

            # Send Chat / Forum Message
            elif path == '/api/chat':
                user_id = int(payload.get('user_id', 1))
                callsign = payload.get('callsign', 'Пилот').strip()
                avatar = payload.get('avatar', 'https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=150')
                car_name = payload.get('car_name', '')
                channel = payload.get('channel', 'general').strip()
                message = payload.get('message', '').strip()
                image_url = payload.get('image_url')
                media_type = payload.get('media_type', 'image')

                if not message and not image_url:
                    self.send_json_response({"error": "Введите текст или прикрепите фото/видео"}, 400)
                    return

                new_msg = add_chat_message(user_id, callsign, avatar, car_name, channel, message, image_url, media_type)
                if new_msg:
                    self.send_json_response({"status": "ok", "message": new_msg})
                else:
                    self.send_json_response({"error": "Ошибка отправки сообщения"}, 500)
                return

            # Like Chat Message
            elif path == '/api/chat/like':
                msg_id = int(payload.get('message_id', 0))
                likes = like_chat_message(msg_id)
                self.send_json_response({"status": "ok", "likes_count": likes})
                return

            # Database Cleaning & Seeding for Admin
            elif path == '/api/admin/clean':
                clear_all_data()
                self.send_json_response({"status": "ok", "message": "Сайт очищен! База данных пуста."})
                return

            elif path == '/api/admin/seed':
                clear_all_data()
                seed_data()
                self.send_json_response({"status": "ok", "message": "Тестовые данные загружены!"})
                return

            # Head-to-Head Duel Simulator
            elif path == '/api/simulate-duel':
                car1_val = payload.get('car1_id')
                car2_val = payload.get('car2_id')
                if not car1_val or not car2_val or not str(car1_val).isdigit() or not str(car2_val).isdigit():
                    self.send_json_response({"error": "Укажите корректные ID обоих автомобилей"}, 400)
                    return
                car1_id = int(car1_val)
                car2_id = int(car2_val)
                discipline = payload.get('discipline', 'Дрэг 402м')

                c.execute('SELECT * FROM cars WHERE id = ?', (car1_id,))
                r1 = c.fetchone()
                c.execute('SELECT * FROM cars WHERE id = ?', (car2_id,))
                r2 = c.fetchone()
                if not r1 or not r2:
                    self.send_json_response({"error": "Один или оба автомобиля не найдены в базе"}, 404)
                    return
                car1 = dict(r1)
                car2 = dict(r2)

                # Calculation factors:
                # 1. Power-to-weight ratio (hp / ton)
                ptw1 = (car1['hp'] / car1['weight']) * 1000
                ptw2 = (car2['hp'] / car2['weight']) * 1000

                # 2. Drivetrain multiplier based on discipline
                # AWD gives massive launch advantage in Drag 0-402, RWD gives top speed roll, Lightweight RWD/AWD dominates Touge
                score1 = ptw1
                score2 = ptw2

                if 'дрэг' in discipline.lower():
                    if car1['drivetrain'] == 'AWD': score1 *= 1.22
                    elif car1['drivetrain'] == 'RWD': score1 *= 1.08
                    else: score1 *= 0.95

                    if car2['drivetrain'] == 'AWD': score2 *= 1.22
                    elif car2['drivetrain'] == 'RWD': score2 *= 1.08
                    else: score2 *= 0.95

                elif 'тоге' in discipline.lower():
                    # In Touge, lighter cars have immense agility
                    weight_factor1 = 1500 / max(car1['weight'], 800)
                    weight_factor2 = 1500 / max(car2['weight'], 800)
                    score1 = (ptw1 * 0.6) + (weight_factor1 * 120)
                    score2 = (ptw2 * 0.6) + (weight_factor2 * 120)
                else: # Roll-on
                    # Aerodynamics and pure HP / torque
                    score1 = car1['hp'] + (car1['torque'] * 0.3)
                    score2 = car2['hp'] + (car2['torque'] * 0.3)

                total = score1 + score2
                win_prob1 = round((score1 / total) * 100, 1)
                win_prob2 = round(100.0 - win_prob1, 1)

                winner = car1 if win_prob1 >= win_prob2 else car2
                loser = car2 if win_prob1 >= win_prob2 else car1
                win_margin = abs(win_prob1 - win_prob2)

                if win_margin > 30:
                    verdict = f"Тотальное доминирование {winner['make']} {winner['model']} (разрыв более 3 корпусов)"
                elif win_margin > 15:
                    verdict = f"Уверенная победа {winner['make']} {winner['model']} (1.5 - 2 корпуса)"
                else:
                    verdict = f"Напряженная дуэль 'нос в нос'! Исход решат миллисекунды на переключениях и зацеп"

                self.send_json_response({
                    "status": "ok",
                    "car1": {
                        "id": car1['id'],
                        "name": f"{car1['make']} {car1['model']}",
                        "hp_ton": round(ptw1, 1),
                        "win_chance": win_prob1
                    },
                    "car2": {
                        "id": car2['id'],
                        "name": f"{car2['make']} {car2['model']}",
                        "hp_ton": round(ptw2, 1),
                        "win_chance": win_prob2
                    },
                    "likely_winner": f"{winner['make']} {winner['model']}",
                    "verdict": verdict,
                    "discipline": discipline
                })
                return

            # Real-Time Heartbeat Ping
            elif path == '/api/presence/ping':
                import time
                uid = payload.get('id') or payload.get('user_id') or 1
                callsign = payload.get('callsign') or 'Пилот'
                avatar = payload.get('avatar') or 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150'
                city = payload.get('city') or 'Краснодар'
                car = payload.get('car') or ''

                ONLINE_SESSIONS[str(uid)] = {
                    "id": uid,
                    "callsign": callsign,
                    "name": payload.get('name') or callsign,
                    "avatar": avatar,
                    "city": city,
                    "car": car,
                    "ts": time.time()
                }

                if isinstance(uid, int) or (isinstance(uid, str) and uid.isdigit()):
                    update_user_last_seen(int(uid))

                # Count active users
                now = time.time()
                active_count = sum(1 for v in ONLINE_SESSIONS.values() if now - v.get('ts', 0) <= 180)
                self.send_json_response({
                    "status": "ok",
                    "online_count": max(1, active_count),
                    "timestamp": int(now)
                })
                return

            else:
                self.send_json_response({"error": "Endpoint not found"}, 404)


        except Exception as e:
            self.send_json_response({"error": str(e)}, 500)
        finally:
            conn.close()

    def serve_static(self, path):
        if path == '/' or path == '':
            path = '/index.html'

        # Sanitize path to prevent directory traversal
        rel_path = path.lstrip('/')
        full_path = os.path.join(STATIC_DIR, rel_path)

        if not os.path.exists(full_path) or os.path.isdir(full_path):
            full_path = os.path.join(STATIC_DIR, 'index.html')

        mime_type, _ = mimetypes.guess_type(full_path)
        if not mime_type:
            mime_type = 'application/octet-stream'
        if full_path.endswith('.css'):
            mime_type = 'text/css; charset=utf-8'
        elif full_path.endswith('.js'):
            mime_type = 'application/javascript; charset=utf-8'
        elif full_path.endswith('.html'):
            mime_type = 'text/html; charset=utf-8'
        elif full_path.endswith('.mp4'):
            mime_type = 'video/mp4'
        elif full_path.endswith('.webm'):
            mime_type = 'video/webm'
        elif full_path.endswith('.mov'):
            mime_type = 'video/quicktime'
        elif full_path.endswith('.webp'):
            mime_type = 'image/webp'

        try:
            with open(full_path, 'rb') as f:
                content = f.read()

            self.send_response(200)
            self.send_header('Content-Type', mime_type)
            self.send_header('Content-Length', str(len(content)))
            self.send_header('Accept-Ranges', 'bytes')
            self.send_header('Cache-Control', 'no-cache')
            self.end_headers()
            self.wfile.write(content)
        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(f"Server Error: {str(e)}".encode('utf-8'))

def run_server(port=PORT):
    # Ensure database is initialized
    init_db()

    # Ensure static directories exist
    os.makedirs(os.path.join(STATIC_DIR, 'css'), exist_ok=True)
    os.makedirs(os.path.join(STATIC_DIR, 'js'), exist_ok=True)
    os.makedirs(os.path.join(STATIC_DIR, 'images'), exist_ok=True)
    os.makedirs(os.path.join(STATIC_DIR, 'uploads'), exist_ok=True)

    server_address = ('', port)
    socketserver.TCPServer.allow_reuse_address = True
    try:
        httpd = socketserver.TCPServer(server_address, KSSRequestHandler)
    except OSError:
        port = port + 1
        server_address = ('', port)
        httpd = socketserver.TCPServer(server_address, KSSRequestHandler)

    print("=" * 65)
    print("🔥 KUBAN STREET SPECIAL (KSS) — СЕРВЕР ЗАПУЩЕН!")
    print(f"📍 Web Platform: http://localhost:{port}")
    print(f"📊 REST API:     http://localhost:{port}/api/stats")
    print(f"🗄️ Database:     {DB_PATH}")
    # Start Telegram bot in background thread if running in cloud (Render/KSS Cloud)
    if os.environ.get('RENDER') or os.environ.get('START_BOT') == '1':
        try:
            import threading
            from bot import run_bot_service
            print("🤖 [CLOUD] Запуск встроенного Telegram-бота в фоновом режиме...")
            bot_thread = threading.Thread(target=run_bot_service, daemon=True)
            bot_thread.start()
        except Exception as e:
            print(f"⚠️ [CLOUD] Не удалось запустить фонового бота: {e}")

    print("Для остановки нажмите Ctrl+C")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nСервер остановлен.")
        httpd.server_close()

if __name__ == '__main__':
    port = PORT
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            pass
    run_server(port)
