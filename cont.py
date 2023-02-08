from flask import Flask, request
from flask import Flask, redirect, url_for
from PCA9685 import PCA9685
import time

app = Flask(__name__)

pwm = PCA9685()
pwm.setPWMFreq(50)
x,y = 90,90
MAX_ANGLE = 180
MIN_ANGLE = 50
@app.route("/")
def index():
    return '''
    <html>
        <head>
            <style>
                .btn {
                    width: 80px;
                    height: 40px;
                    font-size: 20px;
                    margin: 10px;
                }
            </style>
        </head>
        <body>
            <h1>Pan Tilt Control</h1>
            <button class="btn" id="left">Left</button>
            <button class="btn" id="right">Right</button>
            <button class="btn" id="up">Up</button>
            <button class="btn" id="down">Down</button>
            <button class="btn" id="home">Home</button>
            <script>
                const left = document.getElementById("left");
                const right = document.getElementById("right");
                const up = document.getElementById("up");
                const down = document.getElementById("down");
                let x = 90;
                let y = 90;
                
                left.addEventListener("mousedown", () => {
                    const interval = setInterval(() => {
                        if (x > 0) {
                            x -= 1;
                            fetch("/left", {method: "POST"});
                        }
                    }, 50);
                    left.addEventListener("mouseup", () => clearInterval(interval));
                });
                right.addEventListener("mousedown", () => {
                    const interval = setInterval(() => {
                        if (x < 180) {
                            x += 1;
                            fetch("/right", {method: "POST"});
                        }
                    }, 50);
                    right.addEventListener("mouseup", () => clearInterval(interval));
                });
                up.addEventListener("mousedown", () => {
                    const interval = setInterval(() => {
                        if (y < 180) {
                            y += 1;
                            fetch("/up", {method: "POST"});
                        }
                    }, 50);
                    up.addEventListener("mouseup", () => clearInterval(interval));
                });
                down.addEventListener("mousedown", () => {
                    const interval = setInterval(() => {
                        if (y > 0) {
                            y -= 1;
                            fetch("/down", {method: "POST"});
                        }
                    }, 50);
                    down.addEventListener("mouseup", () => clearInterval(interval));
                });
            </script>
        </body>
    </html>
    '''
def starthome():
    global x, y
    x = 90
    y = 90
    pwm.setRotationAngle(0, x)
    pwm.setRotationAngle(1, y)
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
    app.run(host='0.0.0.0', port=80)
