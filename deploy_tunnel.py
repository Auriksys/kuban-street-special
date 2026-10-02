import subprocess
import time
import os
import sys
import re
import urllib.request
import webbrowser

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def check_server():
    try:
        r = urllib.request.urlopen("http://localhost:8080/api/stats", timeout=2)
        return r.getcode() == 200
    except Exception:
        return False

print("=" * 65)
print("  🚀 KUBAN STREET SPECIAL (KSS) — АВТОМАТИЧЕСКИЙ ВЫХОД В СЕТЬ")
print("=" * 65)

# 1. Запуск сервера
if not check_server():
    print("[1/2] Запускаем веб-сервер KSS...")
    server_proc = subprocess.Popen(
        [sys.executable, os.path.join(BASE_DIR, "server.py")],
        cwd=BASE_DIR
    )
    for _ in range(10):
        time.sleep(1)
        if check_server():
            break
    print("✅ Локальный сервер успешно запущен на порту 8080!")
else:
    print("✅ Сервер KSS уже активен на http://localhost:8080")

# 2. Запуск туннеля (Pinggy / Localhost.run)
print("[2/2] Подключаем защищенный публичный интернет-туннель...")

def try_tunnel(cmd, pattern):
    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        for _ in range(25):
            line = proc.stdout.readline()
            if not line:
                time.sleep(0.5)
                continue
            print("  > " + line.strip())
            match = re.search(pattern, line)
            if match:
                return proc, match.group(0).strip()
    except Exception as e:
        print(f"Ошибка при попытке: {e}")
    return None, None

# Попытка 1: Pinggy (мгновенный и стабильный)
proc, public_url = try_tunnel(
    ["ssh", "-p", "443", "-R0:localhost:8080", "-o", "StrictHostKeyChecking=no", "-o", "ServerAliveInterval=30", "a.pinggy.io"],
    r'https://[a-zA-Z0-9.-]+\.a\.pinggy\.link'
)

# Попытка 2: Localhost.run (если pinggy занят)
if not public_url:
    print("\nПодключаем запасной шлюз localhost.run...")
    proc, public_url = try_tunnel(
        ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "ServerAliveInterval=30", "-R", "80:localhost:8080", "nokey@localhost.run"],
        r'https://[a-zA-Z0-9.-]+\.localhost\.run'
    )

if public_url:
    print("\n" + "=" * 65)
    print("🎉 ВАШ САЙТ УСПЕШНО РАБОТАЕТ В ИНТЕРНЕТЕ!")
    print(f"👉 ПУБЛИЧНЫЙ АДРЕС: {public_url}")
    print("=" * 65 + "\n")
    
    # Сохраняем ссылку на Рабочий стол
    desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
    txt_file = os.path.join(desktop_path, "ССЫЛКА_НА_САЙТ.txt")
    url_shortcut = os.path.join(desktop_path, "ОТКРЫТЬ_САЙТ_KSS.url")
    
    try:
        with open(txt_file, "w", encoding="utf-8") as f:
            f.write(f"🔥 KUBAN STREET SPECIAL (KSS) В СЕТИ ИНТЕРНЕТ:\n\n{public_url}\n\nОткрывайте с любого телефона или компьютера!\n")
        with open(url_shortcut, "w", encoding="utf-8") as f:
            f.write(f"[InternetShortcut]\nURL={public_url}\n")
        print(f"📁 Ярлык и файл с ссылкой созданы прямо на вашем Рабочем столе: {txt_file}")
    except Exception as e:
        print("Заметка:", e)

    # Открываем в браузере
    try:
        webbrowser.open(public_url)
    except Exception:
        pass

    print("\n⏳ Туннель активен. Не закрывайте это окно, пока пользуетесь сайтом в интернете!")
    if proc:
        proc.wait()
else:
    print("⚠️ Не удалось автоматически получить туннель через SSH.")
    print("Открываем локальный сайт: http://localhost:8080")
    webbrowser.open("http://localhost:8080")
