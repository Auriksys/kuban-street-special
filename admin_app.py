"""
KubanStreetSpecial - Admin Control Panel Desktop Software
Standalone Native GUI Application for Windows (zero pip dependencies required).
Allows the Administrator to:
- Publish & delete News & Events with photos (pick file from PC or URL)
- Add & manage Spots / Tracks of Krasnodar Krai
- Manage registered Cars & Pilots (view users from Telegram and web)
- Log and verify Battles / Races
- One-click Wipe database (make site clean/empty) or restore demo data
"""

import os
import sys
import json
import shutil
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from db.database import get_db, clear_all_data, seed_data, DB_PATH

STATIC_DIR = os.path.join(BASE_DIR, 'static')
UPLOADS_DIR = os.path.join(STATIC_DIR, 'uploads')
os.makedirs(UPLOADS_DIR, exist_ok=True)

class KSSAdminApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("KUBAN STREET SPECIAL — Панель Управления Админа")
        self.geometry("980x720")
        self.minsize(850, 600)
        self.configure(bg="#0b0e17")

        # Styling
        self.setup_styles()
        self.create_header()

        # Notebook (Tabs)
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=15, pady=10)

        # Tabs
        self.tab_news = ttk.Frame(self.notebook, style="KSS.TFrame")
        self.tab_spots = ttk.Frame(self.notebook, style="KSS.TFrame")
        self.tab_cars = ttk.Frame(self.notebook, style="KSS.TFrame")
        self.tab_pilots = ttk.Frame(self.notebook, style="KSS.TFrame")
        self.tab_battles = ttk.Frame(self.notebook, style="KSS.TFrame")
        self.tab_db = ttk.Frame(self.notebook, style="KSS.TFrame")

        self.notebook.add(self.tab_news, text="📰 Новости и Анонсы")
        self.notebook.add(self.tab_spots, text="⛰️ Споты и Трассы")
        self.notebook.add(self.tab_cars, text="🏎️ Гараж и Авто")
        self.notebook.add(self.tab_pilots, text="👥 Пилоты (Пользователи)")
        self.notebook.add(self.tab_battles, text="⚔️ Заезды")
        self.notebook.add(self.tab_db, text="⚙️ Очистка и База Данных")

        # Build Tab Contents
        self.build_news_tab()
        self.build_spots_tab()
        self.build_cars_tab()
        self.build_pilots_tab()
        self.build_battles_tab()
        self.build_db_tab()

        self.refresh_all()

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")

        # Dark Theme Palette
        bg_dark = "#0b0e17"
        card_bg = "#121624"
        accent_volt = "#a3e635"
        accent_cyan = "#06b6d4"
        text_light = "#f3f4f6"

        style.configure("KSS.TFrame", background=bg_dark)
        style.configure("Card.TFrame", background=card_bg, relief="flat")
        style.configure("TLabel", background=bg_dark, foreground=text_light, font=("Segoe UI", 9))
        style.configure("Card.TLabel", background=card_bg, foreground=text_light, font=("Segoe UI", 9))
        style.configure("Title.TLabel", background=bg_dark, foreground=accent_volt, font=("Segoe UI", 12, "bold"))
        style.configure("CardTitle.TLabel", background=card_bg, foreground=accent_cyan, font=("Segoe UI", 11, "bold"))

        style.configure("TNotebook", background=bg_dark, borderwidth=0)
        style.configure("TNotebook.Tab", background="#1a2035", foreground="#9ca3af", padding=[12, 6], font=("Segoe UI", 9, "bold"))
        style.map("TNotebook.Tab", background=[("selected", "#2563eb")], foreground=[("selected", "#ffffff")])

        style.configure("Treeview", background="#111422", foreground="#e5e7eb", fieldbackground="#111422", rowheight=26, font=("Segoe UI", 9))
        style.configure("Treeview.Heading", background="#1e2438", foreground="#a3e635", font=("Segoe UI", 9, "bold"))
        style.map("Treeview", background=[("selected", "#1e3a8a")], foreground=[("selected", "#ffffff")])

    def create_header(self):
        header = tk.Frame(self, bg="#121624", height=65)
        header.pack(fill="x", side="top")

        lbl_logo = tk.Label(header, text="🔥 KUBAN STREET SPECIAL", bg="#121624", fg="#a3e635", font=("Impact", 18))
        lbl_logo.pack(side="left", padx=15, pady=10)

        lbl_sub = tk.Label(header, text="• ПАНЕЛЬ АДМИНИСТРАТОРА (93/123/23)", bg="#121624", fg="#9ca3af", font=("Segoe UI", 10, "bold"))
        lbl_sub.pack(side="left", pady=12)

        btn_open_site = tk.Button(header, text="🌐 Открыть сайт", bg="#2563eb", fg="white", font=("Segoe UI", 9, "bold"),
                                  padx=10, pady=4, relief="flat", cursor="hand2", command=self.open_site_in_browser)
        btn_open_site.pack(side="right", padx=15, pady=12)

        btn_refresh = tk.Button(header, text="🔄 Обновить всё", bg="#374151", fg="white", font=("Segoe UI", 9),
                                padx=10, pady=4, relief="flat", cursor="hand2", command=self.refresh_all)
        btn_refresh.pack(side="right", padx=5, pady=12)

    def open_site_in_browser(self):
        import webbrowser
        webbrowser.open("http://localhost:8080")

    # =========================================================
    # TAB 1: NEWS & ANNOUNCEMENTS
    # =========================================================
    def build_news_tab(self):
        paned = tk.PanedWindow(self.tab_news, orient="horizontal", bg="#0b0e17", sashwidth=4)
        paned.pack(fill="both", expand=True, padx=5, pady=5)

        # Left: Form
        form_frame = tk.Frame(paned, bg="#121624", padx=15, pady=15)
        paned.add(form_frame, minsize=380)

        tk.Label(form_frame, text="ОПУБЛИКОВАТЬ НОВОСТЬ / АНОНС", bg="#121624", fg="#a3e635", font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(0, 10))

        tk.Label(form_frame, text="Заголовок новости:", bg="#121624", fg="#d1d5db").pack(anchor="w")
        self.ent_news_title = tk.Entry(form_frame, bg="#1e2438", fg="white", insertbackground="white", relief="flat", font=("Segoe UI", 10))
        self.ent_news_title.pack(fill="x", pady=(2, 8))

        tk.Label(form_frame, text="Категория:", bg="#121624", fg="#d1d5db").pack(anchor="w")
        self.combo_news_cat = ttk.Combobox(form_frame, values=["Анонс сходки", "Дрэг-битва", "Горное Тоге", "Регламент", "Новость Края"])
        self.combo_news_cat.set("Анонс сходки")
        self.combo_news_cat.pack(fill="x", pady=(2, 8))

        tk.Label(form_frame, text="Картинка (Файл с компьютера или URL):", bg="#121624", fg="#d1d5db").pack(anchor="w")
        img_row = tk.Frame(form_frame, bg="#121624")
        img_row.pack(fill="x", pady=(2, 8))
        self.ent_news_img = tk.Entry(img_row, bg="#1e2438", fg="white", insertbackground="white", relief="flat", font=("Segoe UI", 9))
        self.ent_news_img.pack(side="left", fill="x", expand=True)
        btn_pick_img = tk.Button(img_row, text="📁 Выбрать фото", bg="#374151", fg="white", font=("Segoe UI", 8),
                                 command=lambda: self.pick_file_into_entry(self.ent_news_img))
        btn_pick_img.pack(side="right", padx=(5, 0))

        tk.Label(form_frame, text="Текст новости / Подробности:", bg="#121624", fg="#d1d5db").pack(anchor="w")
        self.txt_news_content = tk.Text(form_frame, bg="#1e2438", fg="white", insertbackground="white", relief="flat", height=7, font=("Segoe UI", 9))
        self.txt_news_content.pack(fill="both", expand=True, pady=(2, 12))

        btn_pub_news = tk.Button(form_frame, text="🚀 ОПУБЛИКОВАТЬ НА САЙТ", bg="#10b981", fg="white", font=("Segoe UI", 10, "bold"),
                                 relief="flat", pady=7, cursor="hand2", command=self.save_news)
        btn_pub_news.pack(fill="x")

        # Right: News List
        list_frame = tk.Frame(paned, bg="#121624", padx=10, pady=10)
        paned.add(list_frame, minsize=420)

        tk.Label(list_frame, text="ОПУБЛИКОВАННЫЕ НОВОСТИ В БАЗЕ", bg="#121624", fg="#06b6d4", font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(0, 5))

        self.tree_news = ttk.Treeview(list_frame, columns=("id", "title", "cat", "date"), show="headings")
        self.tree_news.heading("id", text="ID")
        self.tree_news.heading("title", text="Заголовок")
        self.tree_news.heading("cat", text="Категория")
        self.tree_news.heading("date", text="Дата")
        self.tree_news.column("id", width=35, anchor="center")
        self.tree_news.column("title", width=180)
        self.tree_news.column("cat", width=95)
        self.tree_news.column("date", width=110, anchor="center")
        self.tree_news.pack(fill="both", expand=True)

        btn_del_news = tk.Button(list_frame, text="🗑️ Удалить выбранную новость", bg="#ef4444", fg="white", font=("Segoe UI", 9, "bold"),
                                 relief="flat", pady=4, cursor="hand2", command=self.delete_selected_news)
        btn_del_news.pack(fill="x", pady=(8, 0))

    def save_news(self):
        title = self.ent_news_title.get().strip()
        cat = self.combo_news_cat.get().strip()
        img = self.ent_news_img.get().strip()
        content = self.txt_news_content.get("1.0", "end").strip()

        if not title or not content:
            messagebox.showwarning("Внимание", "Заполните заголовок и текст новости!")
            return

        conn = get_db()
        c = conn.cursor()
        c.execute('''
            INSERT INTO news (title, content, image_url, category, author)
            VALUES (?, ?, ?, ?, 'Администрация KSS')
        ''', (title, content, img, cat))
        conn.commit()
        conn.close()

        self.ent_news_title.delete(0, "end")
        self.ent_news_img.delete(0, "end")
        self.txt_news_content.delete("1.0", "end")
        messagebox.showinfo("Успех", "Новость успешно сохранена и появится на сайте!")
        self.refresh_news()

    def refresh_news(self):
        for item in self.tree_news.get_children():
            self.tree_news.delete(item)
        conn = get_db()
        c = conn.cursor()
        c.execute('SELECT id, title, category, created_at FROM news ORDER BY created_at DESC')
        for row in c.fetchall():
            self.tree_news.insert("", "end", values=(row[0], row[1], row[2], str(row[3])[:16]))
        conn.close()

    def delete_selected_news(self):
        sel = self.tree_news.selection()
        if not sel:
            messagebox.showwarning("Внимание", "Выберите новость для удаления из списка")
            return
        item_id = self.tree_news.item(sel[0])['values'][0]
        if messagebox.askyesno("Подтверждение", f"Удалить новость #{item_id}?"):
            conn = get_db()
            c = conn.cursor()
            c.execute('DELETE FROM news WHERE id = ?', (item_id,))
            conn.commit()
            conn.close()
            self.refresh_news()

    # =========================================================
    # TAB 2: SPOTS & TRACKS
    # =========================================================
    def build_spots_tab(self):
        paned = tk.PanedWindow(self.tab_spots, orient="horizontal", bg="#0b0e17", sashwidth=4)
        paned.pack(fill="both", expand=True, padx=5, pady=5)

        form_frame = tk.Frame(paned, bg="#121624", padx=15, pady=10)
        paned.add(form_frame, minsize=380)

        tk.Label(form_frame, text="ДОБАВИТЬ СПОТ / ЛОКАЦИЮ", bg="#121624", fg="#a3e635", font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(0, 6))

        tk.Label(form_frame, text="Название спота (напр. OZ Mall, Семь Ветров):", bg="#121624", fg="#d1d5db").pack(anchor="w")
        self.ent_spot_name = tk.Entry(form_frame, bg="#1e2438", fg="white", relief="flat")
        self.ent_spot_name.pack(fill="x", pady=(2, 6))

        row1 = tk.Frame(form_frame, bg="#121624")
        row1.pack(fill="x", pady=(0, 6))
        col1 = tk.Frame(row1, bg="#121624")
        col1.pack(side="left", fill="x", expand=True, padx=(0, 5))
        tk.Label(col1, text="Город:", bg="#121624", fg="#d1d5db").pack(anchor="w")
        self.ent_spot_city = tk.Entry(col1, bg="#1e2438", fg="white", relief="flat")
        self.ent_spot_city.insert(0, "Краснодар")
        self.ent_spot_city.pack(fill="x", pady=2)

        col2 = tk.Frame(row1, bg="#121624")
        col2.pack(side="right", fill="x", expand=True, padx=(5, 0))
        tk.Label(col2, text="Дисциплина:", bg="#121624", fg="#d1d5db").pack(anchor="w")
        self.combo_spot_type = ttk.Combobox(col2, values=["Дрэг", "Тоге", "Дрифт", "Ролл-он"])
        self.combo_spot_type.set("Дрэг")
        self.combo_spot_type.pack(fill="x", pady=2)

        row2 = tk.Frame(form_frame, bg="#121624")
        row2.pack(fill="x", pady=(0, 6))
        col3 = tk.Frame(row2, bg="#121624")
        col3.pack(side="left", fill="x", expand=True, padx=(0, 5))
        tk.Label(col3, text="Широта (Lat):", bg="#121624", fg="#d1d5db").pack(anchor="w")
        self.ent_spot_lat = tk.Entry(col3, bg="#1e2438", fg="white", relief="flat")
        self.ent_spot_lat.insert(0, "45.0118")
        self.ent_spot_lat.pack(fill="x", pady=2)

        col4 = tk.Frame(row2, bg="#121624")
        col4.pack(side="right", fill="x", expand=True, padx=(5, 0))
        tk.Label(col4, text="Долгота (Lng):", bg="#121624", fg="#d1d5db").pack(anchor="w")
        self.ent_spot_lng = tk.Entry(col4, bg="#1e2438", fg="white", relief="flat")
        self.ent_spot_lng.insert(0, "39.1245")
        self.ent_spot_lng.pack(fill="x", pady=2)

        tk.Label(form_frame, text="Фото спота (Файл или ссылка):", bg="#121624", fg="#d1d5db").pack(anchor="w")
        simg_row = tk.Frame(form_frame, bg="#121624")
        simg_row.pack(fill="x", pady=(2, 6))
        self.ent_spot_img = tk.Entry(simg_row, bg="#1e2438", fg="white", relief="flat")
        self.ent_spot_img.pack(side="left", fill="x", expand=True)
        btn_pick_simg = tk.Button(simg_row, text="📁 Фото", bg="#374151", fg="white", font=("Segoe UI", 8),
                                  command=lambda: self.pick_file_into_entry(self.ent_spot_img))
        btn_pick_simg.pack(side="right", padx=(5, 0))

        tk.Label(form_frame, text="Описание спота и время заездов:", bg="#121624", fg="#d1d5db").pack(anchor="w")
        self.txt_spot_desc = tk.Text(form_frame, bg="#1e2438", fg="white", relief="flat", height=4)
        self.txt_spot_desc.insert("1.0", "Широкая прямая, сборы каждую пятницу и субботу после 23:00.")
        self.txt_spot_desc.pack(fill="both", expand=True, pady=(2, 8))

        btn_save_spot = tk.Button(form_frame, text="📍 ДОБАВИТЬ СПОТ НА КАРТУ", bg="#10b981", fg="white", font=("Segoe UI", 9, "bold"),
                                  relief="flat", pady=6, cursor="hand2", command=self.save_spot)
        btn_save_spot.pack(fill="x")

        # Right: Spots List
        list_frame = tk.Frame(paned, bg="#121624", padx=10, pady=10)
        paned.add(list_frame, minsize=420)

        tk.Label(list_frame, text="СПОТЫ В БАЗЕ КУБАНИ", bg="#121624", fg="#06b6d4", font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(0, 5))

        self.tree_spots = ttk.Treeview(list_frame, columns=("id", "name", "city", "type"), show="headings")
        self.tree_spots.heading("id", text="ID")
        self.tree_spots.heading("name", text="Название")
        self.tree_spots.heading("city", text="Город")
        self.tree_spots.heading("type", text="Тип")
        self.tree_spots.column("id", width=35, anchor="center")
        self.tree_spots.column("name", width=180)
        self.tree_spots.column("city", width=100)
        self.tree_spots.column("type", width=80, anchor="center")
        self.tree_spots.pack(fill="both", expand=True)

        btn_del_spot = tk.Button(list_frame, text="🗑️ Удалить выбранный спот", bg="#ef4444", fg="white", font=("Segoe UI", 9, "bold"),
                                 relief="flat", pady=4, cursor="hand2", command=self.delete_selected_spot)
        btn_del_spot.pack(fill="x", pady=(8, 0))

    def save_spot(self):
        name = self.ent_spot_name.get().strip()
        city = self.ent_spot_city.get().strip()
        stype = self.combo_spot_type.get().strip()
        lat = float(self.ent_spot_lat.get().strip() or 45.0)
        lng = float(self.ent_spot_lng.get().strip() or 39.0)
        img = self.ent_spot_img.get().strip() or "https://images.unsplash.com/photo-1568605117036-5fe5e7bab0b7?w=800"
        desc = self.txt_spot_desc.get("1.0", "end").strip()
        slug = name.lower().replace(' ', '-').replace('/', '-')

        if not name:
            messagebox.showwarning("Внимание", "Укажите название спота!")
            return

        conn = get_db()
        c = conn.cursor()
        c.execute('''
            INSERT INTO spots (name, slug, city, type, lat, lng, image_url, description)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (name, slug, city, stype, lat, lng, img, desc))
        conn.commit()
        conn.close()

        self.ent_spot_name.delete(0, "end")
        messagebox.showinfo("Успех", f"Спот '{name}' успешно добавлен на карту!")
        self.refresh_spots()

    def refresh_spots(self):
        for item in self.tree_spots.get_children():
            self.tree_spots.delete(item)
        conn = get_db()
        c = conn.cursor()
        c.execute('SELECT id, name, city, type FROM spots ORDER BY id DESC')
        for row in c.fetchall():
            self.tree_spots.insert("", "end", values=(row[0], row[1], row[2], row[3]))
        conn.close()

    def delete_selected_spot(self):
        sel = self.tree_spots.selection()
        if not sel:
            messagebox.showwarning("Внимание", "Выберите спот для удаления")
            return
        item_id = self.tree_spots.item(sel[0])['values'][0]
        if messagebox.askyesno("Подтверждение", f"Удалить спот #{item_id}?"):
            conn = get_db()
            c = conn.cursor()
            c.execute('DELETE FROM spots WHERE id = ?', (item_id,))
            conn.commit()
            conn.close()
            self.refresh_spots()

    # =========================================================
    # TAB 3: CARS & GARAGE
    # =========================================================
    def build_cars_tab(self):
        main_frame = tk.Frame(self.tab_cars, bg="#0b0e17", padx=10, pady=10)
        main_frame.pack(fill="both", expand=True)

        top_row = tk.Frame(main_frame, bg="#0b0e17")
        top_row.pack(fill="x", pady=(0, 8))
        tk.Label(top_row, text="РЕЕСТР БОЕВЫХ АВТО КУБАНИ В БАЗЕ", bg="#0b0e17", fg="#a3e635", font=("Segoe UI", 12, "bold")).pack(side="left")

        self.tree_cars = ttk.Treeview(main_frame, columns=("id", "pilot", "make", "model", "hp", "drive", "time"), show="headings")
        self.tree_cars.heading("id", text="ID")
        self.tree_cars.heading("pilot", text="Владелец / Пилот")
        self.tree_cars.heading("make", text="Марка")
        self.tree_cars.heading("model", text="Модель")
        self.tree_cars.heading("hp", text="Мощность")
        self.tree_cars.heading("drive", text="Привод")
        self.tree_cars.heading("time", text="0-100")
        self.tree_cars.column("id", width=35, anchor="center")
        self.tree_cars.column("pilot", width=140)
        self.tree_cars.column("make", width=110)
        self.tree_cars.column("model", width=120)
        self.tree_cars.column("hp", width=80, anchor="center")
        self.tree_cars.column("drive", width=70, anchor="center")
        self.tree_cars.column("time", width=70, anchor="center")
        self.tree_cars.pack(fill="both", expand=True)

        btn_bar = tk.Frame(main_frame, bg="#0b0e17")
        btn_bar.pack(fill="x", pady=(8, 0))

        btn_add_car = tk.Button(btn_bar, text="➕ Добавить авто вручную", bg="#2563eb", fg="white", font=("Segoe UI", 9, "bold"),
                                relief="flat", padx=15, pady=5, cursor="hand2", command=self.popup_add_car)
        btn_add_car.pack(side="left")

        btn_del_car = tk.Button(btn_bar, text="🗑️ Удалить выбранное авто", bg="#ef4444", fg="white", font=("Segoe UI", 9, "bold"),
                                relief="flat", padx=15, pady=5, cursor="hand2", command=self.delete_selected_car)
        btn_del_car.pack(side="right")

    def refresh_cars(self):
        for item in self.tree_cars.get_children():
            self.tree_cars.delete(item)
        conn = get_db()
        c = conn.cursor()
        c.execute('''
            SELECT c.id, u.callsign, c.make, c.model, c.hp, c.drivetrain, c.zero_to_hundred
            FROM cars c
            JOIN users u ON c.user_id = u.id
            ORDER BY c.hp DESC
        ''')
        for row in c.fetchall():
            self.tree_cars.insert("", "end", values=(row[0], row[1], row[2], row[3], f"{row[4]} hp", row[5], f"{row[6]}s" if row[6] else "-"))
        conn.close()

    def popup_add_car(self):
        pop = tk.Toplevel(self)
        pop.title("Добавить боевое авто в базу")
        pop.geometry("450x550")
        pop.configure(bg="#121624")

        tk.Label(pop, text="ПАРАМЕТРЫ МАШИНЫ", bg="#121624", fg="#a3e635", font=("Segoe UI", 12, "bold")).pack(pady=10)

        # Fields: User ID, Make, Model, HP, Drivetrain, Photo
        f = tk.Frame(pop, bg="#121624", padx=20)
        f.pack(fill="both", expand=True)

        tk.Label(f, text="Позывной владельца (или создаст нового):", bg="#121624", fg="#d1d5db").pack(anchor="w")
        ent_owner = tk.Entry(f, bg="#1e2438", fg="white", relief="flat")
        ent_owner.insert(0, "Админ_Кубани")
        ent_owner.pack(fill="x", pady=2)

        tk.Label(f, text="Марка (напр. Toyota, BMW, ВАЗ):", bg="#121624", fg="#d1d5db").pack(anchor="w", pady=(6, 0))
        ent_make = tk.Entry(f, bg="#1e2438", fg="white", relief="flat")
        ent_make.pack(fill="x", pady=2)

        tk.Label(f, text="Модель (напр. Mark II, M5, 2107):", bg="#121624", fg="#d1d5db").pack(anchor="w", pady=(6, 0))
        ent_model = tk.Entry(f, bg="#1e2438", fg="white", relief="flat")
        ent_model.pack(fill="x", pady=2)

        tk.Label(f, text="Мощность (л.с.):", bg="#121624", fg="#d1d5db").pack(anchor="w", pady=(6, 0))
        ent_hp = tk.Entry(f, bg="#1e2438", fg="white", relief="flat")
        ent_hp.insert(0, "400")
        ent_hp.pack(fill="x", pady=2)

        tk.Label(f, text="Привод:", bg="#121624", fg="#d1d5db").pack(anchor="w", pady=(6, 0))
        combo_drive = ttk.Combobox(f, values=["RWD", "AWD", "FWD"])
        combo_drive.set("RWD")
        combo_drive.pack(fill="x", pady=2)

        tk.Label(f, text="Фото авто (Файл или ссылка):", bg="#121624", fg="#d1d5db").pack(anchor="w", pady=(6, 0))
        prow = tk.Frame(f, bg="#121624")
        prow.pack(fill="x", pady=2)
        ent_photo = tk.Entry(prow, bg="#1e2438", fg="white", relief="flat")
        ent_photo.pack(side="left", fill="x", expand=True)
        btn_browse = tk.Button(prow, text="📁 Фото", bg="#374151", fg="white", command=lambda: self.pick_file_into_entry(ent_photo))
        btn_browse.pack(side="right", padx=(5, 0))

        def do_save():
            owner = ent_owner.get().strip() or "Пилот_KSS"
            make = ent_make.get().strip()
            model = ent_model.get().strip()
            hp = int(ent_hp.get().strip() or 300)
            drive = combo_drive.get()
            photo = ent_photo.get().strip() or "https://images.unsplash.com/photo-1503376780353-7e6692767b70?w=800"

            if not make or not model:
                messagebox.showwarning("Внимание", "Укажите марку и модель авто!")
                return

            conn = get_db()
            c = conn.cursor()
            # Find or create user
            c.execute('SELECT id FROM users WHERE callsign = ?', (owner,))
            urow = c.fetchone()
            if urow:
                uid = urow[0]
            else:
                c.execute('''
                    INSERT INTO users (username, callsign, name, avatar, city, street_cred)
                    VALUES (?, ?, ?, ?, 'Краснодар', 1000)
                ''', (f"user_{int(datetime.now().timestamp())}", owner, owner, "https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=150"))
                uid = c.lastrowid

            c.execute('''
                INSERT INTO cars (user_id, make, model, hp, drivetrain, photo_url, aspiration, weight)
                VALUES (?, ?, ?, ?, ?, ?, 'Турбо', 1450)
            ''', (uid, make, model, hp, drive, photo))
            conn.commit()
            conn.close()

            pop.destroy()
            messagebox.showinfo("Успех", f"Автомобиль {make} {model} успешно внесен в гараж!")
            self.refresh_cars()

        tk.Button(f, text="💾 СОХРАНИТЬ В БАЗУ", bg="#10b981", fg="white", font=("Segoe UI", 10, "bold"),
                  relief="flat", pady=8, cursor="hand2", command=do_save).pack(fill="x", pady=15)

    def delete_selected_car(self):
        sel = self.tree_cars.selection()
        if not sel:
            messagebox.showwarning("Внимание", "Выберите авто для удаления")
            return
        item_id = self.tree_cars.item(sel[0])['values'][0]
        if messagebox.askyesno("Подтверждение", f"Удалить авто #{item_id}?"):
            conn = get_db()
            c = conn.cursor()
            c.execute('DELETE FROM cars WHERE id = ?', (item_id,))
            conn.commit()
            conn.close()
            self.refresh_cars()

    # =========================================================
    # TAB 4: PILOTS / USERS
    # =========================================================
    def build_pilots_tab(self):
        main_frame = tk.Frame(self.tab_pilots, bg="#0b0e17", padx=10, pady=10)
        main_frame.pack(fill="both", expand=True)

        top_row = tk.Frame(main_frame, bg="#0b0e17")
        top_row.pack(fill="x", pady=(0, 8))
        tk.Label(top_row, text="ЗАРЕГИСТРИРОВАННЫЕ ПИЛОТЫ (САЙТ И TELEGRAM БОТ)", bg="#0b0e17", fg="#a3e635", font=("Segoe UI", 12, "bold")).pack(side="left")

        self.tree_pilots = ttk.Treeview(main_frame, columns=("id", "callsign", "city", "tg", "cred", "wins"), show="headings")
        self.tree_pilots.heading("id", text="ID")
        self.tree_pilots.heading("callsign", text="Позывной")
        self.tree_pilots.heading("city", text="Город")
        self.tree_pilots.heading("tg", text="Telegram")
        self.tree_pilots.heading("cred", text="Street Cred")
        self.tree_pilots.heading("wins", text="Победы")
        self.tree_pilots.column("id", width=35, anchor="center")
        self.tree_pilots.column("callsign", width=150)
        self.tree_pilots.column("city", width=120)
        self.tree_pilots.column("tg", width=130)
        self.tree_pilots.column("cred", width=90, anchor="center")
        self.tree_pilots.column("wins", width=70, anchor="center")
        self.tree_pilots.pack(fill="both", expand=True)

        btn_bar = tk.Frame(main_frame, bg="#0b0e17")
        btn_bar.pack(fill="x", pady=(8, 0))

        btn_cred = tk.Button(btn_bar, text="⚡ Изменить Street Cred", bg="#2563eb", fg="white", font=("Segoe UI", 9, "bold"),
                             relief="flat", padx=12, pady=5, cursor="hand2", command=self.change_pilot_cred)
        btn_cred.pack(side="left")

        btn_del_pilot = tk.Button(btn_bar, text="🗑️ Удалить пилота", bg="#ef4444", fg="white", font=("Segoe UI", 9, "bold"),
                                  relief="flat", padx=12, pady=5, cursor="hand2", command=self.delete_selected_pilot)
        btn_del_pilot.pack(side="right")

    def refresh_pilots(self):
        for item in self.tree_pilots.get_children():
            self.tree_pilots.delete(item)
        conn = get_db()
        c = conn.cursor()
        c.execute('SELECT id, callsign, city, telegram_handle, street_cred, wins FROM users ORDER BY street_cred DESC')
        for row in c.fetchall():
            self.tree_pilots.insert("", "end", values=(row[0], row[1], row[2], row[3] or "-", row[4], row[5]))
        conn.close()

    def change_pilot_cred(self):
        sel = self.tree_pilots.selection()
        if not sel:
            messagebox.showwarning("Внимание", "Выберите пилота из таблицы")
            return
        uid = self.tree_pilots.item(sel[0])['values'][0]
        cur_cred = self.tree_pilots.item(sel[0])['values'][4]

        import tkinter.simpledialog as sd
        new_val = sd.askinteger("Рейтинг", f"Укажите новое количество очков Street Cred:", initialvalue=cur_cred, minvalue=0, maxvalue=99999)
        if new_val is not None:
            conn = get_db()
            c = conn.cursor()
            c.execute('UPDATE users SET street_cred = ? WHERE id = ?', (new_val, uid))
            conn.commit()
            conn.close()
            self.refresh_pilots()

    def delete_selected_pilot(self):
        sel = self.tree_pilots.selection()
        if not sel:
            messagebox.showwarning("Внимание", "Выберите пилота для удаления")
            return
        item_id = self.tree_pilots.item(sel[0])['values'][0]
        if messagebox.askyesno("Подтверждение", f"Удалить пилота #{item_id} и все его авто?"):
            conn = get_db()
            c = conn.cursor()
            c.execute('DELETE FROM users WHERE id = ?', (item_id,))
            c.execute('DELETE FROM cars WHERE user_id = ?', (item_id,))
            conn.commit()
            conn.close()
            self.refresh_pilots()
            self.refresh_cars()

    # =========================================================
    # TAB 5: BATTLES
    # =========================================================
    def build_battles_tab(self):
        main_frame = tk.Frame(self.tab_battles, bg="#0b0e17", padx=10, pady=10)
        main_frame.pack(fill="both", expand=True)

        tk.Label(main_frame, text="ЖУРНАЛ ЗАЕЗДОВ И ПОБЕД", bg="#0b0e17", fg="#a3e635", font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(0, 8))

        self.tree_battles = ttk.Treeview(main_frame, columns=("id", "disc", "spot", "win", "gap", "cred", "date"), show="headings")
        self.tree_battles.heading("id", text="ID")
        self.tree_battles.heading("disc", text="Дисциплина")
        self.tree_battles.heading("spot", text="Локация / Спот")
        self.tree_battles.heading("win", text="Победитель")
        self.tree_battles.heading("gap", text="Разрыв")
        self.tree_battles.heading("cred", text="+PTS")
        self.tree_battles.heading("date", text="Дата")
        self.tree_battles.column("id", width=35, anchor="center")
        self.tree_battles.column("disc", width=95)
        self.tree_battles.column("spot", width=140)
        self.tree_battles.column("win", width=120)
        self.tree_battles.column("gap", width=110)
        self.tree_battles.column("cred", width=60, anchor="center")
        self.tree_battles.column("date", width=110, anchor="center")
        self.tree_battles.pack(fill="both", expand=True)

        btn_del_battle = tk.Button(main_frame, text="🗑️ Удалить выбранный заезд", bg="#ef4444", fg="white", font=("Segoe UI", 9, "bold"),
                                   relief="flat", pady=5, cursor="hand2", command=self.delete_selected_battle)
        btn_del_battle.pack(fill="x", pady=(8, 0))

    def refresh_battles(self):
        for item in self.tree_battles.get_children():
            self.tree_battles.delete(item)
        conn = get_db()
        c = conn.cursor()
        c.execute('''
            SELECT b.id, b.discipline, b.spot_name, u.callsign, b.gap_description, b.cred_delta, b.date_time
            FROM battles b
            JOIN users u ON b.winner_id = u.id
            ORDER BY b.id DESC
        ''')
        for row in c.fetchall():
            self.tree_battles.insert("", "end", values=(row[0], row[1], row[2], row[3], row[4], f"+{row[5]}", str(row[6])[:16]))
        conn.close()

    def delete_selected_battle(self):
        sel = self.tree_battles.selection()
        if not sel:
            messagebox.showwarning("Внимание", "Выберите заезд для удаления")
            return
        item_id = self.tree_battles.item(sel[0])['values'][0]
        if messagebox.askyesno("Подтверждение", f"Удалить запись заезда #{item_id}?"):
            conn = get_db()
            c = conn.cursor()
            c.execute('DELETE FROM battles WHERE id = ?', (item_id,))
            conn.commit()
            conn.close()
            self.refresh_battles()

    # =========================================================
    # TAB 6: DATABASE MANAGEMENT (WIPE OR SEED)
    # =========================================================
    def build_db_tab(self):
        main_frame = tk.Frame(self.tab_db, bg="#0b0e17", padx=25, pady=25)
        main_frame.pack(fill="both", expand=True)

        tk.Label(main_frame, text="УПРАВЛЕНИЕ БАЗОЙ ДАННЫХ И САЙТОМ", bg="#0b0e17", fg="#a3e635", font=("Segoe UI", 14, "bold")).pack(anchor="w", pady=(0, 15))

        # Status Card
        card = tk.Frame(main_frame, bg="#121624", padx=20, pady=20)
        card.pack(fill="x", pady=(0, 20))
        self.lbl_stats = tk.Label(card, text="Загрузка статистики базы...", bg="#121624", fg="#ffffff", font=("Segoe UI", 11))
        self.lbl_stats.pack(anchor="w")

        # Action: Clean Database (Make Empty)
        clean_box = tk.LabelFrame(main_frame, text=" 🔴 ПОЛНАЯ ОЧИСТКА САЙТА (СДЕЛАТЬ ПУСТЫМ) ", bg="#0b0e17", fg="#ef4444", font=("Segoe UI", 11, "bold"), padx=15, pady=15)
        clean_box.pack(fill="x", pady=(0, 20))

        tk.Label(clean_box, text="Удаляет все машины, споты, заезды, пилотов и новости. Сайт становится абсолютно ЧИСТЫМ,\nи вы сможете наполнять его с нуля через эту программу или через Telegram-бота @Kuban_Streetbot.",
                 bg="#0b0e17", fg="#d1d5db", justify="left").pack(anchor="w", pady=(0, 10))

        btn_wipe = tk.Button(clean_box, text="🧹 ОЧИСТИТЬ ВСЕ ДАННЫЕ (СДЕЛАТЬ САЙТ ПУСТЫМ)", bg="#dc2626", fg="white", font=("Segoe UI", 11, "bold"),
                             padx=15, pady=8, relief="flat", cursor="hand2", command=self.wipe_database)
        btn_wipe.pack(anchor="w")

        # Action: Seed Demo Data
        seed_box = tk.LabelFrame(main_frame, text=" 🟢 ЗАГРУЗИТЬ ТЕСТОВЫЕ ДАННЫЕ КУБАНИ ", bg="#0b0e17", fg="#10b981", font=("Segoe UI", 11, "bold"), padx=15, pady=15)
        seed_box.pack(fill="x")

        tk.Label(seed_box, text="Загружает демонстрационные спортивные авто (Chaser, Supra, Golf R, ВАЗ 2107 Turbo), споты (OZ Mall, Семь Ветров, Шаумян),\nсиндикаты и журнал заездов для демонстрации возможностей сайта.",
                 bg="#0b0e17", fg="#d1d5db", justify="left").pack(anchor="w", pady=(0, 10))

        btn_seed = tk.Button(seed_box, text="📦 ЗАГРУЗИТЬ ТЕСТОВЫЕ ДАННЫЕ", bg="#059669", fg="white", font=("Segoe UI", 10, "bold"),
                             padx=15, pady=8, relief="flat", cursor="hand2", command=self.seed_demo_data)
        btn_seed.pack(anchor="w")

    def wipe_database(self):
        if messagebox.askyesno("Внимание: Очистка", "Вы уверены, что хотите полностью очистить сайт?\nВсе машины, новости, споты и заезды будут удалены. Сайт станет пустым."):
            clear_all_data()
            messagebox.showinfo("Готово", "Сайт очищен! База данных теперь полностью пустая.")
            self.refresh_all()

    def seed_demo_data(self):
        if messagebox.askyesno("Загрузка демо", "Загрузить тестовые данные Кубани (машины, споты, заезды)?"):
            clear_all_data()
            seed_data()
            messagebox.showinfo("Готово", "Тестовые данные успешно загружены в базу!")
            self.refresh_all()

    def update_db_stats(self):
        conn = get_db()
        c = conn.cursor()
        c.execute('SELECT COUNT(*) FROM cars')
        cars_c = c.fetchone()[0]
        c.execute('SELECT COUNT(*) FROM spots')
        spots_c = c.fetchone()[0]
        c.execute('SELECT COUNT(*) FROM news')
        news_c = c.fetchone()[0]
        c.execute('SELECT COUNT(*) FROM users')
        users_c = c.fetchone()[0]
        c.execute('SELECT COUNT(*) FROM battles')
        battles_c = c.fetchone()[0]
        conn.close()

        status_text = (
            f"📊 ТЕКУЩЕЕ СОСТОЯНИЕ БАЗЫ ДАННЫХ:\n"
            f"• Боевых авто в гараже: {cars_c}\n"
            f"• Спотов и перевалов: {spots_c}\n"
            f"• Новостей и анонсов: {news_c}\n"
            f"• Зарегистрированных пилотов: {users_c}\n"
            f"• Зафиксированных заездов: {battles_c}\n"
            f"📁 Файл базы: {DB_PATH}"
        )
        self.lbl_stats.config(text=status_text)

    # =========================================================
    # HELPERS
    # =========================================================
    def pick_file_into_entry(self, entry_widget):
        file_path = filedialog.askopenfilename(
            title="Выберите фотографию",
            filetypes=[("Изображения", "*.jpg *.jpeg *.png *.webp *.bmp *.gif"), ("Все файлы", "*.*")]
        )
        if file_path:
            filename = os.path.basename(file_path).replace(' ', '_')
            dest = os.path.join(UPLOADS_DIR, filename)
            try:
                shutil.copy2(file_path, dest)
                public_url = f"/uploads/{filename}"
                entry_widget.delete(0, "end")
                entry_widget.insert(0, public_url)
                messagebox.showinfo("Фото скопировано", f"Фото успешно скопировано в галерею сайта:\n{public_url}")
            except Exception as e:
                entry_widget.delete(0, "end")
                entry_widget.insert(0, file_path)

    def refresh_all(self):
        self.refresh_news()
        self.refresh_spots()
        self.refresh_cars()
        self.refresh_pilots()
        self.refresh_battles()
        self.update_db_stats()


if __name__ == '__main__':
    app = KSSAdminApp()
    app.mainloop()
