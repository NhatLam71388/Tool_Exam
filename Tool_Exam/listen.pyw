import simpleobsws
import asyncio
import keyboard
import assemblyai as aai
import requests
import time
import os
import re

# ================= CẤU HÌNH =================
# OBS WebSocket (sử dụng WebSocket tích hợp của OBS Studio)
OBS_HOST = "localhost"
OBS_PORT = 4455
OBS_PASSWORD = "xojGcBOKzA2o7fcd"  # Mật khẩu WebSocket của OBS

# Đường dẫn lưu file ghi âm từ OBS
RECORDING_PATH = r"C:\Users\Dell\Desktop\nhap\listen"
FILENAME_PATTERN = r"\d{4}-\d{2}-\d{2} \d{2}-\d{2}-\d{2}"  # Regex khớp với tên file "YYYY-MM-DD HH-MM-SS"

# AssemblyAI
aai.settings.api_key = "fa7e021e750e4763986a364a846fcff6"

# Telegram
BOT_TOKEN = "8408463425:AAHgisahCKv1B8UGdzcLdR-9Fkf9HAAonaw"
CHAT_ID = "5994494061"

# ================= BIẾN TRẠNG THÁI =================
ws = None
recording = False

# ================= HÀM KẾT NỐI OBS =================
async def connect_obs():
    global ws
    ws = simpleobsws.WebSocketClient(url=f"ws://{OBS_HOST}:{OBS_PORT}", password=OBS_PASSWORD)
    try:
        await ws.connect()
        await ws.wait_until_identified()
        print("✅ Đã kết nối với OBS WebSocket.")
    except Exception as e:
        print(f"❌ Lỗi kết nối OBS WebSocket: {e}")
        raise

# ================= HÀM BẮT ĐẦU GHI ÂM =================
async def start_recording():
    global recording
    if recording:
        print("⚠️ Đang ghi rồi, không cần bấm nữa!")
        return

    request = simpleobsws.Request('StartRecord')
    response = await ws.call(request)
    if response.ok():
        recording = True
        print("🎙️ Bắt đầu ghi âm qua OBS...")
    else:
        print(f"Lỗi: {response.requestStatus.comment}")

# ================= HÀM DỪNG GHI ÂM =================
async def stop_recording():
    global recording
    if not recording:
        print("⚠️ Chưa bắt đầu ghi!")
        return

    request = simpleobsws.Request('StopRecord')
    response = await ws.call(request)
    if response.ok():
        recording = False
        print("🛑 Dừng ghi âm. Đang chờ file được lưu...")

        # Chờ file được lưu (OBS cần vài giây để finalize file)
        await asyncio.sleep(5)  # Thời gian chờ 5 giây

        # Tìm file mới nhất trong thư mục recording
        latest_file = get_latest_file(RECORDING_PATH, FILENAME_PATTERN)
        if latest_file:
            print(f"✅ Đã tìm thấy file: {latest_file}")

            # Chuyển giọng nói sang văn bản
            try:
                text = speech_to_text(latest_file)
                print("📝 Văn bản:", text)

                # Gửi lên Telegram
                send_to_telegram(text)
            except Exception as e:
                print(f"❌ Lỗi khi xử lý speech-to-text: {e}")
        else:
            print("❌ Không tìm thấy file mới!")
    else:
        print(f"Lỗi: {response.requestStatus.comment}")

# ================= TÌM FILE MỚI NHẤT =================
def get_latest_file(path, pattern):
    files = [f for f in os.listdir(path) if re.match(pattern, f.split('.')[0]) and f.endswith('.mkv')]
    print("Danh sách file tìm thấy:", files)  # Debug
    if not files:
        return None
    latest = max(files, key=lambda f: os.path.getctime(os.path.join(path, f)))
    return os.path.join(path, latest)

# ================ CHUYỂN GIỌNG NÓI -> VĂN BẢN ====================
def speech_to_text(filepath):
    config = aai.TranscriptionConfig(speech_model=aai.SpeechModel.universal)
    transcript = aai.Transcriber(config=config).transcribe(filepath)

    if transcript.status == "error":
        raise RuntimeError(f"Lỗi AssemblyAI: {transcript.error}")

    return transcript.text

# ================ GỬI TELEGRAM ====================
def send_to_telegram(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text}
    response = requests.post(url, json=payload)
    if response.ok:
        print("📩 Đã gửi nội dung lên Telegram.")
    else:
        print(f"❌ Lỗi gửi Telegram: {response.text}")

# ================= MAIN ====================
if __name__ == "__main__":
    print("⌨️ Nhấn phím [ để bắt đầu ghi, phím ] để dừng ghi và xử lý.")
    print("📌 Đảm bảo OBS Studio đang chạy ngầm với WebSocket tích hợp enabled.")

    # Kết nối OBS
    loop = asyncio.get_event_loop()
    loop.run_until_complete(connect_obs())

    # Lắng nghe phím bấm
    while True:
        if keyboard.is_pressed("["):  # Bắt đầu ghi
            loop.run_until_complete(start_recording())
            while keyboard.is_pressed("["):
                pass  # Chờ nhả phím

        if keyboard.is_pressed("]"):  # Dừng ghi
            loop.run_until_complete(stop_recording())
            while keyboard.is_pressed("]"):
                pass  # Chờ nhả phím

        time.sleep(0.1)  # Giảm tải CPU