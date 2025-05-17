from flask import Flask, render_template, Response, send_file
import cv2
import time
import io
from PIL import Image

app = Flask(__name__)

# Open the default camera (0)
camera = cv2.VideoCapture(0)

def generate_frames():
    prev = 0
    while True:
        time_elapsed = time.time() - prev
        if time_elapsed > 1/15:  # limit to ~15 FPS
            prev = time.time()
            success, frame = camera.read()
            if not success:
                break
            else:
                ret, buffer = cv2.imencode('.jpg', frame)
                frame = buffer.tobytes()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video')
def video():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/frame.jpg')
def frame():
    success, frame = camera.read()
    if not success:
        return "Camera error", 500

    # Convert frame (OpenCV -> PIL -> JPEG bytes)
    img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    buf = io.BytesIO()
    img.save(buf, format='JPEG')
    buf.seek(0)

    return send_file(buf, mimetype='image/jpeg')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
