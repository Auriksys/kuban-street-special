"""
KubanStreetSpecial - Database & Seed Data
SQLite schema and realistic initial data for Krasnodar Krai street racers.
"""

import sqlite3
import os
import json
from datetime import datetime, timedelta

DB_PATH = os.path.join(os.path.dirname(__file__), 'kss.sqlite')

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()

    # Users / Pilots table
    c.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        callsign TEXT NOT NULL,
        name TEXT,
        city TEXT DEFAULT 'Краснодар',
        avatar TEXT,
        bio TEXT,
        auth_provider TEXT DEFAULT 'local', -- 'google', 'vk', 'telegram', 'local'
        auth_id TEXT,
        telegram_handle TEXT,
        vk_url TEXT,
        street_cred INTEGER DEFAULT 1000,
        wins INTEGER DEFAULT 0,
        team_id INTEGER,
        last_seen TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # Safely migrate existing users table to add last_seen and losses if missing
    try:
        c.execute('ALTER TABLE users ADD COLUMN last_seen TIMESTAMP')
    except Exception:
        pass
    try:
        c.execute('ALTER TABLE users ADD COLUMN losses INTEGER DEFAULT 0')
    except Exception:
        pass


    # Teams / Syndicates table
    c.execute('''
    CREATE TABLE IF NOT EXISTS teams (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        tag TEXT NOT NULL,
        city TEXT DEFAULT 'Краснодар',
        description TEXT,
        logo TEXT,
        leader_id INTEGER,
        cred_score INTEGER DEFAULT 2500,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # Cars table
    c.execute('''
    CREATE TABLE IF NOT EXISTS cars (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        make TEXT NOT NULL,
        model TEXT NOT NULL,
        generation TEXT,
        year INTEGER,
        plate_number TEXT,
        hp INTEGER NOT NULL,
        torque INTEGER,
        weight INTEGER,
        drivetrain TEXT NOT NULL, -- 'RWD', 'AWD', 'FWD'
        aspiration TEXT NOT NULL, -- 'Турбо', 'Атмо', 'Компрессор', 'Твин-турбо', 'Свап'
        engine_code TEXT, -- e.g. '1JZ-GTE', 'EA888 Gen3', 'EJ207', '21126 Turbo', 'B58'
        zero_to_hundred REAL, -- 0-100 sec
        quarter_mile REAL, -- 402m sec
        specs_json TEXT, -- JSON with suspension, brakes, ecu tune, tires, mods
        photo_url TEXT,
        is_primary INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    )
    ''')

    # Spots / Locations in Krasnodar Krai
    c.execute('''
    CREATE TABLE IF NOT EXISTS spots (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        slug TEXT UNIQUE,
        region TEXT DEFAULT 'Краснодарский край',
        city TEXT NOT NULL,
        type TEXT NOT NULL, -- 'Дрэг', 'Тоге', 'Дрифт', 'Ролл-он'
        difficulty INTEGER DEFAULT 3, -- 1-5
        danger_level TEXT DEFAULT 'Средняя', -- 'Низкая', 'Средняя', 'Высокая (Камеры/ДПС)'
        length_km REAL,
        elevation_gain_m INTEGER,
        surface TEXT DEFAULT 'Асфальт',
        lat REAL NOT NULL,
        lng REAL NOT NULL,
        description TEXT,
        recommended_time TEXT DEFAULT '22:00 - 03:00',
        safety_notes TEXT,
        image_url TEXT
    )
    ''')

    # Battles / Races log
    c.execute('''
    CREATE TABLE IF NOT EXISTS battles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        discipline TEXT NOT NULL, -- 'Дрэг 402м', 'Тоге (Спуск)', 'Тоге (Подъем)', 'Ролл 60-200'
        spot_id INTEGER,
        spot_name TEXT,
        winner_id INTEGER NOT NULL,
        winner_car_id INTEGER NOT NULL,
        loser_id INTEGER,
        loser_car_id INTEGER,
        loser_custom_name TEXT, -- if loser car is not in system
        gap_description TEXT, -- '2 корпуса', '0.3 сек', 'Поул-позишн с отрывом'
        telemetry_notes TEXT,
        video_proof_url TEXT,
        cred_delta INTEGER DEFAULT 25,
        date_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        is_verified INTEGER DEFAULT 1,
        FOREIGN KEY (winner_id) REFERENCES users(id),
        FOREIGN KEY (winner_car_id) REFERENCES cars(id),
        FOREIGN KEY (spot_id) REFERENCES spots(id)
    )
    ''')

    # Auth codes table for Telegram Login
    c.execute('''
    CREATE TABLE IF NOT EXISTS auth_codes (
        code TEXT PRIMARY KEY,
        telegram_id TEXT,
        username TEXT,
        first_name TEXT,
        photo_url TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # News & Announcements table
    c.execute('''
    CREATE TABLE IF NOT EXISTS news (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        content TEXT NOT NULL,
        image_url TEXT,
        category TEXT DEFAULT 'Объявление',
        author TEXT DEFAULT 'Администрация KSS',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # Map Live Temporary Markers (20-49 minutes TTL)
    c.execute('''
    CREATE TABLE IF NOT EXISTS map_markers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        callsign TEXT NOT NULL,
        category TEXT NOT NULL, -- 'ДПС', 'Сходка', 'Опасность', 'Сообщение'
        message TEXT NOT NULL,
        lat REAL NOT NULL,
        lng REAL NOT NULL,
        duration_minutes INTEGER DEFAULT 30, -- strictly 20-49 minutes
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        expires_at TIMESTAMP NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    )
    ''')

    # Safe migrations for serious automotive telemetry & Waze voting
    for col, col_type in [
        ('roll_hundred_two_hundred', 'REAL'),
        ('boost_bar', 'REAL'),
        ('fuel_type', "TEXT DEFAULT 'АИ-100'"),
        ('dragy_verified', 'INTEGER DEFAULT 0'),
        ('dragy_proof_url', 'TEXT')
    ]:
        try:
            c.execute(f'ALTER TABLE cars ADD COLUMN {col} {col_type}')
        except Exception:
            pass

    for col, col_type in [
        ('confirmations', 'INTEGER DEFAULT 1'),
        ('clear_votes', 'INTEGER DEFAULT 0'),
        ('photo_url', 'TEXT'),
        ('video_url', 'TEXT')
    ]:
        try:
            c.execute(f'ALTER TABLE map_markers ADD COLUMN {col} {col_type}')
        except Exception:
            pass

    for col, col_type in [
        ('media_type', "TEXT DEFAULT 'image'"),
        ('video_url', 'TEXT')
    ]:
        try:
            c.execute(f'ALTER TABLE chat_messages ADD COLUMN {col} {col_type}')
        except Exception:
            pass

    # Chat Messages (Live Forum / Radio Channels)
    c.execute('''
    CREATE TABLE IF NOT EXISTS chat_messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        callsign TEXT NOT NULL,
        avatar TEXT,
        car_name TEXT,
        channel TEXT DEFAULT 'general', -- 'general', 'battles', 'tech', 'radar'
        message TEXT NOT NULL,
        image_url TEXT,
        likes_count INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
    )
    ''')

    # Seed sample chat messages if empty
    try:
        c.execute('SELECT COUNT(*) FROM chat_messages')
        if c.fetchone()[0] == 0:
            sample_msgs = [
                (1, "Красный_Чайзер", "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150", "Toyota Chaser (620 hp)", "general", "Салют пилотам Кубани! Сегодня к 23:30 собираемся на парковке OZ Mall. Зацепим телеметрию Dragy, кто хотел ролл 100-200 — подтягивайтесь!", None, 6),
                (2, "Кубанский_Буст", "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150", "Toyota Supra A90 (540 hp)", "radar", "На Семерых Ветрах в Новороссе асфальт чистый и сухой, тумана нет. Кто на тоге сегодня?", None, 4),
                (3, "Ваг_Монстр", "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=150", "VW Golf 7R (480 hp)", "tech", "Залили новый софт на DSG DQ250 и Stage 3. Сняли 3.4 сек 0-100 с лаунча на обычном зацепе. В tech-ветке выложу логи наддува.", None, 9),
                (4, "Армавирский_Дьявол", "https://images.unsplash.com/photo-1522075469751-3a6694fb2f61?w=150", "ВАЗ 2107 Turbo (380 hp)", "battles", "Кто на квотер на OZ Mall? Выкатываем классику на 1.8 бара, ищем соперников на заднем приводе до 500 сил!", None, 7),
                (1, "Красный_Чайзер", "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150", "Toyota Chaser (620 hp)", "radar", "Внимание: на Ростовском шоссе перед выездом экипаж ДПС с камерой на треноге в кустах. Сбавили до 60.", None, 8)
            ]
            c.executemany('''
                INSERT INTO chat_messages (user_id, callsign, avatar, car_name, channel, message, image_url, likes_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', sample_msgs)
    except Exception as e:
        print("Chat seed notice:", e)

    conn.commit()
    conn.close()
    print("Database initialized successfully at", DB_PATH)

def clear_all_data(conn=None):
    close_after = False
    if conn is None:
        conn = get_db()
        close_after = True
    c = conn.cursor()
    c.execute('DELETE FROM battles')
    c.execute('DELETE FROM cars')
    c.execute('DELETE FROM spots')
    c.execute('DELETE FROM teams')
    c.execute('DELETE FROM users')
    c.execute('DELETE FROM news')
    c.execute('DELETE FROM auth_codes')
    c.execute('DELETE FROM map_markers')
    c.execute('DELETE FROM chat_messages')
    conn.commit()
    if close_after:
        conn.close()
    print("🧹 Вся база данных успешно очищена! Сайт пуст.")

def seed_data(conn=None):
    close_after = False
    if conn is None:
        conn = get_db()
        close_after = True
    c = conn.cursor()

    # 1. Teams
    teams = [
        ("Kuban Midnight Syndicate", "KMS", "Краснодар", "Главный ночной синдикат Кубани. Быстрые ролл-оны по объездной и Тургеневскому.", "🔥", 3850),
        ("Black Sea Touge Runners", "BSTR", "Новороссийск", "Короли перевалов и серпантинов Черноморского побережья. Абрау, Семь Ветров, Шесхарис.", "⛰️", 4200),
        ("Sochi Drift Cartel", "SDC", "Сочи", "Узкие горные дорожки Красной Поляны, Ахуна и олимпийский асфальт. Стиль и угол.", "⚡", 3500),
        ("Armavir Drag Force", "ADF", "Армавир", "Турбо-корчи, злые ВАЗы на гарреттах и бескомпромиссные 402 метра.", "🏁", 3100),
    ]
    c.executemany('''
        INSERT INTO teams (name, tag, city, description, logo, cred_score)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', teams)

    # 2. Users (Pilots)
    users = [
        ("marko_krd", "Красный_Чайзер", "Марк Осипов", "Краснодар", "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150", "Touge & Drag. Всегда на связи на OZ Mall.", "vk", "vk_101", "@marko_krd", "https://vk.com/id_marko", 1480, 24, 5, 1),
        ("vlad_supra", "Кубанский_Буст", "Владислав Т.", "Новороссийск", "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150", "Семь Ветров — мой дом. Спускаюсь быстрее гравитации.", "google", "goog_102", "@vlad_boost", "", 1620, 31, 3, 2),
        ("artem_ea888", "Ваг_Монстр", "Артём Климов", "Краснодар", "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=150", "Golf 7R Stage 3. Дрэг 402м, стабильные 3.2с 0-100.", "telegram", "tg_103", "@artem_ea888", "https://vk.com/artem_klim", 1540, 28, 7, 1),
        ("denis_turbo07", "Армавирский_Дьявол", "Денис С.", "Армавир", "https://images.unsplash.com/photo-1522075469751-3a6694fb2f61?w=150", "2107 16V TD05-20G, расчетных 380 сил. Охотник на иномарки.", "local", "loc_104", "@den_turbo07", "", 1390, 19, 9, 4),
        ("sochi_silvia", "Дрифт_Фантом", "Эдуард Мамикон", "Сочи", "https://images.unsplash.com/photo-1492562080023-ab3db95bfbce?w=150", "Ахун и Красная поляна. Поймаешь — угощу хинкали.", "telegram", "tg_105", "@sochi_silvia", "", 1430, 21, 6, 3),
        ("tourerv_krd", "Джей_Зет", "Руслан Касумов", "Краснодар", "https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=150", "JZX100 Tourer V. 500+ hp на холсете. Крайний ряд всегда свободен.", "local", "loc_106", "@rus_jzx", "", 1310, 15, 8, 1),
    ]
    c.executemany('''
        INSERT INTO users (username, callsign, name, city, avatar, bio, auth_provider, auth_id, telegram_handle, vk_url, street_cred, wins, losses, team_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', users)

    # 3. Cars with Professional Telemetry (0-100, 100-200, 402m, Boost bar, Fuel, Dragy)
    cars = [
        # (user_id, make, model, gen, year, plate, hp, torque, weight, drivetrain, aspiration, engine, 0-100, 402m, 100-200, boost, fuel, dragy, specs_json, photo, is_primary)
        (1, "Toyota", "Chaser", "JZX100", 1998, "К999УБ93", 460, 580, 1480, "RWD", "Турбо", "1JZ-GTE VVT-i", 4.1, 11.8, 7.8, 1.6, "АИ-100", 1,
         json.dumps({"turbo": "Garrett GTX3076R Gen2", "ecu": "AEM Infinity Standalone", "brakes": "Brembo 6-pot от C63 AMG", "suspension": "Tein Flex Z коиловеры", "tires": "Toyo Proxes R888R полуслик", "transmission": "R154 усиленная мешалка"}),
         "https://images.unsplash.com/photo-1617814076367-b759c7d7e738?w=800", 1),
        
        (2, "Toyota", "GR Supra", "A90", 2021, "В777ОР123", 530, 710, 1520, "RWD", "Турбо", "B58 3.0 Turbo", 3.4, 10.9, 6.4, 1.8, "АИ-100 + WMI", 1,
         json.dumps({"turbo": "Pure800 Hybrid Turbo", "ecu": "Bootmod3 Custom Map (98+WMI)", "exhaust": "Armytrix Valvetronic безкат", "suspension": "KW Clubsport 3-way", "brakes": "AP Racing Pro 5000R", "tires": "Michelin Pilot Sport Cup 2"}),
         "https://images.unsplash.com/photo-1617788138017-80ad40651399?w=800", 1),

        (3, "Volkswagen", "Golf R", "Mk7.5", 2019, "А007МР23", 480, 590, 1495, "AWD", "Турбо", "2.0 TSI EA888.3", 3.2, 10.7, 7.2, 1.9, "АИ-100", 1,
         json.dumps({"turbo": "IS38 EQT Vortex XL", "ecu": "Etuners Stage 3 + TCU DQ381", "intercooler": "Wagner Tuning Competition", "brakes": "Audi RS3 370mm роторы", "launch_control": "Двухступенчатый лаунч 4200 об/мин", "tires": "Continental SportContact 7"}),
         "https://images.unsplash.com/photo-1541899481282-d53bffe3c35d?w=800", 1),

        (4, "ВАЗ", "2107", "Классика", 2008, "С2107ХК93", 380, 420, 990, "RWD", "Свап / Турбо", "ВАЗ 21126 16V Турбо", 4.3, 11.9, 8.4, 1.7, "АИ-98", 1,
         json.dumps({"turbo": "Mitsubishi TD05-20G дует 1.7 бара", "ecu": "Январь 7.2 дад/дтв кастом прошивка", "gearbox": "КПП Getrag 260 от BMW", "rear_axle": "Мост Volvo 940 с дисковой блокой", "safety": "Болтовой каркас безопасности", "tires": "Federal 595 RS-R"}),
         "https://images.unsplash.com/photo-1605559424843-9e4c228bf1c2?w=800", 1),

        (5, "Nissan", "Silvia", "S15", 2001, "М015РХ123", 410, 490, 1220, "RWD", "Турбо", "SR20DET Blacktop", 4.4, 12.2, 8.9, 1.4, "АИ-100", 0,
         json.dumps({"turbo": "Tomei ARMS M7960", "ecu": "Apex'i PowerFC", "suspension": "DG-5 Touge Spec", "diff": "Nismo 2-Way LSD", "aero": "Vertex Edge Widebody", "steering": "Выворот Wisefab Touge Kit"}),
         "https://images.unsplash.com/photo-1552519507-da3b142c6e3d?w=800", 1),

        (6, "Toyota", "Mark II", "JZX100", 1999, "Е100ХА93", 510, 640, 1530, "RWD", "Турбо", "1.5JZ-GTE (Строкер)", 3.9, 11.4, 7.1, 2.0, "E85 Спирт", 1,
         json.dumps({"turbo": "Holset HX40 Super", "ecu": "Link G4+ Extreme", "cooling": "Радиатор Koyorad 53mm + маслокулер Trust", "sound": "Прямой тракт Fujitsubo 85mm", "clutch": "Двухдисковая керамика OS Giken"}),
         "https://images.unsplash.com/photo-1542282088-72c9c27ed0cd?w=800", 1),
    ]
    c.executemany('''
        INSERT INTO cars (user_id, make, model, generation, year, plate_number, hp, torque, weight, drivetrain, aspiration, engine_code, zero_to_hundred, quarter_mile, roll_hundred_two_hundred, boost_bar, fuel_type, dragy_verified, specs_json, photo_url, is_primary)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', cars)

    # 4. Iconic Spots of Krasnodar Krai
    spots = [
        ("OZ Mall Прямик", "oz-mall-drag", "Краснодарский край", "Краснодар", "Дрэг", 2, "Средняя", 1.2, 5, "Идеальный свежий асфальт", 45.0118, 39.1245, 
         "Главное место сбора драг-рейсеров Краснодара. Широкая прямая, отличный зацеп для лаунча и прогрева резины. Сборы каждую пятницу и субботу после 23:00.", "23:00 - 02:30", "Следите за хвостом при торможении, на съезде к ТЦ бывают лежачие полицейские.", "https://images.unsplash.com/photo-1568605117036-5fe5e7bab0b7?w=800"),
        
        ("Семь Ветров (Андреевский перевал)", "sem-vetrov-touge", "Краснодарский край", "Новороссийск", "Тоге", 5, "Высокая", 6.8, 480, "Асфальт с микро-неровностями, закрытые шпильки 180°", 44.7315, 37.8242,
         "Культовое тоге Кубани. Легендарный серпантин над Новороссийской бухтой. 14 шпилек, перепад высот почти полкилометра. Только для опытных пилотов с жесткими тормозами.", "00:00 - 04:00", "Ограждения есть не везде! Обязательна проверка тормозов перед спуском. В туман не выезжать.", "https://images.unsplash.com/photo-1506744038136-46273834b3fb?w=800"),

        ("Шаумянский перевал", "shaumyan-rally-touge", "Краснодарский край", "Туапсинский район", "Тоге", 5, "Высокая", 11.2, 530, "Смешанный: Асфальт + укатанный гравий (Ралли-стиль)", 44.3312, 39.3128,
         "Самое хардкорное раллийно-тоге место на юге. Знаменитый пыльный перевал между Апшеронском и Туапсе. Тест на прочность подвески и мастерство контроля скольжения.", "22:00 - 03:00", "Пылевая завеса за машиной соперника снижает видимость до 2 метров. Дистанция минимум 50 метров.", "https://images.unsplash.com/photo-1469854523086-cc02fe5d8800?w=800"),

        ("Абрау-Дюрсо — Южная Озереевка", "abrau-touge", "Краснодарский край", "Новороссийск / Абрау", "Тоге", 4, "Средняя", 8.4, 260, "Гладкий курортный асфальт, связки быстрых дуг", 44.7011, 37.6019,
         "Живописный техничный серпантин среди виноградников и скал. Отлично подходит для FWD хот-хэтчей и сбалансированных RWD за счет обилия перекладок 3-й передачи.", "23:30 - 03:30", "Летом возможен нанос мелкой щебенки на апексах поворотов.", "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=800"),

        ("Тургеневское Шоссе / Мега Адыгея", "turgenev-roll-drag", "Краснодарский край", "Краснодар / Яблоновский", "Ролл-он", 2, "Средняя", 2.4, 0, "Многополосный ровный автобан", 45.0189, 38.9320,
         "Традиционная зона ролл-он дуэлей 60-200 и 100-250 км/ч. Удобный разворот на клеверной развязке, хорошая видимость на километры вперед.", "00:00 - 03:00", "Внимание на стыки путепровода. Камеры контроля скорости на выезде из города.", "https://images.unsplash.com/photo-1544620347-c4fd4a3d5957?w=800"),

        ("Горячий Ключ — Фанагорийское (Старая Джубга)", "goryachy-klyuch-touge", "Краснодарский край", "Горячий Ключ", "Тоге", 4, "Средняя", 14.5, 340, "Горный асфальт в густом лесу", 44.5821, 39.1120,
         "Уединенный лесной серпантин без гражданского трафика ночью. Прохладный горный воздух дает турбомоторам максимальную отдачу. Быстрые перепады высот.", "23:00 - 04:00", "Ночью возможен выход диких животных (лисы, олени). Обязателен хороший свет фар.", "https://images.unsplash.com/photo-1511497584788-87676104235f?w=800"),

        ("Знаменский Прямик (Восточный обход)", "znamensky-drag", "Краснодарский край", "Краснодар", "Дрэг", 1, "Низкая", 1.8, 0, "Широкая 4-полосная магистраль", 45.0645, 39.1560,
         "Ночная площадка для замеров Racelogic и Dragy. Безопасная полоса торможения длиной более километра.", "01:00 - 04:00", "Чистый зацеп, минимум боковых помех.", "https://images.unsplash.com/photo-1492144534655-ae79c964c9d7?w=800"),

        ("Красная Поляна — Роза Хутор", "sochi-polyana-touge", "Краснодарский край", "Сочи", "Тоге", 4, "Средняя", 18.0, 620, "Олимпийский премиум-асфальт", 43.6820, 40.2450,
         "Лучшее дорожное покрытие в стране. Скоростные горные дуги, туннели с невероятной акустикой выхлопа и крутые градиенты подъема.", "00:30 - 04:30", "Соблюдайте акустический режим в жилых зонах курорта.", "https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?w=800")
    ]
    c.executemany('''
        INSERT INTO spots (name, slug, region, city, type, difficulty, danger_level, length_km, elevation_gain_m, surface, lat, lng, description, recommended_time, safety_notes, image_url)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', spots)

    # 5. Battles Log (Real battle history)
    battles = [
        ("Дрэг 402м", 1, "OZ Mall Прямик", 3, 3, 1, 1, "", "0.4 сек (1.5 корпуса на финише)", "Golf R выстрелил с лаунча (1.6с 60ft), Chaser догонял на 3-й передаче, но не хватило дистанции", "https://youtube.com/watch?v=kss_drag_oz1", 30, "2026-09-26 23:45:00"),
        ("Тоге (Спуск)", 2, "Семь Ветров (Андреевский перевал)", 2, 2, 5, 5, "", "Отрыв более 50 метров к 8-й шпильке", "Supra на Cup2 резине показала невероятный держак в апексах. Silvia перегрела передние колодки к середине спуска", "", 45, "2026-09-24 01:20:00"),
        ("Дрэг 402м", 1, "OZ Mall Прямик", 4, 4, 6, 6, "", "Полкорпуса на финише (Сенсация ночи!)", "Злая 'семерка' на 1.7 бара ушла в точку со старта, Марк догонял со свистом вестгейта, но финишная черта спасла жигу", "https://t.me/kubanstreet/142", 50, "2026-09-20 00:15:00"),
        ("Ролл 60-200", 5, "Тургеневское Шоссе / Мега Адыгея", 2, 2, 3, 3, "", "3 корпуса в пользу Супры", "B58 на Pure800 после 130 км/ч начал стремительно уезжать от EA888", "", 25, "2026-09-18 02:10:00"),
        ("Тоге (Подъем)", 4, "Абрау-Дюрсо — Южная Озереевка", 1, 1, 5, 5, "", "1 корпус на выходе из связки", "Марк на 1JZ вывез за счет гигантского момента на выходе из шпилек 2-й передачи", "", 35, "2026-09-12 23:55:00"),
        ("Дрэг 402м", 7, "Знаменский Прямик (Восточный обход)", 3, 3, 4, 4, "", "2 корпуса", "Полный привод Golf R не оставил шансов заднему приводу жигулей на холодном ночном асфальте", "", 20, "2026-09-08 01:40:00")
    ]
    c.executemany('''
        INSERT INTO battles (discipline, spot_id, spot_name, winner_id, winner_car_id, loser_id, loser_car_id, loser_custom_name, gap_description, telemetry_notes, video_proof_url, cred_delta, date_time)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', battles)

    sample_msgs = [
        (1, "Красный_Чайзер", "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150", "Toyota Chaser (620 hp)", "general", "Салют пилотам Кубани! Сегодня к 23:30 собираемся на парковке OZ Mall. Зацепим телеметрию Dragy, кто хотел ролл 100-200 — подтягивайтесь!", None, 6),
        (2, "Кубанский_Буст", "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150", "Toyota Supra A90 (540 hp)", "radar", "На Семерых Ветрах в Новороссе асфальт чистый и сухой, тумана нет. Кто на тоге сегодня?", None, 4),
        (3, "Ваг_Монстр", "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=150", "VW Golf 7R (480 hp)", "tech", "Залили новый софт на DSG DQ250 и Stage 3. Сняли 3.4 сек 0-100 с лаунча на обычном зацепе. В tech-ветке выложу логи наддува.", None, 9),
        (4, "Армавирский_Дьявол", "https://images.unsplash.com/photo-1522075469751-3a6694fb2f61?w=150", "ВАЗ 2107 Turbo (380 hp)", "battles", "Кто на квотер на OZ Mall? Выкатываем классику на 1.8 бара, ищем соперников на заднем приводе до 500 сил!", None, 7),
        (1, "Красный_Чайзер", "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150", "Toyota Chaser (620 hp)", "radar", "Внимание: на Ростовском шоссе перед выездом экипаж ДПС с камерой на треноге в кустах. Сбавили до 60.", None, 8)
    ]
    c.executemany('''
        INSERT INTO chat_messages (user_id, callsign, avatar, car_name, channel, message, image_url, likes_count)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', sample_msgs)

    sample_news = [
        ("Ночной сбор пилотов на OZ Mall: Замеры телеметрии Dragy", 
         "В эту субботу в 23:30 на парковке OZ Mall собираются лучшие пилоты Краснодара. Будут замеры 0-100, 100-200 и 402 метра с официальным Dragy. Приглашаются классы до 450 л.с. и Unlimited. Соблюдайте регламент безопасности.",
         "https://images.unsplash.com/photo-1568605117036-5fe5e7bab0b7?w=800",
         "Сходка", "Администрация KSS"),
        ("Открытие сезона горных заездов на Семи Ветрах (Новороссийск)", 
         "Асфальт на Андреевском перевале полностью прогрет и очищен. Напоминаем о необходимости проверки тормозной жидкости перед выездом на спуск. Сборы синдиката BSTR ежедневно после полуночи.",
         "https://images.unsplash.com/photo-1506744038136-46273834b3fb?w=800",
         "Трассы", "BSTR Syndicate"),
        ("Обновление телеметрии и дуэль-симулятора KSS", 
         "В систему добавлен расчет развесовки по осям, учет типа привода (AWD лаунч vs RWD roll) и расчет удельной мощности (л.с./тонну). Фиксируйте свои победы через личный кабинет!",
         "https://images.unsplash.com/photo-1617814076367-b759c7d7e738?w=800",
         "Обновление", "KSS Tech Team")
    ]
    c.executemany('''
        INSERT INTO news (title, content, image_url, category, author)
        VALUES (?, ?, ?, ?, ?)
    ''', sample_news)

    conn.commit()
    if close_after:
        conn.close()
    print("📦 Демо-данные успешно загружены в базу!")

def update_user_last_seen(user_id):
    try:
        conn = get_db()
        c = conn.cursor()
        c.execute('UPDATE users SET last_seen = CURRENT_TIMESTAMP WHERE id = ?', (user_id,))
        conn.commit()
        conn.close()
    except Exception as e:
        print("Presence update error:", e)

def get_online_pilots(minutes=5):
    try:
        conn = get_db()
        c = conn.cursor()
        c.execute('''
            SELECT u.id, u.username, u.callsign, u.name, u.city, u.avatar, u.street_cred, u.telegram_handle,
                   c.make as car_make, c.model as car_model, c.hp as car_hp,
                   u.last_seen
            FROM users u
            LEFT JOIN cars c ON c.user_id = u.id AND c.is_primary = 1
            WHERE u.last_seen >= datetime('now', '-' || ? || ' minutes')
            ORDER BY u.last_seen DESC
        ''', (minutes,))
        rows = [dict(r) for r in c.fetchall()]
        conn.close()
        return rows
    except Exception as e:
        print("Get online error:", e)
        return []

def add_map_marker(user_id, callsign, category, message, lat, lng, duration_minutes=30, photo_url=None):
    try:
        # Strictly enforce 20 to 49 minutes
        duration = min(49, max(20, int(duration_minutes)))
        now = datetime.now()
        expires = now + timedelta(minutes=duration)
        expires_str = expires.strftime('%Y-%m-%d %H:%M:%S')

        conn = get_db()
        c = conn.cursor()
        c.execute('''
            INSERT INTO map_markers (user_id, callsign, category, message, lat, lng, duration_minutes, expires_at, photo_url)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, callsign, category, message, float(lat), float(lng), duration, expires_str, photo_url))
        marker_id = c.lastrowid
        conn.commit()

        c.execute('SELECT * FROM map_markers WHERE id = ?', (marker_id,))
        row = dict(c.fetchone())
        conn.close()

        row['remaining_seconds'] = duration * 60
        return row
    except Exception as e:
        print("add_map_marker error:", e)
        return None

def get_active_map_markers():
    try:
        conn = get_db()
        c = conn.cursor()
        now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Auto-delete expired markers
        c.execute('DELETE FROM map_markers WHERE expires_at < ?', (now_str,))
        conn.commit()

        c.execute('SELECT * FROM map_markers ORDER BY created_at DESC')
        rows = [dict(r) for r in c.fetchall()]
        conn.close()

        now = datetime.now()
        for r in rows:
            try:
                exp = datetime.strptime(r['expires_at'], '%Y-%m-%d %H:%M:%S')
                rem = int((exp - now).total_seconds())
                r['remaining_seconds'] = max(0, rem)
            except Exception:
                r['remaining_seconds'] = r.get('duration_minutes', 30) * 60

        return rows
    except Exception as e:
        print("get_active_map_markers error:", e)
        return []

def delete_map_marker(marker_id):
    try:
        conn = get_db()
        c = conn.cursor()
        c.execute('DELETE FROM map_markers WHERE id = ?', (marker_id,))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print("delete_map_marker error:", e)
        return False

def confirm_map_marker(marker_id):
    try:
        conn = get_db()
        c = conn.cursor()
        c.execute('UPDATE map_markers SET confirmations = COALESCE(confirmations, 1) + 1 WHERE id = ?', (marker_id,))
        conn.commit()
        c.execute('SELECT * FROM map_markers WHERE id = ?', (marker_id,))
        row = c.fetchone()
        conn.close()
        return dict(row) if row else None
    except Exception as e:
        print("confirm_map_marker error:", e)
        return None

def vote_clear_map_marker(marker_id):
    try:
        conn = get_db()
        c = conn.cursor()
        c.execute('UPDATE map_markers SET clear_votes = COALESCE(clear_votes, 0) + 1 WHERE id = ?', (marker_id,))
        conn.commit()
        c.execute('SELECT clear_votes FROM map_markers WHERE id = ?', (marker_id,))
        row = c.fetchone()
        votes = row['clear_votes'] if row else 1
        if votes >= 2:
            # 2 independent pilots confirmed road is clear -> remove marker!
            c.execute('DELETE FROM map_markers WHERE id = ?', (marker_id,))
            conn.commit()
            conn.close()
            return {"deleted": True, "clear_votes": votes}
        conn.close()
        return {"deleted": False, "clear_votes": votes}
    except Exception as e:
        print("vote_clear_map_marker error:", e)
        return None

def update_user_profile(user_id, data):
    try:
        conn = get_db()
        c = conn.cursor()
        fields = []
        params = []
        for k in ['callsign', 'name', 'city', 'avatar', 'bio', 'telegram_handle', 'vk_url']:
            if k in data:
                fields.append(f"{k} = ?")
                params.append(data[k])
        if not fields:
            conn.close()
            return None
        params.append(user_id)
        sql = f"UPDATE users SET {', '.join(fields)} WHERE id = ?"
        c.execute(sql, params)
        conn.commit()

        c.execute('''
            SELECT u.*, t.name as team_name, t.tag as team_tag
            FROM users u
            LEFT JOIN teams t ON u.team_id = t.id
            WHERE u.id = ?
        ''', (user_id,))
        updated = dict(c.fetchone())
        conn.close()
        return updated
    except Exception as e:
        print("update_user_profile error:", e)
        return None

def get_user_profile(user_id):
    try:
        conn = get_db()
        c = conn.cursor()
        c.execute('''
            SELECT u.*, t.name as team_name, t.tag as team_tag
            FROM users u
            LEFT JOIN teams t ON u.team_id = t.id
            WHERE u.id = ?
        ''', (user_id,))
        row = c.fetchone()
        if not row:
            conn.close()
            return None
        user = dict(row)

        # Primary car
        c.execute('SELECT * FROM cars WHERE user_id = ? ORDER BY is_primary DESC, id DESC LIMIT 1', (user_id,))
        car_row = c.fetchone()
        if car_row:
            car = dict(car_row)
            if car.get('specs_json'):
                try:
                    car['specs'] = json.loads(car['specs_json'])
                except Exception:
                    car['specs'] = {}
            user['car'] = car
        else:
            user['car'] = None

        # All cars of user
        c.execute('SELECT * FROM cars WHERE user_id = ? ORDER BY is_primary DESC', (user_id,))
        user['all_cars'] = [dict(r) for r in c.fetchall()]

        # Recent battles
        c.execute('''
            SELECT b.*,
                   wc.make as winner_make, wc.model as winner_model,
                   wu.callsign as winner_callsign,
                   lc.make as loser_make, lc.model as loser_model,
                   lu.callsign as loser_callsign
            FROM battles b
            JOIN cars wc ON b.winner_car_id = wc.id
            JOIN users wu ON b.winner_id = wu.id
            LEFT JOIN cars lc ON b.loser_car_id = lc.id
            LEFT JOIN users lu ON b.loser_id = lu.id
            WHERE b.winner_id = ? OR b.loser_id = ?
            ORDER BY b.date_time DESC LIMIT 6
        ''', (user_id, user_id))
        user['recent_battles'] = [dict(r) for r in c.fetchall()]

        conn.close()
        return user
    except Exception as e:
        print("get_user_profile error:", e)
        return None

# =========================================================================
# CHAT / FORUM ENGINE FUNCTIONS
# =========================================================================

def get_chat_messages(channel='general', limit=60):
    try:
        conn = get_db()
        c = conn.cursor()
        if channel and channel != 'all':
            c.execute('''
                SELECT m.*, u.street_cred, u.city as user_city
                FROM chat_messages m
                LEFT JOIN users u ON m.user_id = u.id
                WHERE m.channel = ?
                ORDER BY m.created_at DESC, m.id DESC
                LIMIT ?
            ''', (channel, limit))
        else:
            c.execute('''
                SELECT m.*, u.street_cred, u.city as user_city
                FROM chat_messages m
                LEFT JOIN users u ON m.user_id = u.id
                ORDER BY m.created_at DESC, m.id DESC
                LIMIT ?
            ''', (limit,))
        rows = [dict(r) for r in c.fetchall()]
        rows.reverse()
        conn.close()
        return rows
    except Exception as e:
        print("get_chat_messages error:", e)
        return []

def add_chat_message(user_id, callsign, avatar, car_name, channel, message, image_url=None, media_type='image'):
    try:
        conn = get_db()
        c = conn.cursor()
        
        # Auto-detect video
        if image_url:
            low = image_url.lower()
            if any(low.endswith(x) for x in ['.mp4', '.webm', '.mov', '.m4v']) or any(x in low for x in ['youtube.com', 'youtu.be', 'rutube.ru', 'vk.com/video']):
                media_type = 'video'

        c.execute('''
            INSERT INTO chat_messages (user_id, callsign, avatar, car_name, channel, message, image_url, media_type)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, callsign, avatar, car_name, channel or 'general', message, image_url, media_type or 'image'))
        conn.commit()
        msg_id = c.lastrowid
        c.execute('SELECT * FROM chat_messages WHERE id = ?', (msg_id,))
        row = c.fetchone()
        conn.close()
        return dict(row) if row else None
    except Exception as e:
        print("add_chat_message error:", e)
        return None

def like_chat_message(message_id):
    try:
        conn = get_db()
        c = conn.cursor()
        c.execute('UPDATE chat_messages SET likes_count = COALESCE(likes_count, 0) + 1 WHERE id = ?', (message_id,))
        conn.commit()
        c.execute('SELECT likes_count FROM chat_messages WHERE id = ?', (message_id,))
        row = c.fetchone()
        conn.close()
        return row['likes_count'] if row else 0
    except Exception as e:
        print("like_chat_message error:", e)
        return 0

def delete_chat_message(message_id):
    try:
        conn = get_db()
        c = conn.cursor()
        c.execute('DELETE FROM chat_messages WHERE id = ?', (message_id,))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print("delete_chat_message error:", e)
        return False

# Auto-initialize database tables and migrations on load
init_db()

if __name__ == '__main__':
    init_db()

