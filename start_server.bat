@echo off
chcp 65001 > nul
title Kuban Street Special - Web Platform
echo ========================================================
echo   🔥 KUBAN STREET SPECIAL (KSS) — КРАСНОДАРСКИЙ КРАЙ 🔥
echo ========================================================
echo Запуск веб-сервера и базы данных SQLite...
echo Открываем http://localhost:8080 в браузере...
start http://localhost:8080
python server.py
pause
