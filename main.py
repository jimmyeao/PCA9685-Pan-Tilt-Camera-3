#!/usr/bin/python3

import io
import logging
import socketserver
import threading
from datetime import datetime
from http import server
from threading import Condition
from PCA9685 import PCA9685
from picamera2 import Picamera2
from libcamera import controls
from picamera2.encoders import JpegEncoder
from picamera2.outputs import FileOutput

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
MIN_ANGLE = 0

PAGE = """\
<html>
<head>
<title>picamera2 MJPEG streaming and control</title>
</head>
<body>
<h2>Picamera2 MJPEG streaming and control</h2>
<img src="stream.mjpg" width="1280" height="720" />
<br>
<button id="servo1_up">Up</button>
<button id="servo1_down">Down</button>
<button id="servo2_left">Left</button>
<button id="servo2_right">Right</button>
<button id="servo2_home">Home</button>
<button id="take_picture">Take Picture</button>
<button id="zoom_in">Zoom In</button>
<button id="zoom_out">Zoom Out</button>


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
  document.getElementById("take_picture").addEventListener("click", function() {
    // send control signal to the server to take a picture
    console.log("Take picture button clicked"); // Add this line
    var xhr = new XMLHttpRequest();
    xhr.open("GET", "/take_picture");
    xhr.send();
  });
  document.getElementById("zoom_in").addEventListener("click", function () {
    // send control signal to the server to zoom in
    var xhr = new XMLHttpRequest();
    xhr.open("GET", "/zoom_in");
    xhr.send();
  });
  document.getElementById("zoom_out").addEventListener("click", function () {
    // send control signal to the server to zoom out
    var xhr = new XMLHttpRequest();
    xhr.open("GET", "/zoom_out");
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
        elif self.path.startswith('/servo/1') or self.path.startswith('/servo/2'):
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
                    x = 105
                    y = 90
                    pwm.setRotationAngle(0, x)
                    pwm.setRotationAngle(1, y)
                    return "Home position set"  
                    pass    
        elif self.path == '/take_picture':
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'Take picture endpoint reached')
            self.handle_take_picture()
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'Servo control signal sent')
        elif self.path == "/zoom_in":
            self.handle_zoom_in()
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"Zoom in")
        elif self.path == "/zoom_out":
            self.handle_zoom_out()
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"Zoom out")            
    
    def handle_take_picture(self):
        print("handle_take_picture function called")
        try:
            # picam2.set_controls({"AeMode": controls.AeModeEnum.Manual})
            # Set the resolution for the hi-res picture
            hi_res_output = io.BytesIO()
            timestamp = datetime.now().isoformat()
            
            picam2.capture_file('/home/pi/%s.jpg' % timestamp) # Pass hi_res_output directly
         
            self.send_response(200)
            print("Taking Picture")
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'Picture taken and saved')
        except Exception as e:
            logging.error('Error taking hi-res picture: %s', str(e))
            self.send_response(500)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'Error taking hi-res picture')
    def handle_zoom_in(self):
        size = picam2.capture_metadata()["ScalerCrop"][2:]
        full_res = picam2.camera_properties["PixelArraySize"]
        print("Zoom In")
        # This syncs us to the arrival of a new camera frame:
        picam2.capture_metadata()

        size = [int(s * 0.95) for s in size]
        offset = [(r - s) // 2 for r, s in zip(full_res, size)]
        picam2.set_controls({"ScalerCrop": offset + size})
    def handle_zoom_out(self):
        size = picam2.capture_metadata()["ScalerCrop"][2:]
        full_res = picam2.camera_properties["PixelArraySize"]
        print("Zoom Out")
        # This syncs us to the arrival of a new camera frame:
        picam2.capture_metadata()

        size = [int(s / 0.95) for s in size]

        offset = [(r - s) // 2 for r, s in zip(full_res, size)]
        picam2.set_controls({"ScalerCrop": offset + size})        



class StreamingServer(socketserver.ThreadingMixIn, server.HTTPServer):
    allow_reuse_address = True
    daemon_threads = True


picam2 = Picamera2()
picam2.configure(picam2.create_video_configuration(main={"size": (2304, 1296)}))
picam2.set_controls({"AfMode": controls.AfModeEnum.Continuous})
output = StreamingOutput()
picam2.start_recording(JpegEncoder(), FileOutput(output))


    


################################

def starthome():
    global x, y
    x = 105
    y = 90
    pwm.setRotationAngle(0, x)
    pwm.setRotationAngle(1, y)
    return "Home position set"


###########################################

try:

        starthome()
        address = ('', 8000)
        server = StreamingServer(address, StreamingHandler)
        server.serve_forever()

      
finally:
    picam2.stop_recording()
