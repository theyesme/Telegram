import time
import string
import random
import configparser as cp
#import logging
import os
import sys
import time
import math

from flask import Flask, request, jsonify
from requests.utils import quote
from base64 import encodebytes

import numpy as np

from skimage import io
from skimage import color
from skimage.morphology import flood_fill
from skimage import filters

#from skimage import data #For debugging
#import skimage #For debugging

from PIL import Image
from io import BytesIO

import googlemaps

#>>!
class logging:
        def debug (str):
            print (str)
        def info  (str):
                print (str)
        
        



app = Flask(__name__)
#app = Flask(__name__, static_folder='') 

app.config["JSON_SORT_KEYS"] = False

#Need to check if meters per pixel depend on latitude https://gis.stackexchange.com/questions/7430/what-ratio-scales-do-google-maps-zoom-levels-correspond-to
#metersPerPixel = { #Measured the area of 1317 Mettler Road (20.26 * 15.46 + 2.77 * 9.07 = 338.3435) and counted pixels for different zoom values
#        "21": 0.00320896364,
#        "20": 0.01280973384,
#        "19": 0.0510245061,
#        "18": 0.20296550689,
#        "17": 0.79986643026
#    }


@app.route("/", methods=['GET','POST'])
def health():
    #parser = cp.ConfigParser(); #For debugging
    #parser.read('config.properties')
    #configFile = {section: dict(parser.items(section)) for section in parser.sections()}
    #loggingLevel=int(configFile["Logging"]["level"])
    #logging.basicConfig(stream=sys.stdout, level=loggingLevel)
    #logging.info (">> health - OK")
    return jsonify({"timestamp": time.time() * 1000})


@app.route("/roofinfo", methods=['POST'])
def roof_info():
    debuggingInfo = "" #For debugging
    start_time = time.time()
    parser = cp.ConfigParser();
    parser.read('config.properties')
    configFile = {section: dict(parser.items(section)) for section in parser.sections()}
    
    
    #>>!loggingLevel=int(configFile["Logging"]["level"])
    #>>!logging.basicConfig(stream=sys.stdout, level=loggingLevel)
    
    
    json_data = request.json
    
    
    if "address" not in json_data:
        return jsonify({"error": True, "message": "address is required"})

    if "imageSize" not in json_data:
        return jsonify({"error": True, "message": "imageSize is required"})

    if "testMode" not in json_data: #For debugging
        testMode = "0"
    else:
        testMode = json_data['testMode']; 

    fileName1 = generate_filename().replace(".png", "-1.png"); 
    fileName2 =  fileName1.replace("-1.png","-2.png");
    fileName3 = fileName1.replace("-1.png","-3.png");
    fileName4 = fileName1.replace("-1.png","-4.jpg");
    
    maxArea = int(configFile["AreaCalculation"]["max_area"])
    multiplier = float (configFile["AreaCalculation"]["multiplier"]) 
    
    location = json_data['address'];
    location_url = quote(location)
    
    #defaultPicSize= int (configFile["GoogleMaps"]["default_size"])
    #picSize = defaultPicSize
            
    #try:
    #    picSize= int(json_data['imageSize'])
    #    if (picSize > defaultPicSize) or (picSize < 0):
    #        picSize = defaultPicSize
    #except:
    #    picSize = defaultPicSize
    #
    
    picSizeX = int(configFile["ImageParams"]["pic_size_x"])
    picSizeY = int(configFile["ImageParams"]["pic_size_y"])
    midX = int(picSizeX) /2
    midY = int(picSizeY) /2
    zoom = configFile["GoogleMaps"]["zoom"]
    metersPerPixelRatio = float(configFile["AreaCalculation"]["meters_per_pixel_ratio"])
    keepImages = int(configFile["Logging"]["keep_images_on_server"])
    
     
    # urlBuildings = "https://maps.googleapis.com/maps/api/staticmap?key=AIzaSyASCbc9fjpscG22k4_sIvwHibUU66MflNE&zoom=20&size=640x640&map_id=d70600c225eb25e5&center=" + location_url #Use Map Style with everything off and gray buildings
    # satUrlBuildings = "https://maps.googleapis.com/maps/api/staticmap?center=" + location_url +"&key=AIzaSyCPMtFukbEgOPJRfD6HXJ7j03j0h_z72lE&zoom=20&maptype=satellite&size=640x640"
    
    logging.debug ("Time 1 (initialized):" + str(time.time() - start_time))
    
    googleKey = configFile["GoogleMaps"]["api_key"]  
    latitude = None
    try:
        gmaps = googlemaps.Client(googleKey)
        geocode_result = gmaps.geocode(location)
        latitude = float(geocode_result[0]['geometry']['location']['lat'])
    except Exception as e:
        logging.info ("Error. Address not resolved. Exception message: " + str(e))
        return jsonify({"error": True, "message": "Address not resolved" })
    
    urlBuildings = configFile["GoogleMaps"]["url"] + "?map_id=" + configFile["GoogleMaps"]["map_id"] +"&key=" + googleKey  + "&zoom=" + configFile["GoogleMaps"]["zoom"] + "&size=" + str(picSizeX) + "x" + str(picSizeY) + "&center=" + location_url 
    satUrlBuildings = configFile["GoogleMaps"]["url"] + "?maptype=satellite"+"&key=" + googleKey  + "&zoom=" + configFile["GoogleMaps"]["zoom"] + "&size=" + str(picSizeX) + "x" + str(picSizeY) + "&center=" + location_url  
    
    satImgBuildings = io.imread(satUrlBuildings)
    io.imsave(fileName1, satImgBuildings)
    
    imgBuildings = io.imread(urlBuildings)
    
    if (keepImages == 1): #For debugging
        fileName0 =  fileName1.replace("-1.png","-0.png");
        io.imsave (fileName0, imgBuildings)
    
    logging.debug ("Time 2: (got info from Google)" + str(time.time() - start_time))
    
    #if (testMode == "testImgBuildings"):  #For debugging
    #    io.imsave(fileName2, imgBuildings)
    #    encoded_img2 = get_response_image(fileName2)
    #    if (keepImages != 1):
    #        os.remove (fileName1)
    #        os.remove (fileName2)
    #    return {
    #        "square": -1,
    #        "image": encoded_img2
    #   }
    

    #debuggingInfo += " imgBuildings.shape:" + str(imgBuildings.shape) 
    #debuggingInfo += " skimage.__version__:" + str(skimage.__version__)
     
    #if (testMode == "testImgBuildings"):  #For debugging
    #    binary_imageBuildings = data.coins()
    #else:
    gray_imgBuildings = color.rgb2gray(imgBuildings)
    imageFill = flood_fill (gray_imgBuildings,(int(midY),int(midX)) ,255)
    binary_imageBuildings = np.where(imageFill > np.mean(imageFill), 0.0, 1.0)
    
    io.imsave(fileName2, binary_imageBuildings)
    
    makeBorderMask(binary_imageBuildings, int(configFile["BorderParams"]["thickness"]), fileName3)
        
    logging.debug ("Time 3 (created binary mask of a central building):" + str(time.time() - start_time))
        
    fillRed = int(configFile["FillParams"]["red"])
    fillGreen = int(configFile["FillParams"]["green"])
    fillBlue = int(configFile["FillParams"]["blue"])
    
    makePng(fileName2, fillRed, fillGreen, fillBlue, int(configFile["FillParams"]["transparency"])) #make semitranparent fill
    makePng(fileName3, int(configFile["BorderParams"]["red"]), int(configFile["BorderParams"]["green"]), int(configFile["BorderParams"]["blue"]), 255) #make untransparent border
    
    mergeImages (fileName1, fileName2, fileName4) #put a semitransparent fill on a sat image  
    mergeImages (fileName4, fileName3, fileName4) #put a border on a sat image 

    logging.debug ("Time 4 (merged all images and created a final image):" + str(time.time() - start_time))
    
    house_area = countArea (metersPerPixelRatio, latitude, zoom, multiplier, binary_imageBuildings, 0)
    if house_area >= maxArea:
        
        logging.info ("Returned error because house_area (" + str(house_area) + ") > max_area. Requested location: " + urlBuildings + " If keep_images_on_server=true in config, you can find an image on server: " + fileName4)
        if (keepImages != 1):
            os.remove(fileName1)
            os.remove(fileName2)
            os.remove(fileName3)
            os.remove(fileName4)
        return jsonify({"error": True, "message": "Area not calculated"})

    logging.debug ("Time 5 (calculated area of a central building):" + str(time.time() - start_time))
    
    encoded_img4 = get_response_image(fileName4)
    
    logging.info("Calculated area (" + str(house_area) + "). Requested location: " + urlBuildings);
    if (keepImages != 1):
        os.remove(fileName1)
        os.remove(fileName2)
        os.remove(fileName3)
        os.remove(fileName4)
    
    if (testMode == "testImageLinks"):
        return {
            "square": house_area,
            "image": fileName4
        }
        
    return {
        "square": house_area,
        "image": encoded_img4
        #"debug": debuggingInfo    #For debugging
    }


def countArea (metersPerPixelRatio, latitude, zoom, multiplier, pixelArray, pixelColor):
    house_pixels = 0
    for row in pixelArray:
        for pixel in row:
            if (pixel == pixelColor):
                house_pixels = house_pixels + 1
              
    house_area = house_pixels * pow(metersPerPixelRatio * math.cos(latitude*math.pi/180)/math.pow(2, float(zoom)),2)
    return house_area * multiplier
    

def mergeImages (imageName1, imageName2, imageName3):
    image1 = Image.open(imageName1)
    image2 = Image.open(imageName2)
    new_image = Image.new('RGBA',(image1.size[0], image1.size[1]), (255,255,255))
    new_image.paste(image1,(0,0))
    new_image.paste(image2,(0,0), image2)
    
    new_image = new_image.convert('RGB')
    new_image.save(imageName3,"JPEG")

def makeBorderMask (array, thickness, fileName):
    new_array = filters.sobel(array)
    rowCount = -1
    colCount = 0
    for row in new_array:
        rowCount = rowCount + 1
        colCount = 0
        for pixel in row:
            if (pixel == 0):
                new_array[rowCount, colCount] = 1
            if (pixel != 0):
                new_array[rowCount, colCount] = 0
                for k in range (1, thickness): 
                    if ((colCount - k) >= 0):
                        new_array [rowCount, colCount - k] = 0
            colCount = colCount + 1
    io.imsave(fileName, new_array)

def makePng(myimage, red, green, blue, transparency):
    img = Image.open(myimage)
    img = img.convert("RGBA")
    pixdata = img.load()
    width, height = img.size
    
    for y in range(height):
        for x in range(width):
            if pixdata[x, y] == (0, 0, 0, 255):
                pixdata[x, y] = (red, green, blue, transparency) #change untransparent black to (un)transparent colored fill
            if pixdata[x, y] == (255, 255, 255, 255):
                pixdata[x, y] = (255, 255, 255, 0) #change untransparent white to transparent white
    img.save(myimage, "PNG")

def generate_filename(size=12, chars=string.ascii_lowercase + string.digits):
 return ''.join(random.choice(chars) for _ in range(size)) + ".png"


def get_response_image(image_path):
    pil_img = Image.open(image_path, mode='r') # reads the PIL image
    byte_arr = BytesIO()
    pil_img.save(byte_arr, format='PNG') # convert the PIL image to byte array
    encoded_img = encodebytes(byte_arr.getvalue()).decode('ascii') # encode as base64
    return encoded_img

def create_app():
   return app