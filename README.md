# ChatToText
## Usage
This module extracts messages from the chat images into a JSON format. 
It is used by [messagink](https://www.linkedin.com/company/messagink/about/)

## Blogs
* [Part 1](https://towardsdatascience.com/chat-images-to-textual-conversation-c44aadef59fe)
* [Part 2](https://towardsdatascience.com/chat-images-to-textual-conversation-part-2-8260c09a032e)
* [Part 3](https://towardsdatascience.com/chat-images-to-textual-conversation-part-3-49cdee0f2c72)

## How To use this module:

### Prerequistites:

**Install the dependencies using following commands**

This Code is configured according to `Python Version - 3.6.9` and `OpenCV Version - 3.4.2.16`

Use `conda` to Configure the  environment. First create `conda` Environment with `Python 3.6.9.` And then follow steps below:

- Firstly install following libraries: 
  - Google Tesseract - `sudo apt install tesseract-ocr`
  - Libraries needed for python wrapper tesserocr - `sudo apt-get install libleptonica-dev libtesseract-dev`
  - Opencv - `sudo apt-get install python-opencv`
  - Also install other requirements - `pip install -r requirements.txt`

**Now you are ready to use the ChatToText module**

- Run following command with arguments as described below:
  - `python imagetotextwhatsapp.py "['img1.jpeg', 'img2.jpeg']"`
  - You can replace `img1.jpeg` and `img2.jpeg` with your own chat images
  - Also any number of images can be added in the string array argument



