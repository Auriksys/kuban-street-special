@echo off
chcp 65001 > nul
title KSS - Выход в Интернет
cd /d "c:\Users\Аркадий\Desktop\KubanStreetSpecial"
python deploy_tunnel.py
pause
