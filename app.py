import io
import cv2
import os
import time
import requests
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from picamera2 import Picamera2, MappedArray
from datetime import datetime

# Configurations
GO_BACKEND_UPLOAD_URL = "http://<your-go-backend-ip>:<port>/upload"  # e.g., http://192.168.1.100:8080/upload
CHUNK_DURATION_SEC = 10
MJPEG_PORT = 8000
FRAME_RATE = 24
RESOLUTION = (640, 480)

picam2 = Picamera2()
video_config = picam2.create_video_configuration(main={"size": RESOLUTION, "format": "RGB888"})
picam2.configure(video_config)
picam2.start()

# MJPEG Streaming Server
class MJPEGHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'multipart/x-mixed-replace; boundary=frame')
        self.end_headers()
        try:
            while True:
                frame = picam2.capture_array()
                _, jpeg = cv2.imencode('.jpg', frame)
                self.wfile.write(b'--frame\r\n')
                self.wfile.write(b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n')
                time.sleep(1 / FRAME_RATE)
        except (BrokenPipeError, ConnectionResetError):
            pass

def start_mjpeg_server():
    server = HTTPServer(('', MJPEG_PORT), MJPEGHandler)
    print(f"[STREAMING] MJPEG available at http://<pi-ip>:{MJPEG_PORT}")
    server.serve_forever()

# Recording and Upload Thread
def record_and_upload():
    while True:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"/tmp/vid_{timestamp}.mp4"
        print(f"[RECORDING] {output_path}")

        # Record with ffmpeg directly from Pi camera (via raw stream)
        record_cmd = f"ffmpeg -y -f v4l2 -framerate {FRAME_RATE} -video_size {RESOLUTION[0]}x{RESOLUTION[1]} -i /dev/video0 -t {CHUNK_DURATION_SEC} -c:v libx264 {output_path}"
        os.system(record_cmd)

        print(f"[UPLOAD] Sending {output_path}")
        try:
            with open(output_path, 'rb') as f:
                files = {'file': (os.path.basename(output_path), f, 'video/mp4')}
                r = requests.post(GO_BACKEND_UPLOAD_URL, files=files)
                print(f"[UPLOAD] Status {r.status_code}")
        except Exception as e:
            print(f"[UPLOAD ERROR] {e}")
        finally:
            os.remove(output_path)

# Start both threads
threading.Thread(target=start_mjpeg_server, daemon=True).start()
threading.Thread(target=record_and_upload, daemon=True).start()

# Keep alive
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("Exiting...")
    picam2.stop()
