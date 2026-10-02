@echo off
chcp 65001 > nul
title Kuban Street Special - Persistent SSL Tunnel
echo ========================================================
echo   🌐 ЗАПУСК ПУБЛИЧНОГО SSL-ТУННЕЛЯ ДЛЯ KSS
echo ========================================================
python tunnel_manager.py
pause
