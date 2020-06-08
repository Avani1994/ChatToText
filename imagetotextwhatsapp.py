# -*- coding: utf-8 -*-
"""ImagetotextWhatsapp.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1lm4B7oRazaiLVL01brl7WZlVuP5iMU-b
"""

# !sudo apt install tesseract-ocr

# !pip3 install pytesseract

# !sudo apt-get install libleptonica-dev libtesseract-dev

# !pip3 install tesserocr

import pytesseract
import shutil
import os
import random
import tesserocr
import cv2
from google.colab.patches import cv2_imshow
import re 
from pylab import array, plot, show, axis, arange, figure, uint8 
from skimage.measure import compare_ssim
import imutils
import numpy as np
import sys, ast
try:
    from PIL import Image
except ImportError:
    import Image
import json

from google.colab import files






regextime = re.compile(r'((([0|'']?[1-9]|1[0-2])(:|\.|-)[0-5][0-9]((:|\.)[0-5][0-9])?( )?(AM|am|aM|Am|PM|pm|pM|Pm))|(([0]?[0-9]|1[0-9]|2[0-3])(:|\.)[0-5][0-9]((:|\.)[0-5][0-9])?))') 
regexAmPm = re.compile(r'(([\d])(' '|'')(.m|.M| .m| .M]))')
regex24hr = re.compile(r'(((''|[\d])[\d])(:|\.|-)([\d][\d]))')



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
    imgorig1 = cv2.imread(im1, cv2.IMREAD_UNCHANGED)
    imgorig2 = cv2.imread(im2, cv2.IMREAD_UNCHANGED)
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
      print("Not equal")
      return(None)

def convert_img_to_text(arr):
  #arr = ['guguTest.png', 'guguTest2high.png']
  writer = []
  other = []
  data = {}
  borderdata = {}
  data['data'] = []
  borderdata['data'] = []

  for i, img in enumerate(arr):
    # coding=utf-8
    
    if(i > 0):
      result = crop(arr[i-1], arr[i])
      final = result if result is not None else cv2.imread(img, cv2.IMREAD_UNCHANGED)
    else:
      final = cv2.imread(img, cv2.IMREAD_UNCHANGED)

    # since tesserocr accepts PIL images, converting opencv image to pil
    pil_img = Image.fromarray(cv2.cvtColor(final, cv2.COLOR_BGR2RGB))
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
      threshold = 0.10*width
      borderthreshold = 0.07*width 
      inc = int(0.01*width)
      message = ''
      testMessage = ''
      # iterate over returned list, draw rectangles
      for i, (im,box,_,_) in enumerate(boxes):
        x,y,w,h = box['x'],box['y'],box['w'],box['h']
        xprev,yprev,_,_ = boxes[i-1][1]['x'], boxes[i-1][1]['y'],boxes[i-1][1]['w'],boxes[i-1][1]['h']
        # print(y, yprev, i, "avnu")
        # print(xprev, threshold, "callu check")
        # print(inc, 'increase')
        # print(borderthreshold, 'border')
        crop_img = final[max(0, y-inc):min(y+h+inc,height), max(0, x-inc):min(x+w+inc, width)]
        #cv2.circle(final,(int(threshold), y), 5, (255,0,0), -1)
        #print(crop_img)
        cv2_imshow(crop_img)
        cv2.waitKey(0)
        extractedInformation = pytesseract.image_to_string(crop_img)
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
        if(abs(y-yprev) > borderthreshold):
          if(testMessage):
            if(xprev < threshold):
              temp = {}
              temp['name'] = 'other'
              temp['message'] = testMessage
            else:
              temp = {}
              temp['name'] = 'writer'
              temp['message'] = testMessage  
            borderdata['data'].append(temp)
          
          testMessage = ''
          if(extractedInformation):
            testMessage =  testMessage + ' ' + extractedInformation
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
        if(x < threshold):
          temp = {}
          temp['name'] = 'other'
          temp['message'] = testMessage
        else:
          temp = {}
          temp['name'] = 'writer'
          temp['message'] = testMessage
        borderdata['data'].append(temp)
      testMessage = ''   
    finally:
      api.End()
  
  json_data = json.dumps(borderdata)
  return json_data
  #print(data)
  # print(other)
  # print(writer)

if __name__ == '__main__':
  arr = ast.literal_eval( sys.argv[1] )
  return(convert_img_to_text(arr))  
