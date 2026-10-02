@echo off
chcp 65001 > nul
title Kuban Street Special - Запуск ВСего (Сервер + Бот + Интернет)
echo ========================================================
echo   🔥 KUBAN STREET SPECIAL — ПОЛНЫЙ ЗАПУСК С ТУННЕЛЕМ 🔥
echo ========================================================
echo 1. Запуск веб-сервера...
start "KSS Web Server" cmd /k "python server.py"
timeout /t 2 > nul
echo 2. Запуск Telegram Бота...
start "KSS Telegram Bot" cmd /k "python bot.py"
timeout /t 1 > nul
echo 3. Подключение публичного SSL-туннеля и захват адреса...
python tunnel_manager.py
pause
