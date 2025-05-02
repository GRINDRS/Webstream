from flask import Flask, Response  
import cv2  

app = Flask(__name__)  # Create a Flask web application instance

# Open the default webcam (index 0). Change to 1, 2, etc. if needed.
cap = cv2.VideoCapture(0)

# This function generates a stream of JPEG frames from the webcam
# Each frame is encoded and yielded as a chunked HTTP response (MJPEG format)
def generate_frames():
    while True:
        success, frame = cap.read()  # Read a frame from the webcam
        if not success:
            break  # If reading fails, exit the loop
        ret, buffer = cv2.imencode('.jpg', frame)  # Encode the frame as JPEG
        frame = buffer.tobytes()  # Convert to raw bytes
        # Yield in MJPEG format so browsers can render it as a live stream
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')


@app.route('/')
def index():
    return '''
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Live Video Feed</title>
            <style>
                body {
                    margin: 0;
                    padding: 0;
                    font-family: Arial, sans-serif;
                    background: #f4f4f4;
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    justify-content: center;
                    height: 100vh;
                    color: #333;
                }
                h1 {
                    margin-bottom: 20px;
                }
                .video-container {
                    background: white;
                    padding: 20px;
                    border-radius: 10px;
                    box-shadow: 0 0 15px rgba(0,0,0,0.1);
                }
                img {
                    border-radius: 10px;
                    max-width: 100%;
                    height: auto;
                }
            </style>
        </head>
        <body>
            <div class="video-container">
                <h1>Live Webcam Stream</h1>
                <img src="/video" width="640" /> <!-- Stream displayed as MJPEG image -->
            </div>
        </body>
        </html>
    '''

# Define the route for the video feed
# It returns a streaming response from the generate_frames() function
@app.route('/video')
def video():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

# Run the app on all network interfaces (0.0.0.0) so other devices can access it
# Port 5000 is the default Flask port
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
