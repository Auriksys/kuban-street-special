@echo off
chcp 65001 > nul
title Отправка Kuban Street Special в репозиторий Auriksys
echo ========================================================
echo   🚀 ЗАГРУЗКА В РЕПОЗИТОРИЙ GITHUB: Auriksys/kuban-street-special
echo ========================================================
where git >nul 2>nul
if %errorlevel% neq 0 (
    echo [ВНИМАНИЕ] Git не установлен на вашем компьютере.
    echo.
    echo Чтобы загрузить файлы прямо сейчас через браузер без Git:
    echo 1. Откройте прямую ссылку:
    echo    https://github.com/Auriksys/kuban-street-special/upload/main
    echo 2. Перетащите все файлы из папки KubanStreetSpecial мышкой в браузер
    echo 3. Нажмите зеленую кнопку "Commit changes"!
    echo.
    pause
    exit /b
)

echo [1/5] Инициализация Git...
if not exist ".git" (
    git init
)

echo [2/5] Настройка автора коммита...
git config user.name "Auriksys"
git config user.email "auriksys@users.noreply.github.com"
git branch -M main

echo [3/5] Добавление файлов...
git add .

echo [4/5] Фиксация коммита...
git commit -m "Initial commit for Kuban Street Special"

echo [5/5] Подключение к https://github.com/Auriksys/kuban-street-special.git...
git remote remove origin 2>nul
git remote add origin https://github.com/Auriksys/kuban-street-special.git

echo.
echo Отправка на GitHub...
git push -u origin main --force

if %errorlevel% equ 0 (
    echo.
    echo ========================================================
    echo   🎉 ПОБЕДА! Все файлы успешно загружены в репозиторий!
    echo   https://github.com/Auriksys/kuban-street-special
    echo ========================================================
    echo.
    echo Теперь переходите на Render.com:
    echo 1. Откройте https://render.com
    echo 2. Нажмите "New +" -> "Web Service"
    echo 3. Выберите репозиторий kuban-street-special и нажмите "Deploy"!
) else (
    echo.
    echo Если появилось окно входа в GitHub, подтвердите авторизацию в браузере.
)
pause
