#!/usr/bin/python3

import io
import logging
import socketserver
import threading
from http import server
from threading import Condition
from flask import Flask, request, redirect, url_for, send_file, render_template
from flask import Response
from PCA9685 import PCA9685
from picamera2 import Picamera2
from picamera2.encoders import JpegEncoder
from picamera2.outputs import FileOutput
app = Flask(__name__)

try:
    pwm = PCA9685()
    pwm.setPWMFreq(50)
except OSError as e:
    # Log the error message
    print("Error: ", e)
    # Exit the program
    sys.exit()
x,y = 90,90
MAX_ANGLE = 180
MIN_ANGLE = 50

PAGE = """\
<html>
<head>
<title>picamera2 MJPEG streaming demo</title>
</head>
<body>
<h1>Picamera2 MJPEG Streaming Demo</h1>
<img src="stream.mjpg" width="640" height="480" />
<br>
<button id="servo1_up">Up</button>
<button id="servo1_down">Down</button>
<button id="servo2_left">Left</button>
<button id="servo2_right">Right</button>
<button id="servo2_home">Home</button>
<script>
  document.getElementById("servo1_up").addEventListener("click", function() {
    // send control signal to the server to rotate servo 1 up
    var xhr = new XMLHttpRequest();
    xhr.open("GET", "/servo/1/up");
    xhr.send();
  });
  document.getElementById("servo1_down").addEventListener("click", function() {
    // send control signal to the server to rotate servo 1 down
    var xhr = new XMLHttpRequest();
    xhr.open("GET", "/servo/1/down");
    xhr.send();
  });
  document.getElementById("servo2_left").addEventListener("click", function() {
    // send control signal to the server to rotate servo 2 left
    var xhr = new XMLHttpRequest();
    xhr.open("GET", "/servo/2/left");
    xhr.send();
  });
  document.getElementById("servo2_right").addEventListener("click", function() {
    // send control signal to the server to rotate servo 2 right
    var xhr = new XMLHttpRequest();
    xhr.open("GET", "/servo/2/right");
    xhr.send();
  });
  document.getElementById("servo2_home").addEventListener("click", function() {
    // send control signal to the server to rotate servo 2 right
    var xhr = new XMLHttpRequest();
    xhr.open("GET", "/servo/2/home");
    xhr.send();
  });
</script>

</body>
</html>
"""


class StreamingOutput(io.BufferedIOBase):
    def __init__(self):
        self.frame = None
        self.condition = Condition()

    def write(self, buf):
        with self.condition:
            self.frame = buf
            self.condition.notify_all()


class StreamingHandler(server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(301)
            self.send_header('Location', '/index.html')
            self.end_headers()
        elif self.path == '/index.html':
            content = PAGE.encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.send_header('Content-Length', len(content))
            self.end_headers()
            self.wfile.write(content)
        elif self.path == '/stream.mjpg':
            self.send_response(200)
            self.send_header('Age', 0)
            self.send_header('Cache-Control', 'no-cache, private')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=FRAME')
            self.end_headers()
            try:
                while True:
                    with output.condition:
                        output.condition.wait()
                        frame = output.frame
                    self.wfile.write(b'--FRAME\r\n')
                    self.send_header('Content-Type', 'image/jpeg')
                    self.send_header('Content-Length', len(frame))
                    self.end_headers()
                    self.wfile.write(frame)
                    self.wfile.write(b'\r\n')
            except Exception as e:
                logging.warning(
                    'Removed streaming client %s: %s',
                    self.client_address, str(e))
        elif self.path.startswith('/servo'):
            global x,y
            # This is the endpoint that will handle the incoming requests from the buttons
            servo_id, direction = self.path.split('/')[2:]
            if servo_id == '1':
                if direction == 'up':
                    # Increase the PWM duty cycle for servo 1
                    if x < MAX_ANGLE:
                        x = x + 5
                        pwm.setRotationAngle(0, x)
                        print(f"x: {x}")
                    pass
                elif direction == 'down':
                    # Decrease the PWM duty cycle for servo 1
                    if x > MIN_ANGLE:
                        x = x - 5
                        pwm.setRotationAngle(0, x)
                        print(f"x: {x}")
                    return redirect(url_for("index"))                    
                    pass
            elif servo_id == '2':
                if direction == 'left':
                    # Increase the PWM duty cycle for servo 2
                    if y > MIN_ANGLE:
                        y = y - 5
                        pwm.setRotationAngle(1, y)
                        print(f"y: {y}")                    
                    pass
                elif direction == 'right':
                    # Decrease the PWM duty cycle for servo 2
                    if y < MAX_ANGLE:
                        y = y + 5
                        pwm.setRotationAngle(1, y)
                        print(f"y: {y}")                    
                    pass
                elif direction == 'home':
                    x = 90
                    y = 90
                    pwm.setRotationAngle(0, x)
                    pwm.setRotationAngle(1, y)
                    return "Home position set"  
                    pass                  
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'Servo control signal sent')




class StreamingServer(socketserver.ThreadingMixIn, server.HTTPServer):
    allow_reuse_address = True
    daemon_threads = True


picam2 = Picamera2()
picam2.configure(picam2.create_video_configuration(main={"size": (640, 480)}))
output = StreamingOutput()
picam2.start_recording(JpegEncoder(), FileOutput(output))
@app.route("/")
def index():
    return render_template('index.html')
    


################################

def starthome():
    global x, y
    x = 90
    y = 90
    pwm.setRotationAngle(0, x)
    pwm.setRotationAngle(1, y)
    return "Home position set"


###########################################

try:
    if __name__ == '__main__':
        starthome()
        address = ('', 8000)
        server = StreamingServer(address, StreamingHandler)
        server.serve_forever()

      
finally:
    picam2.stop_recording()
