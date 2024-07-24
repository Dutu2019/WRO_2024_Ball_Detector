This is the code for a Ping Pong ball tracking software. It uses OpenCV to detect pixels of a specific range of colors and then draws a bounding box around them. It also serves the video stream on a URL as this is supposed to run on a Raspberry Pi Zero 2 W, which has no display.

There is a Python version which works best and a C++ version. Make sure to update the color ranges for your specific lighting condition if you want to try the program.
