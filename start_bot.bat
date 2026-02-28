@echo off
chcp 65001 >nul
title Notes Bot
echo Активация виртуального окружения...
call venv\Scripts\activate.bat
echo Запуск бота...
python bot.py
pause