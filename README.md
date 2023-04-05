# PCA9685-Pan-Tilt-Camera-3
Python code for the raspberry pi to control a PCA9685 based pan/tilt servo and to stream/capture images

Added zoom in/out and take snapshot - pictures saved in /home/pi - edit the code if you want a different location!
Note, when taking a picture, it does not respect the zoom level, i haven't figured this bit out yet.

I would also like to add:

Camera Controls (Exposre, resolution, white balance etc)


# Setup
```
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
sudo python3 main.py
```
Now visit the webpage shown in the output:
![image](https://user-images.githubusercontent.com/5197831/230153050-1dc9e6c8-f457-412e-b5b2-3c08679f0f6c.png)


