# PCA9685-Pan-Tilt-Camera-3
Python code for the raspberry pi to control a PCA9685 based pan/tilt servo and to stream/capture images

# Setup
```
sudo apt-get install python3-pip
pip3 install flask
pip3 install smbus
sudo raspi-config
	Select "Interfacing Options."
	Select "I2C."
	Select "Yes" to enable the I2C interface.
	Select "OK" and then "Finish" to save the changes.
	Reboot the Raspberry Pi for the changes to take effect.
```
Then
```
git clone https://github.com/jimmyeao/PCA9685-Pan-Tilt-Camera-3.git
cd PCA9685-Pan-Tilt-Camera-3
python3 main.py
```
Now visit the webpage shown in the output:
![image](https://user-images.githubusercontent.com/5197831/217539943-a8492a73-fb53-4ba2-b512-10bb4dff0ef6.png)
