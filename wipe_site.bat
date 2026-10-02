@echo off
chcp 65001 > nul
title Kuban Street Special - Очистка Сайта
echo ========================================================
echo   🧹 ОЧИСТКА БАЗЫ ДАННЫХ KUBAN STREET SPECIAL 🧹
echo ========================================================
echo Внимание! Это удалит все машины, споты, заезды и сделает сайт пустым.
set /p confirm="Вы уверены? (y/n): "
if /i "%confirm%"=="y" (
    python clear_database.py
) else (
    echo Отменено.
)
pause
