"""
KubanStreetSpecial - Smart Tunnel Manager & Auto-Configurator
Runs SSH tunnel to localhost.run, automatically detects the assigned public URL,
updates bot_config.json, updates kss_status.json, copies URL to clipboard,
and opens the site in the browser.
"""

import os
import sys
import re
import json
import time
import subprocess
import webbrowser

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, 'bot_config.json')
STATUS_PATH = os.path.join(BASE_DIR, 'kss_status.json')

def update_config(url):
    try:
        cfg = {}
        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                cfg = json.load(f)
        cfg['webapp_url'] = url
        with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
        print(f"[TUNNEL] ✅ bot_config.json обновлен: webapp_url = {url}")
    except Exception as e:
        print(f"[TUNNEL] ⚠️ Ошибка обновления bot_config.json: {e}")

def update_status(url):
    try:
        status_data = {}
        if os.path.exists(STATUS_PATH):
            with open(STATUS_PATH, 'r', encoding='utf-8') as f:
                status_data = json.load(f)
        status_data['status'] = 'online'
        status_data['server_online'] = True
        status_data['tunnel_online'] = True
        status_data['public_url'] = url
        status_data['last_check'] = time.strftime('%Y-%m-%d %H:%M:%S')
        with open(STATUS_PATH, 'w', encoding='utf-8') as f:
            json.dump(status_data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        pass

def copy_to_clipboard(text):
    try:
        p = subprocess.Popen('clip', stdin=subprocess.PIPE, shell=True)
        p.communicate(text.encode('utf-8'))
        print(f"[TUNNEL] 📋 Адрес скопирован в буфер обмена!")
    except Exception:
        pass

def run_tunnel():
    print("=" * 65)
    print("🌐 KUBAN STREET SPECIAL — SMART TUNNEL MANAGER")
    print("=" * 65)
    print("Подключение к публичному защищенному шлюзу localhost.run...")
    
    cmd = [
        "ssh",
        "-R", "80:localhost:8080",
        "-o", "StrictHostKeyChecking=no",
        "-o", "ServerAliveInterval=30",
        "-o", "ServerAliveCountMax=3",
        "localhost.run"
    ]
    
    while True:
        try:
            print("\n[TUNNEL] 🔄 Запуск SSH-сессии...")
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding='utf-8',
                errors='replace',
                bufsize=1
            )
            
            detected_url = None
            
            for line in iter(process.stdout.readline, ''):
                clean_line = line.strip()
                if clean_line:
                    print(f"  > {clean_line}")
                
                # Check for URLs like https://xxxx.lhr.life or http://xxxx.lhr.life
                matches = re.findall(r'https://[a-zA-Z0-9.-]+\.lhr\.life', clean_line)
                if not matches:
                    matches = re.findall(r'https://[a-zA-Z0-9.-]+\.localhost\.run', clean_line)
                    # Filter out admin.localhost.run
                    matches = [m for m in matches if 'admin.localhost.run' not in m]

                if matches and not detected_url:
                    detected_url = matches[0]
                    print("\n" + "=" * 65)
                    print("🔥 УСПЕХ! ВАШ САЙТ KUBAN STREET SPECIAL ОПУБЛИКОВАН В ИНТЕРНЕТЕ!")
                    print(f"👉 ПРЯМАЯ ССЫЛКА: {detected_url}")
                    print("=" * 65)
                    
                    update_config(detected_url)
                    update_status(detected_url)
                    copy_to_clipboard(detected_url)
                    
                    try:
                        webbrowser.open(detected_url)
                    except Exception:
                        pass
            
            process.wait()
            print("[TUNNEL] ⚠️ Туннель разорван, авто-переподключение через 3 секунды...")
            time.sleep(3)
            
        except KeyboardInterrupt:
            print("\n[TUNNEL] Остановка пользователем.")
            break
        except Exception as e:
            print(f"[TUNNEL] Ошибка: {e}. Переподключение через 5 секунд...")
            time.sleep(5)

if __name__ == '__main__':
    run_tunnel()
