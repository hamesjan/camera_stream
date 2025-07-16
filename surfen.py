import lgpio
import time
import threading
import websocket
import json
import subprocess

# --- GPIO Setup ---
M1_DIR = 17
M1_STEP = 27
M1_EN = 22
M2_DIR = 5
M2_STEP = 6
M2_EN = 13

h = lgpio.gpiochip_open(0)
for pin in [M1_DIR, M1_STEP, M1_EN, M2_DIR, M2_STEP, M2_EN]:
    lgpio.gpio_claim_output(h, pin)
    lgpio.gpio_write(h, pin, 0)

def step_motor(motor_id, direction, steps, delay=0.001):
    dir_pin = M1_DIR if motor_id == 1 else M2_DIR
    step_pin = M1_STEP if motor_id == 1 else M2_STEP
    lgpio.gpio_write(h, dir_pin, 1 if direction == 1 else 0)
    for _ in range(steps):
        lgpio.gpio_write(h, step_pin, 1)
        time.sleep(delay)
        lgpio.gpio_write(h, step_pin, 0)
        time.sleep(delay)

def handle_command(command):
    if command == "up":
        step_motor(1, direction=1, steps=100)
    elif command == "down":
        step_motor(1, direction=0, steps=100)
    elif command == "right":
        step_motor(2, direction=1, steps=100)
    elif command == "left":
        step_motor(2, direction=0, steps=100)

def on_message(ws, message):
    try:
        data = json.loads(message)
        cmd = data.get("command")
        handle_command(cmd)
    except Exception as e:
        print("Error handling message:", e)

def on_open(ws):
    print("Connected to Control WebSocket")
    ws.send(json.dumps({ "client": "pi" }))

def on_close(ws, close_status_code, close_msg):
    print("WebSocket closed")

def start_websocket():
    ws = websocket.WebSocketApp(
        "ws://<EC2_PUBLIC_IP>:8090",
        on_message=on_message,
        on_open=on_open,
        on_close=on_close
    )
    ws.run_forever()

def start_video_stream():
    cmd = [
        "bash", "-c",
        "libcamera-vid -t 0 --width 640 --height 480 --framerate 25 --codec yuv420 -o - | "
        "ffmpeg -f lavfi -i anullsrc=channel_layout=stereo:sample_rate=44100 "
        "-f rawvideo -pixel_format yuv420p -video_size 640x480 -framerate 25 -i - "
        "-c:v libx264 -preset ultrafast -b:v 2000k -c:a aac -b:a 128k -ar 44100 "
        "-f mpegts -mpegts_copyts 1 http://<EC2_PUBLIC_IP>:8081/supersecret"
    ]
    subprocess.Popen(cmd)

# --- Main ---
try:
    threading.Thread(target=start_websocket, daemon=True).start()
    start_video_stream()
    while True:
        time.sleep(1)
finally:
    lgpio.gpiochip_close(h)
