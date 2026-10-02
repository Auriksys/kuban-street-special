@echo off
chcp 65001 > nul
title Загрузка Kuban Street Special на GitHub
echo ========================================================
echo   🚀 АВТОМАТИЧЕСКАЯ ЗАГРУЗКА РЕПОЗИТОРИЯ НА GITHUB
echo ========================================================
where git >nul 2>nul
if %errorlevel% neq 0 (
    echo [ВНИМАНИЕ] Утилита Git не обнаружена в системе.
    echo.
    echo Самый простой способ (1 минута):
    echo 1. Откройте github.com/new и создайте репозиторий: kuban-street-special
    echo 2. Нажмите "uploading an existing file"
    echo 3. Просто перетащите все файлы из этой папки мышкой в браузер и нажмите "Commit"!
    echo.
    echo Или установите Git одной командой:
    echo   winget install Git.Git
    echo.
    pause
    exit /b
)

echo [1/4] Инициализация Git...
if not exist ".git" (
    git init
    git branch -M main
)

echo [2/4] Добавление файлов проекта...
git add .

echo [3/4] Создание коммита...
git commit -m "Deploy Kuban Street Special to Cloud"

echo.
echo ========================================================
echo Вставьте ссылку на ваш репозиторий GitHub
echo (например: https://github.com/ИМЯ_ПОЛЬЗОВАТЕЛЯ/kuban-street-special.git)
echo ========================================================
set /p REPO_URL="Вставьте ссылку и нажмите Enter: "

if "%REPO_URL%"=="" (
    echo Ссылка не введена.
    pause
    exit /b
)

git remote remove origin 2>nul
git remote add origin %REPO_URL%

echo.
echo [4/4] Отправка на GitHub...
git push -u origin main

if %errorlevel% equ 0 (
    echo.
    echo ========================================================
    echo   🎉 УСПЕШНО! Проект загружен на GitHub!
    echo ========================================================
    echo Теперь перейдите на https://render.com
    echo и выберите этот репозиторий в "New Web Service".
) else (
    echo.
    echo Если появилось окно браузера с подтверждением GitHub,
    echo нажмите "Authorize" или войдите в аккаунт.
)
pause
