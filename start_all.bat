@echo off
chcp 65001 > nul
title Kuban Street Special - Стартер Системы
echo ========================================================
echo   🔥 KUBAN STREET SPECIAL (KSS) — КРАСНОДАРСКИЙ КРАЙ 🔥
echo ========================================================
echo 1. Запустить ВСЁ (Веб-сервер + Telegram-бот + Программа Админа)
echo 2. Запустить только Веб-сервер (http://localhost:8080)
echo 3. Запустить только Telegram-бота (@Kuban_Streetbot)
echo 4. Запустить только Программу Админа (admin_app.py)
echo ========================================================
set /p choice="Выберите вариант (1-4, Enter = 1): "

if "%choice%"=="2" goto server
if "%choice%"=="3" goto bot
if "%choice%"=="4" goto admin

:all
start "KSS Web Server" cmd /c "start_server.bat"
timeout /t 2 > nul
start "KSS Telegram Bot" cmd /c "start_bot.bat"
start "KSS Admin Panel" cmd /c "start_admin.bat"
exit

:server
call start_server.bat
exit

:bot
call start_bot.bat
exit

:admin
call start_admin.bat
exit
