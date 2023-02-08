from flask import Flask, request, redirect, url_for, send_file
from flask import Response
from PCA9685 import PCA9685
import time
from PIL import Image
import io
from io import BytesIO
from picamera2 import Picamera2
app = Flask(__name__)

pwm = PCA9685()
pwm.setPWMFreq(50)
x,y = 90,90
MAX_ANGLE = 180
MIN_ANGLE = 50




        
@app.route("/")
def index():
    picam2 = Picamera2() 
    picam2.start() 
    time.sleep(1)
    image = picam2.capture_image("main")
    byte_io = BytesIO()
    image.save(byte_io, format='png')
    byte_io.seek(0)
    picam2.stop() 
    return send_file(byte_io, mimetype='image/png')


   
@app.route("/start_home", methods=["POST"])
def starthome():
    global x, y
    x = 90
    y = 90
    pwm.setRotationAngle(0, x)
    pwm.setRotationAngle(1, y)
    return "Home position set"

@app.route("/up", methods=["POST"])
def move_up():
    global x
    if x < MAX_ANGLE:
        x = x + 5
        pwm.setRotationAngle(0, x)
        print(f"x: {x}")
    return redirect(url_for("index"))

@app.route("/down", methods=["POST"])
def move_down():
    global x
    if x > MIN_ANGLE:
        x = x - 5
        pwm.setRotationAngle(0, x)
        print(f"x: {x}")
    return redirect(url_for("index"))

@app.route("/right", methods=["POST"])
def move_right():
    global y
    if y < MAX_ANGLE:
        y = y + 5
        pwm.setRotationAngle(1, y)
        print(f"y: {y}")
    return redirect(url_for("index"))

@app.route("/left", methods=["POST"])
def move_left():
    global y
    if y > MIN_ANGLE:
        y = y - 5
        pwm.setRotationAngle(1, y)
        print(f"y: {y}")
    return redirect(url_for("index"))
    
@app.route("/home", methods=["POST"])
def home():
    global x, y
    x = 90
    y = 90
    pwm.setRotationAngle(0, x)
    pwm.setRotationAngle(1, y)

if __name__ == '__main__':
    starthome()
    app.run(debug=True,host='0.0.0.0', port=80)

