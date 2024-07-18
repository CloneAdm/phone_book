# settings.py
import os
import pathlib
from datetime import datetime
import logging
from colorlog import ColoredFormatter

# Уровень логирования
LOG_LEVEL = logging.DEBUG

# URL для получения данных
URL = "http://10.0.2.30:2040/"

# Текущая дата и время
_current_datetime = datetime.now().strftime("%Y-%m-%d_%H-%M")

# Папка для хранения данных
BASE_DIR = pathlib.Path(_current_datetime)

# Создание папок, если они не существуют
os.makedirs(BASE_DIR, exist_ok=True)

PHOTO_DIR = pathlib.Path("foto")
JSON_FILE = BASE_DIR / f"phone_book_{_current_datetime}.json"
HTML_FILE = BASE_DIR / f"phone_book_{_current_datetime}.html"
LOG_FILE = BASE_DIR / f"phone_book_{_current_datetime}.log"

# Форматы логов и цвета
log_format = "%(log_color)s%(asctime)s.%(msecs)03d | %(levelname)-8s | %(name)-8s | %(funcName)-15s:%(lineno)-4d | %(message)s"
file_log_format = "%(asctime)s.%(msecs)03d | %(levelname)-8s | %(name)-8s | %(funcName)-15s:%(lineno)-4d | %(message)s"
date_format = "%Y-%m-%d %H:%M:%S"
log_colors = {
    "DEBUG": "cyan",
    "INFO": "green",
    "WARNING": "yellow",
    "ERROR": "light_red",
    "CRITICAL": "bold_red",
}

# Настройка логирования с кодировкой 'utf-8'
logger = logging.getLogger()
logger.setLevel(LOG_LEVEL)

# Обработчик для записи логов в файл
file_handler = logging.FileHandler(LOG_FILE, encoding='utf-8')
file_handler.setLevel(LOG_LEVEL)
file_handler.setFormatter(logging.Formatter(file_log_format, datefmt=date_format))

# Обработчик для вывода логов в консоль с цветами
console_handler = logging.StreamHandler()
console_handler.setLevel(LOG_LEVEL)
console_handler.setFormatter(ColoredFormatter(log_format, datefmt=date_format, log_colors=log_colors))

# Добавление обработчиков к логгеру
logger.addHandler(file_handler)
logger.addHandler(console_handler)
