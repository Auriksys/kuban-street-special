"""
KubanStreetSpecial - Permanent Domain & Network Configuration Wizard
Allows setting a permanent subdomain, Ngrok static domain, Cloudflare tunnel token,
or custom external domain name.
"""

import os
import sys
import json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, 'network_config.json')

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def save_config(cfg):
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)
    print("✅ Настройки успешно сохранены в network_config.json!")

def main():
    cfg = load_config()

    while True:
        print("\n" + "=" * 65)
        print("  🌐 НАСТРОЙКА ПОСТОЯННОГО ДОМЕНА — KUBAN STREET SPECIAL")
        print("=" * 65)
        print(f"1. Постоянный поддомен Localtunnel:  {cfg.get('subdomain', 'kuban-street-special')}.loca.lt")
        print(f"2. Ngrok постоянный статический домен: {cfg.get('ngrok_domain', 'Не задан')}")
        print(f"3. Cloudflare Tunnel токен:            {'Задан (скрыт)' if cfg.get('cloudflare_token') else 'Не задан'}")
        print(f"4. Свой постоянный домен (VPS/IP):     {cfg.get('custom_domain', 'Не задан')}")
        print(f"5. Telegram Chat ID для уведомлений:   {cfg.get('admin_telegram_chat_id', 'Не задан')}")
        print("-----------------------------------------------------------------")
        print("[1] Изменить постоянный поддомен Localtunnel")
        print("[2] Настроить бесплатный статический домен Ngrok")
        print("[3] Ввести токен Cloudflare Zero Trust Tunnel")
        print("[4] Ввести свой постоянный домен (например, https://kuban-special.ru)")
        print("[5] Ввести свой Telegram ID для уведомлений о сбоях/подъемах")
        print("[0] Выход")
        print("=" * 65)

        choice = input("Выберите пункт меню (0-5): ").strip()

        if choice == '1':
            sub = input("Введите желаемое имя поддомена (например, kuban-special): ").strip().lower()
            if sub:
                cfg['subdomain'] = sub
                save_config(cfg)
                print(f"👉 Будет использоваться адрес: https://{sub}.loca.lt")

        elif choice == '2':
            token = input("Введите Ngrok Authtoken (с сайта dashboard.ngrok.com): ").strip()
            domain = input("Введите ваш бесплатный статический домен Ngrok (например, kuban.ngrok-free.app): ").strip()
            if token:
                cfg['ngrok_auth_token'] = token
            if domain:
                cfg['ngrok_domain'] = domain
            save_config(cfg)

        elif choice == '3':
            token = input("Введите Cloudflare Tunnel Token (из панели Cloudflare Zero Trust): ").strip()
            if token:
                cfg['cloudflare_token'] = token
                save_config(cfg)

        elif choice == '4':
            dom = input("Введите полный URL вашего домена (например, https://kss.myracing.ru): ").strip()
            if dom:
                if not dom.startswith('http'):
                    dom = 'https://' + dom
                cfg['custom_domain'] = dom
                save_config(cfg)

        elif choice == '5':
            cid = input("Введите ваш цифровой Telegram Chat ID (можно узнать у @userinfobot): ").strip()
            if cid:
                cfg['admin_telegram_chat_id'] = cid
                save_config(cfg)
                print("✅ Теперь Watchdog будет отправлять алерты при сбоях и перезапусках в Telegram!")

        elif choice in ['0', 'exit', 'q']:
            print("Выход из конфигуратора.")
            break
        else:
            print("Неверный выбор.")

if __name__ == '__main__':
    main()
