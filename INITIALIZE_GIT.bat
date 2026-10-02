@echo off
chcp 65001 > nul
title Инициализация Git
git init
git branch -M main
git add .
git commit -m "Deploy Kuban Street Special"
echo.
echo ========================================================
echo   ✅ Локальный репозиторий успешно подготовлен!
echo ========================================================
pause
