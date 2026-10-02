import os
import zipfile

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ZIP_OUTPUT = os.path.join(os.path.dirname(BASE_DIR), "KubanStreetSpecial_Deploy.zip")

EXCLUDE_DIRS = {'.git', '__pycache__', '.pytest_cache', '.vscode', '.idea'}
EXCLUDE_FILES = {'KubanStreetSpecial_Deploy.zip'}

print("=" * 65)
print("📦 СБОРКА АРХИВА ДЛЯ ОБЛАЧНОГО ХОСТИНГА KUBAN STREET SPECIAL")
print("=" * 65)

count = 0
with zipfile.ZipFile(ZIP_OUTPUT, 'w', zipfile.ZIP_DEFLATED) as zipf:
    for root, dirs, files in os.walk(BASE_DIR):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        for file in files:
            if file in EXCLUDE_FILES or file.endswith('.pyc'):
                continue
            abs_path = os.path.join(root, file)
            rel_path = os.path.relpath(abs_path, BASE_DIR)
            zipf.write(abs_path, rel_path)
            count += 1

print(f"✅ Успешно упаковано {count} файлов в архив:")
print(f"📁 {ZIP_OUTPUT}")
print("=" * 65)
