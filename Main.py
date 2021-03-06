import cv2
import numpy as np
import os
from gpiozero import LED
from time import sleep
from guizero import App, PushButton, Text
import sys
from PIL import Image
import RPi.GPIO as GPIO 
from mfrc522 import SimpleMFRC522 


recognizer = cv2.face.LBPHFaceRecognizer_create()
recognizer.read('trainer/trainer.yml')
cascadePath = "haarcascade_frontalface_default.xml"
faceCascade = cv2.CascadeClassifier(cascadePath);

font = cv2.FONT_HERSHEY_SIMPLEX

def exitApp():
    sys.exit()
    cv2.destroyAllWindows()

#indicate id counter
id = 0

#for gpio pin to connect solenoid
led = LED(13)


names = ['None', 'Zion', 'Paula', 'Ilza', 'Gabriel', 'Williams', 'Yetunde', 'Violin', 'Laila', 'Praise', 'Bode', 'Micheal'] 
def NewUser():
    reader = SimpleMFRC522() 
    try:
            idNos = [114225200613, 961239530875]
            id, text = reader.read()         
            #print(id)
            if id in idNos:
                print(id)
                print("\n [INFO] start face detector ...")
                cam = cv2.VideoCapture(0)
                cam.set(3, 640) # set video width
                cam.set(4, 480) # set video height
                face_detector = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')

                # For each person, enter one numeric face id
                face_id = input('\n enter user id end and press <Enter> ==>  ')
                print("\n [INFO] Initializing face capture. Look at the camera and wait ...")
                # Initialize individual sampling face count
                count = 0
                while(True):
                    ret, img = cam.read()
                    img = cv2.flip(img, -1) # flip video image vertically
                    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                    faces = face_detector.detectMultiScale(gray, 1.3, 5)

                    for (x,y,w,h) in faces:
                        cv2.rectangle(img, (x,y), (x+w,y+h), (255,0,0), 2)     
                        count += 1

                        # Save the captured image into the datasets folder
                        cv2.imwrite("dataset/User." + str(face_id) + '.' + str(count) + ".jpg", gray[y:y+h,x:x+w])

                        cv2.imshow('image', img)

                    k = cv2.waitKey(50) & 0xff # Press 'ESC' for exiting video
                    if k == 27:
                        break
                    elif count >= 30: # Take 30 face samples and stop video
                        break
                    # Do a bit of cleanup
                    #print("\n [INFO] Exiting Program and cleanup stuff")
                    cam.release()
                    cv2.destroyAllWindows()

                #Face Training
                print("\n [INFO] Please wait...Initializing...")
                # Path for face image database
                path = 'dataset'
                recognizer = cv2.face.LBPHFaceRecognizer_create()   #LBPH (LOCAL BINARY PATTERNS HISTOGRAMS)
                detector = cv2.CascadeClassifier('haarcascades/haarcascade_frontalface_default.xml');
                # function to get the images and label data
                def getImagesAndLabels(path):
                    imagePaths = [os.path.join(path,f) for f in os.listdir(path)]     
                    faceSamples=[]
                    ids = []
                    for imagePath in imagePaths:
                        PIL_img = Image.open(imagePath).convert('L') # convert it to grayscale
                        img_numpy = np.array(PIL_img,'uint8')
                        id = int(os.path.split(imagePath)[-1].split(".")[1])
                        faces = detector.detectMultiScale(img_numpy)
                        for (x,y,w,h) in faces:	
                            faceSamples.append(img_numpy[y:y+h,x:x+w])
                            ids.append(id)
                    return faceSamples,ids

            print ("\n [INFO] Training faces. It will take a few seconds. Wait ...")
            faces,ids = getImagesAndLabels(path)
            recognizer.train(faces, np.array(ids))

            # Save the model into trainer/trainer.yml
            recognizer.write('trainer/trainer.yml') # recognizer.save() worked on Mac, but not on Pi

            # Print the numer of faces trained and end program
            print("\n [INFO] {0} Capture Successful!".format(len(np.unique(ids))))

                    
            else:
                print('rfid not found')
            print(text) 
    finally:         
            GPIO.cleanup()


def ExistingUser():
    
    # Initialize and start realtime video capture
    cam = cv2.VideoCapture(0)
    cam.set(3, 640) # set video widht
    cam.set(4, 480) # set video height

    # Define min window size to be recognized as a face
    minW = 0.1*cam.get(3)
    minH = 0.1*cam.get(4)

    while True:
        ret, img =cam.read()
        #img = cv2.flip(img, -1) # Flip vertically
        gray = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
    
        faces = faceCascade.detectMultiScale( 
        gray,
        scaleFactor = 1.2,
        minNeighbors = 5,
        minSize = (int(minW), int(minH)),
       )

        for(x,y,w,h) in faces:
            cv2.rectangle(img, (x,y), (x+w,y+h), (0,255,0), 2)
            id, confidence = recognizer.predict(gray[y:y+h,x:x+w])

            # Check if confidence is less them 100 ==> "0" is perfect match 
            if (confidence < 100):
                id = names[id]
                confidence = "  {0}%".format(round(100 - confidence))
		cam.release()
		cv2.destroyAllWindows()
                #led.on()
                #sleep(5)        
                #led.off() #door locks after 3seconds
            else:
                id = "unknown"
                confidence = "  {0}%".format(round(100 - confidence))
        
            cv2.putText(img, str(id), (x+5,y-5), font, 1, (255,255,255), 2)
            #cv2.putText(img, str(confidence), (x+5,y+h-5), font, 1, (255,255,0), 1)  
    
        cv2.imshow('camera',img) 

        k = cv2.waitKey(10) & 0xff # Press 'ESC' for exiting video
        if k == 27:
            break

    # Do a bit of cleanup
    print("\n [INFO] Exiting Program and cleanup stuff")
    cam.release()
    cv2.destroyAllWindows()

app = App('Access Control System', bg = "#02075d", height = 600, width = 800)

ledButton = PushButton(app, command=NewUser, text="NEW USER", align="top",width = 25)
ledButton.text_size = 25
ledButton.bg = 'lightblue'

ledButton = PushButton(app, command=ExistingUser, text="EXISTING USERS", width = 25)
ledButton.text_size = 25
ledButton.bg = 'lightblue'

exitButton = PushButton(app, command=exitApp, text="EXIT", width = 25)
exitButton.text_size = 25
ledButton.bg = 'lightblue'

designBy = Text(app, text="Designed by Olaleye Gabriel and Oladiran Zion", align="bottom")
designBy.text_size = 10

app.display()

