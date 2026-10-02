@echo off
chcp 65001 > nul
title KSS - Публичный доступ в Интернет
echo ========================================================
echo   🌐 KUBAN STREET SPECIAL — ВЫХОД В ИНТЕРНЕТ
echo ========================================================
echo.
echo Этот скрипт бесплатно создает публичную ссылку HTTPS для вашего сайта.
echo Ссылку можно скинуть друзьям или открыть на любом смартфоне!
echo.
echo Сервер KSS должен быть запущен на порту 8080 (start_server.bat).
echo.
echo --------------------------------------------------------
echo Выберите сервис для публичного туннеля:
echo [1] Localhost.run (Работает сразу через встроенный Windows SSH)
echo [2] Pinggy.io (Альтернативный быстрый туннель)
echo --------------------------------------------------------
set /p choice="Ваш выбор (1 или 2, Enter = 1): "

if "%choice%"=="2" (
    echo.
    echo Подключаем Pinggy.io... Ссылка появится ниже:
    ssh -p 443 -R0:localhost:8080 -o StrictHostKeyChecking=no -o ServerAliveInterval=30 a.pinggy.io
) else (
    echo.
    echo Подключаем Localhost.run... Ссылка появится ниже:
    ssh -o StrictHostKeyChecking=no -o ServerAliveInterval=30 -R 80:localhost:8080 nokey@localhost.run
)

pause
