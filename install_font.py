import urllib.request
import os
import winreg
import shutil

url = 'https://github.com/google/fonts/raw/main/ofl/vazirmatn/Vazirmatn-Regular.ttf'
font_dir = os.path.join(os.environ['LOCALAPPDATA'], 'Microsoft', 'Windows', 'Fonts')
os.makedirs(font_dir, exist_ok=True)
dest = os.path.join(font_dir, 'Vazirmatn-Regular.ttf')

print("Downloading font...")
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req) as resp, open(dest, 'wb') as out:
    shutil.copyfileobj(resp, out)

print("Installing font in registry...")
key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Software\Microsoft\Windows NT\CurrentVersion\Fonts', 0, winreg.KEY_SET_VALUE)
winreg.SetValueEx(key, 'Vazirmatn Regular (TrueType)', 0, winreg.REG_SZ, 'Vazirmatn-Regular.ttf')
winreg.CloseKey(key)

print("Font Vazirmatn downloaded and installed successfully!")
