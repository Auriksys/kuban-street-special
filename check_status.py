"""
KubanStreetSpecial - Instant Status Checker CLI
Allows checking server health, active public URL, and uptime at any moment.
"""

import os
import sys
import json
import time
import urllib.request

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATUS_FILE = os.path.join(BASE_DIR, 'kss_status.json')
CONFIG_FILE = os.path.join(BASE_DIR, 'network_config.json')

def test_endpoint(url, timeout=3):
    start = time.time()
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'KSS-Checker/1.0'})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            ms = round((time.time() - start) * 1000)
            return resp.getcode() == 200, ms, resp.read().decode('utf-8')
    except Exception as e:
        return False, 0, str(e)

def main():
    print("=" * 65)
    print("  🔍 KUBAN STREET SPECIAL (KSS) — ПРОВЕРКА СОСТОЯНИЯ")
    print("=" * 65)

    # 1. Check local server
    print("\n[1] Проверка локального сервера KSS...")
    local_ok, local_ms, local_data = test_endpoint("http://127.0.0.1:8080/api/health", timeout=2.5)
    if local_ok:
        print(f"  ✅ Сервер работает: http://localhost:8080 (Отклик: {local_ms} ms)")
    else:
        print("  🔴 Локальный сервер НЕ отвечает или остановлен!")

    # 2. Check Watchdog status file
    status_data = None
    if os.path.exists(STATUS_FILE):
        try:
            with open(STATUS_FILE, 'r', encoding='utf-8') as f:
                status_data = json.load(f)
        except Exception:
            pass

    public_url = None
    if status_data:
        public_url = status_data.get('public_url')
        print(f"\n[2] Данные системы мониторинга (Watchdog):")
        print(f"  • Статус: {status_data.get('status', 'unknown').upper()}")
        print(f"  • Время непрерывной работы: {status_data.get('uptime_human', 'Н/Д')}")
        print(f"  • Выполнено проверок: {status_data.get('checks_total', 0)}")
        print(f"  • Автоматических восстановлений: {status_data.get('recoveries_count', 0)}")
        print(f"  • Последний инцидент: {status_data.get('last_incident', 'Нет')}")
    else:
        print("\n[2] Служба мониторинга kss_watchdog.py пока не создала отчет.")

    # 3. Check public internet link
    desktop_txt = os.path.join(os.path.expanduser("~"), "Desktop", "ССЫЛКА_НА_САЙТ.txt")
    if not public_url and os.path.exists(desktop_txt):
        try:
            with open(desktop_txt, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.startswith('http'):
                        public_url = line.strip()
                        break
        except Exception:
            pass

    print(f"\n[3] Проверка доступности в глобальном Интернете...")
    if public_url:
        print(f"  Тестируем адрес: {public_url} ...")
        remote_ok, remote_ms, _ = test_endpoint(f"{public_url.rstrip('/')}/api/health", timeout=6.0)
        if remote_ok:
            print(f"  🟢 ИНТЕРНЕТ-ДОСТУП АКТИВЕН! Сайт открывается (Отклик: {remote_ms} ms)")
            print(f"  👉 ПУБЛИЧНАЯ ССЫЛКА: {public_url}")
        else:
            print(f"  🟡 Адрес {public_url} сейчас не ответил. Возможно, идет переподключение туннеля.")
    else:
        print("  ⚠️ Публичный туннель не запущен. Запустите 'ЗАПУСТИТЬ_САЙТ_В_ИНТЕРНЕТ.bat' на рабочем столе.")

    print("\n" + "=" * 65)

if __name__ == '__main__':
    main()
