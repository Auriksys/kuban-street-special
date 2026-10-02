"""
KubanStreetSpecial - High-Reliability Watchdog & Auto-Healing Engine (24/7 Monitor)
Continuous health monitoring, automatic recovery, permanent domain management,
and zero-friction resilience for the KSS platform.
"""

import os
import sys
import time
import json
import re
import socket
import threading
import subprocess
import urllib.request
import urllib.parse
from datetime import datetime, timedelta

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, 'network_config.json')
STATUS_FILE = os.path.join(BASE_DIR, 'kss_status.json')
BOT_CONFIG_FILE = os.path.join(BASE_DIR, 'bot_config.json')

DEFAULT_CONFIG = {
    "subdomain": "kuban-street-special",
    "preferred_tunnel": "auto",  # 'auto', 'localtunnel', 'cloudflared', 'ngrok', 'pinggy', 'localhost.run'
    "local_port": 8080,
    "check_interval_seconds": 5,
    "remote_check_interval_seconds": 12,
    "auto_restart_server": True,
    "auto_restart_tunnel": True,
    "telegram_alerts": True,
    "admin_telegram_chat_id": "",
    "custom_domain": "",
    "ngrok_auth_token": "",
    "ngrok_domain": "",
    "cloudflare_token": "",
    "pinggy_token": ""
}

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                cfg = dict(DEFAULT_CONFIG)
                cfg.update(data)
                return cfg
        except Exception:
            pass
    return dict(DEFAULT_CONFIG)

def save_config(cfg):
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[Watchdog] Не удалось сохранить конфигурацию: {e}")

class KSSWatchdog:
    def __init__(self):
        self.cfg = load_config()
        self.port = self.cfg.get('local_port', 8080)
        self.server_proc = None
        self.tunnel_proc = None
        
        self.server_online = False
        self.tunnel_online = False
        self.public_url = self.cfg.get('custom_domain', '')
        self.tunnel_type = "Не запущен"
        
        self.start_time = datetime.now()
        self.checks_total = 0
        self.recoveries_count = 0
        self.local_latency_ms = 0
        self.remote_latency_ms = 0
        self.last_check_time = None
        self.last_incident = "Сбоев не зафиксировано"
        self.consecutive_local_fails = 0
        self.consecutive_remote_fails = 0
        
        self.logs = []
        self.running = True
        self.lock = threading.Lock()

    def log(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        entry = f"[{timestamp}] [{level}] {message}"
        with self.lock:
            self.logs.append(entry)
            if len(self.logs) > 30:
                self.logs.pop(0)
        print(entry)

    def write_status_file(self):
        uptime_delta = datetime.now() - self.start_time
        total_seconds = int(uptime_delta.total_seconds())
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        uptime_human = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

        status_data = {
            "status": "online" if (self.server_online and self.tunnel_online) else ("degraded" if self.server_online else "offline"),
            "server_online": self.server_online,
            "tunnel_online": self.tunnel_online,
            "tunnel_type": self.tunnel_type,
            "public_url": self.public_url,
            "local_url": f"http://localhost:{self.port}",
            "uptime_seconds": total_seconds,
            "uptime_human": uptime_human,
            "latency_ms": self.local_latency_ms,
            "remote_latency_ms": self.remote_latency_ms,
            "checks_total": self.checks_total,
            "recoveries_count": self.recoveries_count,
            "last_check": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "last_incident": self.last_incident,
            "recent_logs": self.logs[-5:]
        }
        try:
            with open(STATUS_FILE, 'w', encoding='utf-8') as f:
                json.dump(status_data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def send_telegram_alert(self, text):
        if not self.cfg.get('telegram_alerts'):
            return
        
        # Read bot token from bot_config.json
        token = None
        if os.path.exists(BOT_CONFIG_FILE):
            try:
                with open(BOT_CONFIG_FILE, 'r', encoding='utf-8') as f:
                    bcfg = json.load(f)
                    token = bcfg.get('bot_token')
            except Exception:
                pass
        
        chat_id = self.cfg.get('admin_telegram_chat_id')
        if not token or not chat_id:
            return

        def _send():
            try:
                url = f"https://api.telegram.org/bot{token}/sendMessage"
                payload = json.dumps({'chat_id': chat_id, 'text': text, 'parse_mode': 'HTML'}).encode('utf-8')
                req = urllib.request.Request(url, data=payload, headers={'Content-Type': 'application/json'})
                with urllib.request.urlopen(req, timeout=8):
                    pass
            except Exception:
                pass

        threading.Thread(target=_send, daemon=True).start()

    def update_desktop_shortcuts(self, url):
        desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
        txt_path = os.path.join(desktop_path, "ССЫЛКА_НА_САЙТ.txt")
        url_path = os.path.join(desktop_path, "ОТКРЫТЬ_САЙТ_KSS.url")
        
        content = (
            "==========================================================\n"
            "   🏁 KUBAN STREET SPECIAL (KSS) — САЙТ В СЕТИ ИНТЕРНЕТ   \n"
            "==========================================================\n\n"
            f"👉 ТЕКУЩИЙ ПУБЛИЧНЫЙ АДРЕС:\n{url}\n\n"
            "✅ Сайт активен и находится под круглосуточным мониторингом Watchdog!\n"
            "📱 Ссылку можно открывать на смартфонах (iOS / Android) или с ПК.\n"
            f"🕒 Обновлено: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        )
        try:
            with open(txt_path, 'w', encoding='utf-8') as f:
                f.write(content)
        except Exception as e:
            self.log(f"Не удалось обновить {txt_path}: {e}", "WARN")

        try:
            with open(url_path, 'w', encoding='utf-8') as f:
                f.write(f"[InternetShortcut]\nURL={url}\nIconIndex=0\n")
        except Exception:
            pass

        # Update bot_config.json WebApp URL
        if os.path.exists(BOT_CONFIG_FILE):
            try:
                with open(BOT_CONFIG_FILE, 'r', encoding='utf-8') as f:
                    bcfg = json.load(f)
                bcfg['webapp_url'] = url
                with open(BOT_CONFIG_FILE, 'w', encoding='utf-8') as f:
                    json.dump(bcfg, f, ensure_ascii=False, indent=2)
                self.log(f"WebApp URL в Telegram-боте синхронизирован: {url}")
            except Exception as e:
                self.log(f"Ошибка синхронизации bot_config.json: {e}", "WARN")

    # =========================================================================
    # LOCAL SERVER SUPERVISOR
    # =========================================================================

    def check_local_health(self):
        start = time.time()
        url = f"http://127.0.0.1:{self.port}/api/health"
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'KSS-Watchdog/2.0'})
            with urllib.request.urlopen(req, timeout=3.5) as resp:
                if resp.getcode() == 200:
                    data = json.loads(resp.read().decode('utf-8'))
                    self.local_latency_ms = round((time.time() - start) * 1000)
                    return True, data
        except Exception:
            pass
        return False, None

    def start_local_server(self):
        self.log(f"Запуск локального сервера KSS на порту {self.port}...")
        server_script = os.path.join(BASE_DIR, 'server.py')
        
        # Launch server subprocess
        try:
            self.server_proc = subprocess.Popen(
                [sys.executable, server_script],
                cwd=BASE_DIR,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            # Wait up to 10 seconds for healthy status
            for _ in range(20):
                time.sleep(0.5)
                healthy, _ = self.check_local_health()
                if healthy:
                    self.server_online = True
                    self.log(f"✅ Локальный сервер успешно запущен (PID {self.server_proc.pid}, отклик {self.local_latency_ms} ms)")
                    return True
        except Exception as e:
            self.log(f"Критическая ошибка запуска server.py: {e}", "ERROR")
        return False

    def restart_local_server(self, reason="Не отвечает на запросы"):
        self.recoveries_count += 1
        self.last_incident = f"Перезапуск сервера: {reason} ({datetime.now().strftime('%H:%M:%S')})"
        self.log(f"⚠️ АВАРИЙНЫЙ ПЕРЕЗАПУСК СЕРВЕРА: {reason}", "WARN")
        self.send_telegram_alert(f"⚠️ <b>Внимание:</b> Перезапуск сервера KSS: <i>{reason}</i>")
        
        if self.server_proc:
            try:
                self.server_proc.terminate()
                self.server_proc.wait(timeout=3)
            except Exception:
                try:
                    self.server_proc.kill()
                except Exception:
                    pass

        time.sleep(1)
        self.start_local_server()

    # =========================================================================
    # TUNNEL / PERMANENT DOMAIN MANAGER
    # =========================================================================

    def check_remote_health(self):
        if not self.public_url:
            return False
        
        start = time.time()
        test_url = f"{self.public_url.rstrip('/')}/api/health"
        try:
            req = urllib.request.Request(test_url, headers={'User-Agent': 'KSS-Watchdog/2.0'})
            with urllib.request.urlopen(req, timeout=7.0) as resp:
                if resp.getcode() == 200:
                    self.remote_latency_ms = round((time.time() - start) * 1000)
                    return True
        except Exception:
            pass
        return False

    def is_tool_available(self, name):
        try:
            subprocess.run([name, "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=2)
            return True
        except Exception:
            return False

    def start_tunnel(self):
        subdomain = self.cfg.get('subdomain', 'kuban-street-special')
        preferred = self.cfg.get('preferred_tunnel', 'auto').lower()

        # 1. Custom Domain if user explicitly hosts it
        if self.cfg.get('custom_domain'):
            self.public_url = self.cfg.get('custom_domain')
            self.tunnel_type = "Постоянный внешний домен"
            self.tunnel_online = True
            self.log(f"Используется указанный постоянный домен: {self.public_url}")
            return True

        # 2. Cloudflare Named Tunnel (if token provided)
        cf_token = self.cfg.get('cloudflare_token')
        if cf_token and self.is_tool_available('cloudflared'):
            self.log("Запуск постоянного Cloudflare Zero Trust туннеля...")
            try:
                self.tunnel_proc = subprocess.Popen(
                    ["cloudflared", "tunnel", "run", "--token", cf_token],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                self.tunnel_type = "Cloudflare Permanent Tunnel"
                self.tunnel_online = True
                return True
            except Exception as e:
                self.log(f"Ошибка cloudflared: {e}", "WARN")

        # 3. Ngrok with Static Domain (if configured)
        ngrok_token = self.cfg.get('ngrok_auth_token')
        ngrok_dom = self.cfg.get('ngrok_domain')
        if ngrok_token and self.is_tool_available('ngrok'):
            try:
                subprocess.run(["ngrok", "config", "add-authtoken", ngrok_token], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5)
                cmd = ["ngrok", "http", str(self.port)]
                if ngrok_dom:
                    cmd.extend(["--domain", ngrok_dom])
                self.tunnel_proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                self.tunnel_type = f"Ngrok ({ngrok_dom or 'Dynamic'})"
                if ngrok_dom:
                    self.public_url = f"https://{ngrok_dom}"
                    self.tunnel_online = True
                    self.update_desktop_shortcuts(self.public_url)
                    return True
            except Exception as e:
                self.log(f"Ошибка ngrok: {e}", "WARN")

        # 4. Localtunnel with Permanent Subdomain (npx localtunnel)
        if preferred in ['auto', 'localtunnel'] and self.is_tool_available('npx'):
            self.log(f"Запуск постоянного туннеля Localtunnel (https://{subdomain}.loca.lt)...")
            try:
                self.tunnel_proc = subprocess.Popen(
                    ["npx", "localtunnel", "--port", str(self.port), "--subdomain", subdomain],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1
                )
                # Read initial lines for URL
                for _ in range(25):
                    line = self.tunnel_proc.stdout.readline()
                    if "your url is:" in line.lower():
                        match = re.search(r'https://[a-zA-Z0-9.-]+\.loca\.lt', line)
                        if match:
                            self.public_url = match.group(0)
                            self.tunnel_type = "Localtunnel (Постоянный домен)"
                            self.tunnel_online = True
                            self.log(f"✅ Постоянный домен Localtunnel подключен: {self.public_url}")
                            self.update_desktop_shortcuts(self.public_url)
                            return True
                    time.sleep(0.4)
            except Exception as e:
                self.log(f"Localtunnel не ответил: {e}", "INFO")

        # 5. High-Reliability SSH Tunnel: Pinggy with Keep-Alive
        self.log("Подключение защищенного туннеля высокой доступности (SSH Pinggy Keep-Alive)...")
        pinggy_cmd = [
            "ssh", "-p", "443",
            f"-R0:localhost:{self.port}",
            "-o", "StrictHostKeyChecking=no",
            "-o", "ServerAliveInterval=10",
            "-o", "ServerAliveCountMax=3",
            "-o", "ExitOnForwardFailure=yes",
            "-o", "TCPKeepAlive=yes",
            "a.pinggy.io"
        ]
        
        try:
            self.tunnel_proc = subprocess.Popen(
                pinggy_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            
            for _ in range(30):
                line = self.tunnel_proc.stdout.readline()
                if not line:
                    time.sleep(0.3)
                    continue
                match = re.search(r'https://[a-zA-Z0-9.-]+\.a\.pinggy\.link', line)
                if match:
                    self.public_url = match.group(0).strip()
                    self.tunnel_type = "Pinggy Secure SSL (Keep-Alive)"
                    self.tunnel_online = True
                    self.log(f"✅ Публичный адрес успешно получен: {self.public_url}")
                    self.update_desktop_shortcuts(self.public_url)
                    return True
                time.sleep(0.2)
        except Exception as e:
            self.log(f"Ошибка Pinggy SSH: {e}", "WARN")

        # 6. Fallback: Localhost.run
        self.log("Резервный шлюз: Localhost.run...")
        lh_cmd = [
            "ssh",
            "-o", "StrictHostKeyChecking=no",
            "-o", "ServerAliveInterval=10",
            "-o", "ServerAliveCountMax=3",
            "-o", "ExitOnForwardFailure=yes",
            "-R", f"80:localhost:{self.port}",
            "nokey@localhost.run"
        ]
        try:
            self.tunnel_proc = subprocess.Popen(
                lh_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            for _ in range(30):
                line = self.tunnel_proc.stdout.readline()
                if not line:
                    time.sleep(0.3)
                    continue
                match = re.search(r'https://[a-zA-Z0-9.-]+\.localhost\.run', line)
                if match:
                    self.public_url = match.group(0).strip()
                    self.tunnel_type = "Localhost.run SSL"
                    self.tunnel_online = True
                    self.log(f"✅ Резервный адрес успешно подключен: {self.public_url}")
                    self.update_desktop_shortcuts(self.public_url)
                    return True
                time.sleep(0.2)
        except Exception as e:
            self.log(f"Ошибка Localhost.run: {e}", "WARN")

        self.tunnel_online = False
        return False

    def restart_tunnel(self, reason="Потеря связи со шлюзом"):
        self.recoveries_count += 1
        self.last_incident = f"Восстановление туннеля: {reason} ({datetime.now().strftime('%H:%M:%S')})"
        self.log(f"🔄 АВТО-ВОССТАНОВЛЕНИЕ ТУННЕЛЯ: {reason}...", "WARN")
        
        if self.tunnel_proc:
            try:
                self.tunnel_proc.terminate()
                self.tunnel_proc.wait(timeout=3)
            except Exception:
                try:
                    self.tunnel_proc.kill()
                except Exception:
                    pass

        time.sleep(2)
        success = self.start_tunnel()
        if success:
            self.log(f"✅ Туннель успешно переподключен! Новый адрес: {self.public_url}")
            self.send_telegram_alert(f"✅ <b>Сайт KSS переподключен и доступен:</b>\n{self.public_url}")
        else:
            self.log("⚠️ Не удалось мгновенно переподключить туннель, следующая попытка через 10 сек.", "WARN")

    # =========================================================================
    # CORE MONITORING & VISUAL DASHBOARD
    # =========================================================================

    def render_dashboard(self):
        uptime_delta = datetime.now() - self.start_time
        total_seconds = int(uptime_delta.total_seconds())
        h, rem = divmod(total_seconds, 3600)
        m, s = divmod(rem, 60)
        uptime_str = f"{h:02d} ч {m:02d} мин {s:02d} сек"

        srv_badge = "🟢 ОНЛАЙН (ЗДОРОВ)" if self.server_online else "🔴 СБОЙ / ПЕРЕЗАПУСК"
        tun_badge = "🟢 В СЕТИ ИНТЕРНЕТ" if self.tunnel_online else "🟡 ПЕРЕПОДКЛЮЧЕНИЕ..."

        lines = [
            "\n" + "=" * 70,
            "  🛡️ KUBAN STREET SPECIAL (KSS) — СИСТЕМА МОНИТОРИНГА 24/7",
            "=" * 70,
            f"  🖥️  ЛОКАЛЬНЫЙ СЕРВЕР:      {srv_badge}  (Порт {self.port})",
            f"  🌐  ПУБЛИЧНЫЙ ДОСТУП:      {tun_badge}",
            f"  🔗  ПОСТОЯННЫЙ АДРЕС:      {self.public_url or 'Подключение...'}",
            f"  📡  ТИП СОЕДИНЕНИЯ:        {self.tunnel_type}",
            f"  ⏱️  ВРЕМЯ РАБОТЫ (UPTIME): {uptime_str}",
            f"  ⚡  ОТКЛИК (LATENCY):      Локальный: {self.local_latency_ms} ms | Внешний: {self.remote_latency_ms} ms",
            f"  📊  ПРОВЕРОК ВЫПОЛНЕНО:    {self.checks_total}  |  Авто-восстановлений: {self.recoveries_count}",
            f"  🕒  ПОСЛЕДНЯЯ ПРОВЕРКА:    {datetime.now().strftime('%H:%M:%S')} (Каждые {self.cfg.get('check_interval_seconds', 5)} сек)",
            "-" * 70,
            "  📝 ПОСЛЕДНИЕ СОБЫТИЯ СИСТЕМЫ:"
        ]
        for l in self.logs[-4:]:
            lines.append(f"     {l}")
        lines.append("=" * 70)
        lines.append("💡 Подсказка: Нажмите Ctrl+C для безопасного завершения работы.")
        print("\n".join(lines))

    def run(self):
        print("=" * 70)
        print("  🚀 ЗАПУСК ВЫСОКОНАДЕЖНОЙ СИСТЕМЫ KSS (СЕРВЕР + ТУННЕЛЬ + WATCHDOG)")
        print("=" * 70)

        # 1. Start local server
        healthy, _ = self.check_local_health()
        if not healthy:
            self.start_local_server()
        else:
            self.server_online = True
            self.log(f"Сервер KSS уже активен на http://localhost:{self.port}")

        # 2. Start public tunnel
        self.start_tunnel()

        # 3. Write initial status file
        self.write_status_file()

        # 4. Main monitoring loop
        check_interval = self.cfg.get('check_interval_seconds', 5)
        remote_interval = self.cfg.get('remote_check_interval_seconds', 12)
        last_remote_check = 0

        while self.running:
            try:
                time.sleep(check_interval)
                self.checks_total += 1
                now = time.time()

                # Step A: Local Server Check
                local_ok, _ = self.check_local_health()
                self.server_online = local_ok
                if not local_ok:
                    self.consecutive_local_fails += 1
                    self.log(f"⚠️ Локальный сервер не ответил ({self.consecutive_local_fails}/2)", "WARN")
                    if self.consecutive_local_fails >= 2:
                        self.restart_local_server("Не отвечает на GET /api/health")
                        self.consecutive_local_fails = 0
                else:
                    self.consecutive_local_fails = 0

                # Step B: Remote Tunnel Check
                if now - last_remote_check >= remote_interval:
                    last_remote_check = now
                    remote_ok = self.check_remote_health()
                    self.tunnel_online = remote_ok

                    if not remote_ok:
                        self.consecutive_remote_fails += 1
                        self.log(f"⚠️ Публичный туннель не ответил ({self.consecutive_remote_fails}/2)", "WARN")
                        if self.consecutive_remote_fails >= 2:
                            self.restart_tunnel("Внешний URL не отвечает")
                            self.consecutive_remote_fails = 0
                    else:
                        self.consecutive_remote_fails = 0

                # Step C: Update status file & visual dashboard
                self.write_status_file()
                
                # Render dashboard every 15 seconds
                if self.checks_total % 3 == 0:
                    self.render_dashboard()

            except KeyboardInterrupt:
                self.log("Получен сигнал завершения (Ctrl+C). Остановка...", "INFO")
                self.cleanup()
                break
            except Exception as e:
                self.log(f"Ошибка в цикле мониторинга: {e}", "ERROR")
                time.sleep(2)

    def cleanup(self):
        self.running = False
        print("\nОстановка дочерних процессов...")
        if self.tunnel_proc:
            try:
                self.tunnel_proc.terminate()
            except Exception:
                pass
        if self.server_proc:
            try:
                self.server_proc.terminate()
            except Exception:
                pass
        print("✅ Все службы корректно остановлены.")

if __name__ == '__main__':
    wd = KSSWatchdog()
    wd.run()
