import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from db.database import clear_all_data

if __name__ == '__main__':
    print("=" * 60)
    print("🧹 KUBAN STREET SPECIAL — ОЧИСТКА БАЗЫ ДАННЫХ")
    print("=" * 60)
    clear_all_data()
    print("\n✅ Сайт теперь полностью чист! В базе 0 машин, 0 спотов, 0 новостей.")
    print("Вы можете наполнить его с чистого листа:")
    print("1. Через программу админа: start_admin.bat")
    print("2. Либо пользователи сами добавят авто через сайт или бота @Kuban_Streetbot!")
