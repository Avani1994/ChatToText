# -*- coding: utf-8 -*-
"""ImagetotextWhatsapp.ipynb

Automatically generated by Colaboratory.

Original file is located at
    V1 https://colab.research.google.com/drive/1lm4B7oRazaiLVL01brl7WZlVuP5iMU-b
    V2 https://colab.research.google.com/drive/1Djl3V7Fx8A13d4SVBlrhZ_fNtZ0YUtqT
"""

# !sudo apt install tesseract-ocr

# !pip3 install pytesseract

# !sudo apt-get install libleptonica-dev libtesseract-dev

# !pip3 install tesserocr
#!pip install ImageHash
#!pip install opencv-python==3.4.2.16
#!pip install opencv-contrib-python==3.4.2.16

import pytesseract
import shutil
import os
import random
import tesserocr
import cv2
#from google.colab.patches import cv2_imshow
import re 
from pylab import array, plot, show, axis, arange, figure, uint8 
from skimage.measure import compare_ssim
import imutils
import numpy as np
import sys, ast
from pylab import *
from pathlib import Path
import pickle
try:
    from PIL import Image
except ImportError:
    import Image
import json

#from google.colab import files
import logging
logging.getLogger("imported_module").setLevel(logging.WARNING)



regextime = re.compile(r'((([0|'']?[1-9]|1[0-2])(:|\.|-)[0-5][0-9]((:|\.)[0-5][0-9])?( )?(AM|am|aM|Am|PM|pm|pM|Pm))|(([0]?[0-9]|1[0-9]|2[0-3])(:|\.)[0-5][0-9]((:|\.)[0-5][0-9])?))') 
regexAmPm = re.compile(r'(([\d])(' '|'')(.m|.M| .m| .M]))')
regex24hr = re.compile(r'(((''|[\d])[\d])(:|\.|-)([\d][\d]))')

def getMinMaxBorder(boxes):
  minn = float('inf')
  maxx = float('-inf')
  for i, (im,box,_,_) in enumerate(boxes):
    x,y,w,h = box['x'],box['y'],box['w'],box['h']
    if(x < minn):
      minn = x
    if(x+w > maxx):
      maxx = x+w
  return (minn, maxx)

def fill_rects(image, stats):
  for i,stat in enumerate(stats):
    if i > 0:
        p1 = (stat[0],stat[1])
        p2 = (stat[0] + stat[2],stat[1] + stat[3])
        cv2.rectangle(image,p1,p2,255,-1)

def crop(im1, im2):
  if(len(arr) > 1):
    img1 = cv2.imread(im1, 0)
    img2 = cv2.imread(im2, 0)
    imgorig1 = cv2.imread(im1)
    imgorig2 = cv2.imread(im2)
    h1, w1 = img1.shape
    h2, w2 = img2.shape

    if(h1 == h2 and w1 == w2):
      
      # Subtract the 2 image to get the difference region
      img3 = cv2.subtract(img1,img2)

      # Make it smaller to speed up everything and easier to cluster
      small_img = cv2.resize(img3,(0,0),fx = 0.25, fy = 0.25)
      img_h, img_w = small_img.shape

      # Morphological close process to cluster nearby objects
      fat_img = cv2.dilate(small_img, None,iterations = 20)
      fat_img = cv2.erode(fat_img, None,iterations = 20)

      fat_img = cv2.dilate(fat_img, None,iterations = 20)
      fat_img = cv2.erode(fat_img, None,iterations = 20)

      # Threshold strong signals
      _, bin_img = cv2.threshold(fat_img,20,255,cv2.THRESH_BINARY)

      # Analyse connected components
      num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(bin_img)

      # Cluster all the intersected bounding box together
      rsmall, csmall = np.shape(small_img)
      new_img1 = np.zeros((rsmall, csmall), dtype=np.uint8)

      fill_rects(new_img1,stats)


      # Analyse New connected components to get final regions
      num_labels_new, labels_new, stats_new, centroids_new = cv2.connectedComponentsWithStats(new_img1)

      min_dia_width = img_w * 0.1
      fScale = 0.25

      dia_regions = []
      for i ,stat in enumerate(stats_new):
        if i > 0:
          # get basic dimensions
          x,y,w,h = stat[0:4]

          # calculate ratio
          ratio = w / float(h)

          # if condition met, save in list
          if ratio < 1 and w > min_dia_width:
              dia_regions.append((x/fScale,y/fScale,w/fScale,h/fScale))


      # for region in dia_regions:
      #   x,y,w,h = region
      #   x = int(x)
      #   y = int(y)
      #   w = int(w)
      #   h = int(h)
      #   cv2.rectangle(img1,(x,y),(x+w,y+h),(0,255,0),2)
        
      x,y,w,h= dia_regions[0]
      crop_img = imgorig2[int(y):int(y+h),int(x):int(x+w)]
      #cv2_imshow(img2)
      #print('\n')
      #cv2_imshow(crop_img)
      # labels_disp = np.uint8(200*labels/np.max(labels)) + 50
      # labels_disp2 = np.uint8(200*labels_new/np.max(labels_new)) + 50


      # regular_img = cv2.resize(labels_disp2,(w1, h1),fx = 4, fy = 4)

      return crop_img
    else:
      #print("Not equal")
      return(None)

	
def fixDarkMode(image, mode):
    maxIntensity = 90.0 # depends on dtype of image data
    # Parameters for manipulating image data
    phi = 1.5
    theta = 0.9
    # Decrease intensity such that
    # dark pixels become much darker, 
    # bright pixels become slightly dark 
    newImage1 = (maxIntensity/phi)*(image/(maxIntensity/theta))**1.5
    newImage1 = array(newImage1,dtype=uint8)
    mask = cv2.bitwise_not(newImage1)
    # use mask or not based on dark mode or light mode image ("newImage1" for light mode and "mask" for dark mode)
    if(mode == 'Light'):
      finalImg = newImage1
    else:
      finalImg = mask
    #print(final)
    
    # image manipulation to change every pixel value based on some threshold value (here 140)
    for x in finalImg:
      for pixel in range(0,len(x)):
        if(0<x[pixel]<140):
          x[pixel]=0
        if(x[pixel]>=140):
          x[pixel]=255
    
    return finalImg

def detectEmoji(img, mode):
  image = cv2.imread(img,0) # load as 1-channel 8bit grayscale
    #image = cv2.imread('sanyatext.jpeg',0) # load as 1-channel 8bit grayscale
  imagefinal = cv2.imread(img)
  height,width,c = imagefinal.shape
  pixelsthresh = 0.007 * height * width
  heightupperthresh = 0.000093 * height * width
  widthupperthresh = 0.000093 * height * width
  heightlowerthresh = 0.0000144 * height * width
  widthlowerthresh = 0.000019 * height * width
  
  '''
  img = image

  white_lower = np.asarray([230, 230, 230])
  white_upper = np.asarray([255, 255, 255])

  mask = cv2.inRange(img, white_lower, white_upper)
  mask = cv2.bitwise_not(mask)
  '''

  maxIntensity = 90.0 # depends on dtype of image data

  # Parameters for manipulating image data
  phi = 1.5
  theta = 0.9

  # Decrease intensity such that
  # dark pixels become much darker, 
  # bright pixels become slightly dark 
  newImage1 = (maxIntensity/phi)*(image/(maxIntensity/theta))**1.5
  newImage1 = array(newImage1,dtype=uint8)
  mask = cv2.bitwise_not(newImage1)
  #cv2_imshow(newImage1)
  # use mask or not based on dark mode or light mode image ("newImage1" for light mode and "mask" for dark mode)
  if(mode == 'Light'):
    finalImg = newImage1
  else:
    finalImg = mask
  #print(final)
  
  # image manipulation to change every pixel value based on some threshold value (here 140)
  for x in finalImg:
    for pixel in range(0,len(x)):
      if(0<x[pixel]<140):
        x[pixel]=0
      if(x[pixel]>=140):
        x[pixel]=255
  
  # Now threshold the image based on adaptive value (Read more bout this function what it does)
  binary_img = cv2.adaptiveThreshold(finalImg, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                    cv2.THRESH_BINARY_INV, 131, 15)
  #cv2_imshow(binary_img)
  _, _, boxes, _ = cv2.connectedComponentsWithStats(binary_img)
  
  # first box is the background
  boxes = boxes[1:]
  filtered_boxes = []
  for x,y,w,h,pixels in boxes:
      #print(pixels)
      if pixels < pixelsthresh and h < heightupperthresh and w < widthupperthresh and h > heightlowerthresh  and w > widthlowerthresh: 
        #these are values for filtering boxes as we only want boxes which contain emoji in them
        filtered_boxes.append((x,y,w,h,pixels))

  
  #show = []
  emoji = []
  i = 0
  path = os.path.abspath("../ChatToText/DetectedEmoji/")
  fileobj = Path(path)
  if fileobj.exists():
    shutil.rmtree(path)
  os.makedirs(path)
  boundingBoxMapping = {}
  for x,y,w,h,pixels in filtered_boxes:
      side = max(w,h)
      crop_img = imagefinal[y-8:y+side, x-5:x+side+5]
      cv2.imwrite(path + '/image' + str(i) + '.png', crop_img)
      #cv2.rectangle(imagefinal, (x-5,y-8), (x+side+5,y+side), (0,0,255),2)
      #cv2_imshow(crop_img)
      boundingBoxMapping[(x-5, y-8, x+side+5, y+side)] = path + '/image' + str(i) + '.png'
      #print(pixels)
      #print(x,y,w,h)
      #show.append(crop_img)
      crop_img = Image.fromarray(crop_img)
      emoji.append(crop_img)
      i = i+1
  #cv2_imshow(imagefinal)
  #print(boundingBoxMapping)
  return boundingBoxMapping


# Resize images to a similar dimension
# This helps improve accuracy and decreases unnecessarily high number of keypoints
def imageResizeTrain(image):
    maxD = 1024
    height,width = image.shape
    aspectRatio = width/height
    if aspectRatio < 1:
        newSize = (int(maxD*aspectRatio),maxD)
    else:
        newSize = (maxD,int(maxD/aspectRatio))
    image = cv2.resize(image,newSize)
    return image

def imageResizeTest(image):
    maxD = 1024
    height,width,channel = image.shape
    aspectRatio = width/height
    if aspectRatio < 1:
        newSize = (int(maxD*aspectRatio),maxD)
    else:
        newSize = (maxD,int(maxD/aspectRatio))
    image = cv2.resize(image,newSize)
    return image


def computeSIFT(image):
    sift = cv2.xfeatures2d.SIFT_create()
    return sift.detectAndCompute(image, None)

def fetchKeypointsandDescriptorsTest(imgpath):
  imagebw = imageResizeTrain(cv2.imread(imgpath,0))
  keypointTest, descriptorTest = computeSIFT(imagebw)
  return keypointTest, descriptorTest

def fetchDescriptorFromFile(emoji):
    filepathL = os.path.abspath("../ChatToText/Descriptors/" + emoji + "/L.txt")
    filepathD = os.path.abspath("../ChatToText/Descriptors/" + emoji + "/D.txt")
    descriptorL = None
    descriptorD = None
    fileobjL = Path(filepathL)
    if fileobjL.exists():
      fileL = open(filepathL,'rb')
      descriptorL = pickle.load(fileL)
      fileL.close()
    fileobjD = Path(filepathD)
    if fileobjD.exists():
      fileD = open(filepathD,'rb')
      descriptorD = pickle.load(fileD)
      fileD.close()
    return descriptorL, descriptorD

def fetchKeypointFromFile(emoji):
    filepathL = os.path.abspath("../ChatToText/Keypoints/" + emoji + "/L.txt")
    filepathD = os.path.abspath("../ChatToText/Keypoints/" + emoji + "/D.txt")
    # str(imageList[i].split('.')[0]) + ".txt"
    keypointL = []
    keypointD = []
    deserializedKeypointsL = []
    deserializedKeypointsD = []
    fileobjL = Path(filepathL)
    if fileobjL.exists():
      fileL = open(filepathL,'rb')
      deserializedKeypointsL = pickle.load(fileL)
      fileL.close()
    fileobjD = Path(filepathD)
    if fileobjD.exists():
      fileD = open(filepathD,'rb')
      deserializedKeypointsD = pickle.load(fileD)
      fileD.close()
    for point in deserializedKeypointsL:
        temp = cv2.KeyPoint(x=point[0][0],y=point[0][1],_size=point[1], _angle=point[2], _response=point[3], _octave=point[4], _class_id=point[5])
        keypointL.append(temp)
    for point in deserializedKeypointsD:
        temp = cv2.KeyPoint(x=point[0][0],y=point[0][1],_size=point[1], _angle=point[2], _response=point[3], _octave=point[4], _class_id=point[5])
        keypointD.append(temp)
    return keypointL, keypointD

def calculateScore(matches,keypoint1,keypoint2):
    return 100 * (matches/min(keypoint1,keypoint2))

#Main KNN algorithm to detect similarity on SIFT Features
def calculateMatches(des1,des2):
    bf = cv2.BFMatcher()
    matches = bf.knnMatch(des1,des2,k=2)
    topResults1 = []
    for i, pair in enumerate(matches):
      try:
          m, n = pair
          if m.distance < 0.7*n.distance:
              topResults1.append([m])
      except ValueError:
          pass            
    matches = bf.knnMatch(des2,des1,k=2)
    topResults2 = []
    for i, pair in enumerate(matches):
      try:
          m, n = pair
          if m.distance < 0.7*n.distance:
              topResults2.append([m])
      except ValueError:
          pass
    topResults = []
    for match1 in topResults1:
        match1QueryIndex = match1[0].queryIdx
        match1TrainIndex = match1[0].trainIdx

        for match2 in topResults2:
            match2QueryIndex = match2[0].queryIdx
            match2TrainIndex = match2[0].trainIdx

            if (match1QueryIndex == match2TrainIndex) and (match1TrainIndex == match2QueryIndex):
                topResults.append(match1)
    return topResults

def findEmojiMatch(emoji):
    maxScore = float('-inf')
    matchedEmoji = None
    keypointEmoji,descriptorEmoji = fetchKeypointsandDescriptorsTest(emoji)
    #,_ = fetchDescriptorFromFile(emoji)
    subdirs = [x[0] for x in os.walk(os.path.abspath("../ChatToText/InitialTestSIFTFeatures/"))]                                                                            
    for subdir in subdirs[1:]:
        #r[subdir] =  {} 
        #print(subdir)
        files = os.walk(subdir).__next__()[2]    
        #print(files)                                                                         
        if (len(files) > 0):
          #print(subdir)   
          em = subdir.split('/')[-1]                                                                                       
          keypointL, keypointD = fetchKeypointFromFile(em)
          descriptorL, descriptorD = fetchDescriptorFromFile(em)
          scoreL = float('-inf')
          scoreD = float('-inf')
          #print(descriptorL)
          if(keypointL and descriptorEmoji is not None and len(descriptorEmoji) > 0):
            matchesL = calculateMatches(descriptorEmoji, descriptorL)
            scoreL = calculateScore(len(matchesL), len(keypointEmoji), len(keypointL))
          if(keypointD and descriptorEmoji is not None and len(descriptorEmoji) > 0):
            matchesD = calculateMatches(descriptorEmoji, descriptorD)
            scoreD = calculateScore(len(matchesD), len(keypointEmoji), len(keypointD))
          
          score = max(scoreL, scoreD)
          #print(score,em,"**********")
          if(score > maxScore):
            maxScore = score
            matchedEmoji = em
    return matchedEmoji, maxScore

#emoji Name mapping to Unicode
def returnEmojiNameToUnicodeMapping():
  emojiNameToUnicode = {' Face with Cowboy Hat':'🤠', 'Anger Face':'😠', 'Angry Face': '😡', 'Crying Face':'😢', 
                      'Disappointed Face': '😞', 'Disappointed but Relieved Face': '😥', 
                      'Face Screaming in Fear' : '😱', 'Face Throwing a Kiss': '😘', 'Face With Rolling Eyes':'🙄', 
                      'Face With Tears of Joy':'😂', 'Face With Wide Open Eyes':'😳','Face With a Zipper Mouth': '🤐',
                      'Face with Cold Sweat':'😓', 'Face with Open Mouth': '😮','Face with Open Mouth Vomiting': '🤮',
                      'Face with Pleading Eyes': '🥺', 'Grimacing Face': '😬', 'Hugging Face':'🤗', 
                      'Kissing Face With Wide Eyes':'😗',
                      'Loudly Crying Face': '😭', 'Partying Face': '🥳', 'Red Heart':'❤', 'Relieved Face': '😌', 
                      'Serious Face with Symbols Covering Mouth': '🤬', 'Smiling Face With Halo' : '😇', 
                      'Smiling Face with Heart-Shaped Eyes': '😍', 'Smiling Face with Smiling Eyes': '😊', 'Smirking Face': '😏',
                      'Sneezing Face': '🤧'
                      }
  return emojiNameToUnicode


def convert_img_to_text(arr):
  #arr = ['guguTest.png', 'guguTest2high.png']
  writer = []
  other = []
  data = {}
  borderdata = {}
  data['data'] = []
  borderdata['data'] = []
  mode = None

  for j, img in enumerate(arr):
    # coding=utf-8
    numpyImg = cv2.imread(img)
    if(np.mean(numpyImg) > 127):
      mode = 'Light'
    else:
      mode = 'Dark'
    if(j > 0):
      result = crop(arr[j-1], arr[j])
      final = result if result is not None else cv2.imread(img)
    else:
      final = cv2.imread(img)

    '''DETECT EMOJIS HERE FIRST AND SAVE THEM IN A FOLDER'''
    pathActual = os.path.abspath('../ChatToText/actual.PNG')
    cv2.imwrite(pathActual, final)
    imgFileToBBMapping = detectEmoji(pathActual, mode)
    emojiMappingInImg = {}
    for bb,emoji in imgFileToBBMapping.items():
      if mode == 'Dark':
        cv2.rectangle(final, (bb[0],bb[1]), (bb[2],bb[3]), (0,0,0), -1)
      else:
        cv2.rectangle(final, (bb[0],bb[1]), (bb[2],bb[3]), (255,255,255), -1)
      matchedEmoji, maxScore = findEmojiMatch(emoji)
      if(matchedEmoji != None and maxScore >= 8):
        unicodeEmoji = returnEmojiNameToUnicodeMapping()[matchedEmoji] 
        emojiMappingInImg[bb] = unicodeEmoji
    '''******************'''
    pathActualForNoiseRemoval = os.path.abspath('../ChatToText/noiseRemoved.PNG')
    cv2.imwrite(pathActualForNoiseRemoval, final)
    im = cv2.imread(pathActualForNoiseRemoval,0)
    fixedMode = fixDarkMode(im, mode)

    imbeforenoiseremoval = cv2.imread(pathActual,0)
    fixedModeBeforeNoise = fixDarkMode(imbeforenoiseremoval, mode)

    #since tesserocr accepts PIL images, converting opencv image to pil
    pil_img = Image.fromarray(cv2.cvtColor(fixedModeBeforeNoise, cv2.COLOR_GRAY2RGB))
    #initialize api
    api = tesserocr.PyTessBaseAPI()
    try:
      # set pil image for ocr
      api.SetImage(pil_img)
      # Google tesseract-ocr has a page segmentation methos(psm) option for specifying ocr types
      # psm values can be: block of text, single text line, single word, single character etc.
      # api.GetComponentImages method exposes this functionality
      # function returns:
      # image (:class:`PIL.Image`): Image object.
      # bounding box (dict): dict with x, y, w, h keys.
      # block id (int): textline block id (if blockids is ``True``). ``None`` otherwise.
      # paragraph id (int): textline paragraph id within its block (if paraids is True).
      # ``None`` otherwise.
      boxes = api.GetComponentImages(tesserocr.RIL.TEXTLINE,True)
      # get text
      text = api.GetUTF8Text()
      height, width, c = final.shape
      #threshold = 0.10*width
      minn, maxx = getMinMaxBorder(boxes)
      borderthreshold = 0.07*width 
      inc = int(0.01*width)
      blueTickArea = 0.00128 * width * height
      message = ''
      testMessage = ''
      # iterate over returned list, draw rectangles
      for i, (im,box,_,_) in enumerate(boxes):
        x,y,w,h = box['x'],box['y'],box['w'],box['h']
        # try to skip bluetick boxes
        if(w*h < blueTickArea):
          continue
        # previous bounding box  
        xprev,yprev,wprev,hprev = boxes[i-1][1]['x'], boxes[i-1][1]['y'],boxes[i-1][1]['w'],boxes[i-1][1]['h']

        k = i + 1 #for finding right next textbox
        if(k < len(boxes)):
          # try to skip if text box is bluetick box
          xnext,ynext,wnext,hnext = boxes[k][1]['x'], boxes[k][1]['y'],boxes[k][1]['w'],boxes[k][1]['h']
          area = wnext*hnext
          #print(area, "Area of text box")
          while(area < blueTickArea):
            k = k + 1
            if(k == len(boxes)):
              break
            xnext,ynext,wnext,hnext = boxes[k][1]['x'], boxes[k][1]['y'],boxes[k][1]['w'],boxes[k][1]['h']
            area = wnext*hnext
            #print(area, "Area of text box")
            continue
        
        # print(y, yprev, i, "avnu")
        # print(xprev, threshold, "callu check")
        # print(inc, 'increase')
        # print(borderthreshold, 'border')
        textboxtopleftx = max(0, x-inc)
        textboxtoplefty = max(0, y-inc)
        textboxbottomrightx = min(x+w+inc, width)
        textboxbottomrighty = min(y+h+inc,height)
        nextTextBoxtoplefty = max(0, ynext-inc)
        crop_img = fixedMode[max(0, y-inc):min(y+h+inc,height), max(0, x-inc):min(x+w+inc, width)]
        #cv2.circle(final,(int(threshold), y), 5, (255,0,0), -1)
        #print(crop_img)
        #cv2_imshow(crop_img)
        #cv2.waitKey(0)

        '''******** EMOJI MAPPING ON TEXT LINES START *************'''
        emojisTobeAppended = []
        nextIndividualEmojis = []
        for bb, path in emojiMappingInImg.items():
          emoji = path.split('/')[-1]
          topleftx, toplefty, bottomrightx, bottomrighty = bb
          #print(topleftx, toplefty, bottomrightx, bottomrighty, "emojibox")
          #print( textboxtopleftx , textboxtoplefty, textboxbottomrightx,  textboxbottomrighty)
          #print(nextTextBoxtoplefty, "next textbox topleft y")
          # If emojis lies within current textbox
          if(topleftx >= textboxtopleftx-5 and toplefty >=  textboxtoplefty-5 and bottomrightx <= textboxbottomrightx+5 and bottomrighty <= textboxbottomrighty+5):
            emojisTobeAppended.append(emoji)
          
          # For individual emojis in next line
          if toplefty >= textboxbottomrighty:
            #print("upper")
            #print(nextTextBoxtoplefty, bottomrighty )
            if(nextTextBoxtoplefty >= bottomrighty):
              #print("lower")
              nextIndividualEmojis.append((emoji,bb)) #append all emojis existing between two text boxes
        '''********* EMOJI MAPPING ON TEXT LINES END ***********'''


        extractedInformation = pytesseract.image_to_string(crop_img, lang='eng')
        #print(extractedInformation)
        if('Type a message' in extractedInformation):
          continue
        totalLen = len(extractedInformation)
        stringCheck = extractedInformation[totalLen-8:] if totalLen >= 8 else extractedInformation
        matchAmPm = regexAmPm.search(stringCheck)
        match24hr = regex24hr.search(stringCheck)                  
        
        if(matchAmPm):
          i = extractedInformation.rfind(matchAmPm.groups()[0])
          indexFromLast = totalLen - i
          chopIndex = -indexFromLast-5
          extractedInformation =  extractedInformation[:chopIndex+1]
          
        elif(match24hr):
          i = extractedInformation.rfind(match24hr.groups()[0])
          indexFromLast = totalLen - i
          chopIndex = -indexFromLast
          extractedInformation = extractedInformation[:chopIndex]
          
        

        #second case border detection
        extractedInformation = extractedInformation + ' '.join(emojisTobeAppended)
        if(abs(y-yprev) > borderthreshold):
          #appending single chat bubble
          if(testMessage):
            valleft = abs(xprev - minn)
            valright = abs(maxx-(xprev+wprev))
            if(valleft < valright):
              temp = {}
              temp['name'] = 'other'
              temp['message'] = testMessage.strip()
            else:
              temp = {}
              temp['name'] = 'writer'
              temp['message'] = testMessage.strip()
            borderdata['data'].append(temp)
          
          testMessage = ''
          if(extractedInformation):
            testMessage =  testMessage + ' ' + extractedInformation

          #appending individual emojis after current chat bubble
          if(nextIndividualEmojis):
            xStartEmoji = nextIndividualEmojis[0][1][0] #topleftx for first emoji in the list
            xEndEmoji = nextIndividualEmojis[-1][1][2] #bottomrightx for last emoji in list
            valleft = abs(xStartEmoji - minn)
            valright = abs(maxx-(xEndEmoji))
            emojiString = ' '.join([pair[0] for pair in nextIndividualEmojis])
            if(valleft < valright):
              other.append(emojiString)
              temp = {}
              temp['name'] = 'other'
              temp['message'] = emojiString.strip()
            else:
              writer.append(emojiString)
              temp = {}
              temp['name'] = 'writer'
              temp['message'] = emojiString.strip()
            borderdata['data'].append(temp)
        
        else:
          if(extractedInformation):
            testMessage =  testMessage + ' ' + extractedInformation
          continue
      

        # if(message):
        #   print('avani************')
        #   if(x < threshold):
        #     other.append(message)
        #     temp = {}
        #     temp['name'] = 'other'
        #     temp['message'] = message
        #     temp['time'] = t
        #   else:
        #     writer.append(message)
        #     temp = {}
        #     temp['name'] = 'writer'
        #     temp['message'] = message
        #     temp['time'] = t
        #   data['data'].append(temp)
        #   print(message)
        # message = ''

        #cv2.rectangle(final, (x,y), (x+w,y+h), color=(0,255,0))
      
      if(testMessage):
        valleft = abs(x- minn)
        valright = abs(maxx-(x+w))
        if(valleft < valleft):
          temp = {}
          temp['name'] = 'other'
          temp['message'] = testMessage.strip()
        else:
          temp = {}
          temp['name'] = 'writer'
          temp['message'] = testMessage.strip()
        borderdata['data'].append(temp)
      testMessage = '' 
      #check if last line contains individual emojis
      lastLineEmoji = []
      for bb, path in emojiMappingInImg.items():
          emoji = path.split('/')[-1]
          topleftx, toplefty, bottomrightx, bottomrighty = bb
          if toplefty > textboxbottomrighty:
              lastLineEmoji.append((emoji, bb))
      # append if individual emojis exist in last lines
      if(lastLineEmoji):
        xStartEmoji = lastLineEmoji[0][1][0] #topleftx for first emoji in the list
        xEndEmoji = lastLineEmoji[-1][1][2] #bottomrightx for last emoji in list
        valleft = abs(xStartEmoji - minn)
        valright = abs(maxx-(xEndEmoji))
        lastLineEmojiString = ' '.join([pair[0] for pair in lastLineEmoji])
        if(valleft < valright):
          other.append(lastLineEmojiString)
          temp = {}
          temp['name'] = 'other'
          temp['message'] = lastLineEmojiString.strip()
          #temp['time'] = t
        else:
          writer.append(lastLineEmojiString)
          temp = {}
          temp['name'] = 'writer'
          temp['message'] = lastLineEmojiString.strip()
          #temp['time'] = t
        borderdata['data'].append(temp)
    finally:
      api.End()
  
  json_data = json.dumps(borderdata)
  return json_data
  #print(data)
  #print(other)
  #print(writer)

def main(arr):
  print(convert_img_to_text(arr))


if __name__ == '__main__':
  arr = ast.literal_eval( sys.argv[1] )
  main(arr)
  


