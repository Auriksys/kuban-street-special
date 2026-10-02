@echo off
chcp 65001 > nul
title Создание архива для деплоя
python make_deploy_zip.py
echo.
echo Архив готов на Рабочем столе!
pause
