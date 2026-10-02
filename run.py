"""
KubanStreetSpecial - Unified Launcher
Runs Server and Telegram Bot or allows selecting components.
"""

import subprocess
import sys
import os
import webbrowser
import time

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def main():
    print("=" * 65)
    print("🚀 ЗАПУСК СИСТЕМЫ KUBAN STREET SPECIAL (KSS)")
    print("=" * 65)
    print("1. Запустить веб-платформу (Server + UI) -> http://localhost:8080")
    print("2. Запустить Telegram Bot")
    print("3. Запустить Web-сервер + Telegram Bot")
    print("4. Запустить ВСЁ С ТУННЕЛЕМ В ИНТЕРНЕТ (Сервер + Бот + Публичный SSL туннель)")
    print("=" * 65)
    
    choice = "1"
    if len(sys.argv) > 1:
        choice = sys.argv[1]
    else:
        try:
            choice = input("Выберите режим (1, 2, 3 или 4) [По умолчанию: 1]: ").strip() or "1"
        except Exception:
            choice = "1"

    if choice == "1":
        # Launch server and open browser
        server_py = os.path.join(BASE_DIR, 'server.py')
        time.sleep(0.5)
        webbrowser.open("http://localhost:8080")
        subprocess.call([sys.executable, server_py])

    elif choice == "2":
        bot_py = os.path.join(BASE_DIR, 'bot.py')
        subprocess.call([sys.executable, bot_py])

    elif choice == "3":
        server_py = os.path.join(BASE_DIR, 'server.py')
        bot_py = os.path.join(BASE_DIR, 'bot.py')
        p_server = subprocess.Popen([sys.executable, server_py])
        time.sleep(1)
        webbrowser.open("http://localhost:8080")
        p_bot = subprocess.Popen([sys.executable, bot_py])
        try:
            p_server.wait()
            p_bot.wait()
        except KeyboardInterrupt:
            p_server.terminate()
            p_bot.terminate()

    elif choice == "4":
        server_py = os.path.join(BASE_DIR, 'server.py')
        bot_py = os.path.join(BASE_DIR, 'bot.py')
        p_server = subprocess.Popen([sys.executable, server_py])
        time.sleep(1)
        webbrowser.open("http://localhost:8080")
        p_bot = subprocess.Popen([sys.executable, bot_py])
        
        # Start Smart Tunnel Manager
        tunnel_py = os.path.join(BASE_DIR, 'tunnel_manager.py')
        p_tunnel = subprocess.Popen([sys.executable, tunnel_py])
        try:
            p_server.wait()
            p_bot.wait()
            p_tunnel.wait()
        except KeyboardInterrupt:
            p_server.terminate()
            p_bot.terminate()
            p_tunnel.terminate()

if __name__ == '__main__':
    main()
