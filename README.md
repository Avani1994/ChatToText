How To use this module:

Prerequistites:

Install the dependencies using following commands:

This Code is configured according to Python Version - 3.6.9 and OpenCV Version - 3.4.2.16
Use Conda to Configure the  environment. First create Conda Environment with Python 3.6.9. And then follow steps below:

Firstly install following libraries: 

* Google Tesseract - sudo apt install tesseract-ocr
* Libraries needed for python wrapper tesserocr - sudo apt-get install libleptonica-dev libtesseract-dev
* Opencv - sudo apt-get install python-opencv
* Also install other requirements - pip install -r requirements.txt

Now you are ready to use the ChatToText module

Run following command with arguments as described below:

 - python imagetotextwhatsapp.py "['img1.jpeg', 'img2.jpeg']"

* You can replace img1.jpeg and img2.jpeg with your own chat images 
* Also any number of images can be added in the string array argument



