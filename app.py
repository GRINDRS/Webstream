from flask import Flask, render_template, request, redirect, url_for, Response, make_response
import json, time, cv2, io, threading
from PIL import Image
from collections import Counter
import paho.mqtt.client as mqtt

app = Flask(__name__)
cap = cv2.VideoCapture(0)


options = ["Mia", "May"]
answers = []
spoke_path = "spoke.json"

def load_json(name):
    with open(name) as f:
        return json.load(f)

def save_json(name, data):
    with open(name, 'w') as f:
        json.dump(data, f, indent=4)

def get_vote_cookie_key():
    return "has_voted_" + "_".join(option.lower() for option in options)

def generate_frames():
    prev = 0
    while True:
        time_elapsed = time.time() - prev
        if time_elapsed > 1 / 15:
            prev = time.time()
            success, frame = cap.read()
            if not success:
                break
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/', methods=['GET', 'POST'])
def index():
    spoke = load_json(spoke_path)
    vote_cookie_key = get_vote_cookie_key()
    has_voted = request.cookies.get(vote_cookie_key)

    if request.method == 'POST' and not has_voted:
        user_answer = request.form.get("answer")
        if user_answer in options:
            answers.append(user_answer)
            response = make_response(redirect(url_for("index")))
            response.set_cookie(vote_cookie_key, "true", max_age=60*60*24)
            return response
        else:
            return redirect(url_for("index"))

    count = Counter(answers)
    if count and count[options[0]] == count[options[1]]:
        most_common = "Equal answers."
    elif count:
        most_common = f"Most common answer: {count.most_common(1)[0][0]}"
    else:
        most_common = "No answers yet."

    return render_template(
        'index.html',
        spoke=spoke,
        most_common=most_common,
        options=options,
        has_voted=bool(has_voted)
    )

@app.route('/video')
def video():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/frame.jpg')
def frame():
    if not cap.isOpened():
        return "Camera error", 500
    success, frame = cap.read()
    cap.release()
    if not success:
        return "Frame capture failed", 500
    img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    buf = io.BytesIO()
    img.save(buf, format='JPEG')
    buf.seek(0)
    # return send_file(buf, mimetype='image/jpeg')

