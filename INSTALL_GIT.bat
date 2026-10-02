@echo off
chcp 65001 > nul
title Автоматическая установка Git для Windows
echo ========================================================
echo   📥 АВТОМАТИЧЕСКАЯ УСТАНОВКА GIT НА ВАШ КОМПЬЮТЕР
echo ========================================================
echo Подождите, Windows скачивает официальный Git...
winget install --id Git.Git -e --source winget --accept-source-agreements --accept-package-agreements
if %errorlevel% equ 0 (
    echo.
    echo ========================================================
    echo   🎉 Git успешно установлен!
    echo   Теперь закройте это окно и запустите PUSH_TO_AURIKSYS.bat
    echo ========================================================
) else (
    echo.
    echo Не удалось автоматически скачать через winget.
    echo Пожалуйста, используйте загрузку файлов через браузер на странице:
    echo https://github.com/Auriksys/kuban-street-special/upload
)
pause
