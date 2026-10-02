import os
import shutil

base = os.path.dirname(os.path.abspath(__file__))
static = os.path.join(base, 'static')

# Copy index.html
shutil.copy2(os.path.join(static, 'index.html'), os.path.join(base, 'index.html'))

# Copy style.css
shutil.copy2(os.path.join(static, 'css', 'style.css'), os.path.join(base, 'style.css'))

# Copy all .js files
js_dir = os.path.join(static, 'js')
for f in os.listdir(js_dir):
    if f.endswith('.js'):
        shutil.copy2(os.path.join(js_dir, f), os.path.join(base, f))

print("OK: All files copied to root folder successfully!")
