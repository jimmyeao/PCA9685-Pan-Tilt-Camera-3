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
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
  
  <!-- Bootstrap CSS -->
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.4.0-alpha1/dist/css/bootstrap.min.css" rel="stylesheet" integrity="sha384-KyZXEAg3QhqLMpG8r+Knujsl5/5vzKmUzR7Zz8L0tvJ5Ubl1Fq5fDh9Gg9xEB9gt/" crossorigin="anonymous">
  
  <!-- jQuery -->
  <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>

  <!-- Bootstrap JS -->
  <script src="https://cdn.jsdelivr.net/npm/@popperjs/core@2.11.6/dist/umd/popper.min.js" integrity="sha384-oBqDVmMxFTUfQGfIOkAZz6nRd5cXf7p//c1l5zA8f8F+tzJ5U5//f3frY0X5L+U/" crossorigin="anonymous"></script>
  <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.4.0-alpha1/dist/js/bootstrap.min.js" integrity="sha384-pzjw8f+ua7Kw1TIq0v8FqFjcJ6pajs/rfdfs3SO+kD4Ck5BdPtF+to8xMp9MvcY/" crossorigin="anonymous"></script>
    <style>
    .stream-image {
      max-width: 80%;
      height: auto;
    }
  </style>
</head>

<body>
  <div class="container">
    <h1 class="text-center my-3">Picamera2 MJPEG Streaming and Control</h1>
    <div class="row">
      <div class="col-md-8 offset-md-2">
  <img src="stream.mjpg" class="img-fluid stream-image" alt="Camera Stream">
</div>

    </div>
    <div class="row mt-4">
  <div class="col-md-8 offset-md-2 d-flex justify-content-center">
    <div class="d-flex flex-column mx-2">
      <label for="servo1">Servo 1</label>
      <input type="range" class="form-range" id="servo1" min="0" max="180" step="1" value="90">
    </div>
    <div class="d-flex flex-column mx-2">
      <label for="servo2">Servo 2</label>
      <input type="range" class="form-range" id="servo2" min="0" max="180" step="1" value="90">
    </div>
    <button class="btn btn-primary mx-2" id="servo2_home">Home</button>
    <button class="btn btn-success mx-2" id="take_picture">Take Picture</button>
    <button class="btn btn-success mx-2" id="zoom_in">Zoom In</button>
    <button class="btn btn-success mx-2" id="zoom_out">Zoom Out</button>
  </div>
</div>

  </div>


<script>
  document.getElementById("servo1").addEventListener("input", function() {
    // send control signal to the server to set servo 1 position
    var xhr = new XMLHttpRequest();
    xhr.open("GET", "/servo/1/position/" + this.value);
    xhr.send();
  });
  document.getElementById("servo2").addEventListener("input", function() {
    // send control signal to the server to set servo 2 position
    var xhr = new XMLHttpRequest();
    xhr.open("GET", "/servo/2/position/" + this.value);
    xhr.send();
  });

  document.getElementById("servo2_home").addEventListener("click", function() {
    // send control signal to the server to rotate servo 2 right
    var xhr = new XMLHttpRequest();
    xhr.open("GET", "/servo/2/home");
    xhr.send();
    // reset servo 2 slider to default position
    document.getElementById("servo2").value = 90;
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
  
  // periodically check if reset sliders flag is set and reset sliders if true
setInterval(function() {
    var xhr = new XMLHttpRequest();
    xhr.open("GET", "/check_reset_sliders");
    xhr.onload = function() {
        if (xhr.status === 200 && xhr.responseText === "True") {
            // reset sliders to default positions
            document.getElementById("servo1").value = 90;
            document.getElementById("servo2").value = 90;
        }
    };
    xhr.send();
}, 1000);

</script>


</body>
</html>
"""
def reset_sliders():
    # reset sliders to default positions
    document.getElementById("servo1").value = 90;
    document.getElementById("servo2").value = 90;

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
        if self.path == "/":
            self.send_response(301)
            self.send_header("Location", "/index.html")
            self.end_headers()
        elif self.path == "/index.html":
            content = PAGE.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.send_header("Content-Length", len(content))
            self.end_headers()
            self.wfile.write(content)
        elif self.path == "/stream.mjpg":
            self.send_response(200)
            self.send_header("Age", 0)
            self.send_header("Cache-Control", "no-cache, private")
            self.send_header("Pragma", "no-cache")
            self.send_header(
                "Content-Type", "multipart/x-mixed-replace; boundary=FRAME"
            )
            self.end_headers()
            try:
                while True:
                    with output.condition:
                        output.condition.wait()
                        frame = output.frame
                    self.wfile.write(b"--FRAME\r\n")
                    self.send_header("Content-Type", "image/jpeg")
                    self.send_header("Content-Length", len(frame))
                    self.end_headers()
                    self.wfile.write(frame)
                    self.wfile.write(b"\r\n")
                   
            except Exception as e:
                logging.warning(
                    "Removed streaming client %s: %s", self.client_address, str(e)
                )
        elif self.path == "/servo/2/home":
                x = 105
                y = 90
                pwm.setRotationAngle(0, x)
                pwm.setRotationAngle(1, y)
                self.send_response(200)
                self.send_header("Content-Type", "text/plain")
                self.end_headers()
                self.wfile.write(b"Home position set")  
                self.server.reset_sliders_flag = True
                content = PAGE.encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/html")
                self.send_header("Content-Length", len(content))
                self.end_headers()
                self.wfile.write(content)
        elif self.path == "/check_reset_sliders":
         # check reset sliders flag and reset sliders if true
            if self.server.reset_sliders_flag:
                self.server.reset_sliders_flag = False
                self.send_response(200)
                self.send_header("Content-Type", "text/plain")
                self.end_headers()
                self.wfile.write(b"True")
            else:
                self.send_response(200)
                self.send_header("Content-Type", "text/plain")
                self.end_headers()
                self.wfile.write(b"False")

        elif self.path.startswith("/servo/"):
            try:
                parts = self.path.split("/")
                if len(parts) == 5 and parts[3] == "position":
                    servo_id = int(parts[2])
                    position = int(parts[4])

                    if servo_id == 1:
                        x = position
                        pwm.setRotationAngle(0, x)
                        print(f"x: {x}")
                    elif servo_id == 2:
                        y = position
                        pwm.setRotationAngle(1, y)
                        print(f"y: {y}")

                    self.send_response(200)
                    self.send_header("Content-Type", "text/plain")
                    self.end_headers()
                    self.wfile.write(b"Servo position set")
                else:
                    self.send_response(400)
                    self.send_header("Content-Type", "text/plain")
                    self.end_headers()
                    self.wfile.write(b"Bad request")
            except Exception as e:
                logging.error("Error setting servo position: %s", str(e))
                self.send_response(500)
                self.send_header("Content-Type", "text/plain")
                self.end_headers()
                self.wfile.write(b"Error setting servo position")
            
        elif self.path == "/take_picture":
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"Take picture endpoint reached")
            self.handle_take_picture()
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"Servo control signal sent")
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
        elif self.path == "/reset_sliders":
            self.reset_sliders()

    def handle_take_picture(self):
        print("handle_take_picture function called")
        try:
            # picam2.set_controls({"AeMode": controls.AeModeEnum.Manual})
            # Set the resolution for the hi-res picture
            hi_res_output = io.BytesIO()
            timestamp = datetime.now().isoformat()

            picam2.capture_file(
                "/home/pi/%s.jpg" % timestamp
            )  # Pass hi_res_output directly

            self.send_response(200)
            print("Taking Picture")
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"Picture taken and saved")
        except Exception as e:
            logging.error("Error taking hi-res picture: %s", str(e))
            self.send_response(500)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"Error taking hi-res picture")


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
#picam2.configure(picam2.create_video_configuration(main={"size": (2304, 1296)}))
picam2.configure(picam2.create_video_configuration(main={"size": (1920, 1080)}))
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
