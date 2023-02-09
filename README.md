# PCA9685-Pan-Tilt-Camera-3
Python code for the raspberry pi to control a PCA9685 based pan/tilt servo and to stream/capture images

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
![image](https://user-images.githubusercontent.com/5197831/217870655-658c2930-d272-4f9d-b084-0afe1c06b967.png)

