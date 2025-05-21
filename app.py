from flask import Flask, render_template, request, redirect, url_for, Response, make_response, send_file
import json, time, cv2, io, threading
from PIL import Image
from collections import Counter
import paho.mqtt.client as mqtt

app = Flask(__name__)

# Initialize the webcam
cap = cv2.VideoCapture(0)

# Voting options
options = ["Mia", "May"]
# Store user answers (in memory)
answers = []

# Path to JSON file used for shared data
spoke_path = "spoke.json"

def load_json(name):
    """
    Load JSON data from a file.

    Args:
        name (str): File path.

    Returns:
        dict: Parsed JSON data.
    """
    with open(name) as f:
        return json.load(f)

def save_json(name, data):
    """
    Save JSON data to a file.

    Args:
        name (str): File path.
        data (dict): Data to save.
    """
    with open(name, 'w') as f:
        json.dump(data, f, indent=4)

def get_vote_cookie_key():
    """
    Generate a unique cookie key to track if the user has voted.

    Returns:
        str: Unique cookie key.
    """
    return "has_voted_" + "_".join(option.lower() for option in options)

def generate_frames():
    """
    Generator function that captures frames from the camera and yields them as JPEG byte streams
    for real-time video streaming over HTTP.
    """
    prev = 0
    while True:
        time_elapsed = time.time() - prev
        if time_elapsed > 1 / 15:  # Limit to ~15 FPS
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
    """
    Render the main page and handle form submissions for user voting.
    Cookies are used to prevent multiple votes.
    """
    spoke = load_json(spoke_path)
    vote_cookie_key = get_vote_cookie_key()
    has_voted = request.cookies.get(vote_cookie_key)

    if request.method == 'POST' and not has_voted:
        user_answer = request.form.get("answer")
        if user_answer in options:
            answers.append(user_answer)
            # Set cookie to prevent duplicate voting
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
    """
    Stream live video from the camera to the browser using multipart/x-mixed-replace.
    """
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/frame.jpg')
def frame():
    """
    Capture a single frame from the camera and return it as a JPEG image.
    """
    try:
        temp_cap = cv2.VideoCapture(0)
        if not temp_cap.isOpened():
            return "Camera error", 500
        success, frame = temp_cap.read()
        temp_cap.release()
        if not success:
            return "Frame capture failed", 500

        # Convert OpenCV image (BGR) to PIL Image (RGB)
        img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        buf = io.BytesIO()
        img.save(buf, format='JPEG')
        buf.seek(0)
        return send_file(buf, mimetype='image/jpeg')
    except Exception as e:
        print(f"Frame capture exception: {e}")
        return "Internal error", 500

if __name__ == '__main__':
    # Start the Flask app
    app.run(host='0.0.0.0', port=5000, threaded=True)
