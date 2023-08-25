# import required libraries
import RPi.GPIO as GPIO
import time
import cv2

GPIO.setwarnings(False)

# Set GPIO numbering mode
GPIO.setmode(GPIO.BOARD)

# Set pin 11 as an output, and define as servo as PWM pin 11
GPIO.setup(11,GPIO.OUT)
servo = GPIO.PWM(11,50) # pin 5 for micro servo, pulse 50Hz

# Set pin 29 as an input, and define as PIR as pin 29
GPIO.setup(29,GPIO.IN)


# Start PWM running, with value of 0 (pulse off)
servo.start(0)

#Define the trained XML classifiers
face_cascade = cv2.CascadeClassifier('haarcascades/haarcascade_frontalcatface.xml')

#Define timeout
timeout = 60   # [seconds]

while True:
    pir = GPIO.input(29) # pin 29 for PIR sensor
    if pir ==0:
     
        print ("No motion detected!")
        time.sleep(0.1)
  
    elif pir ==1:
     
        print ("Motion detected!")
  
        # capture frames from a camera 
        cap = cv2.VideoCapture(0)
        
        #start timeout timer if capturing has been initialized
        timeout_start = time.time()
        
        # loop runs till timeout
        while time.time() < timeout_start + timeout:
            
            # reads frames from a camera 
            ret, img = cap.read() 
  
            # convert to gray scale of each frames 
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) 
  
            # Detects faces of different sizes in the input image 
            faces = face_cascade.detectMultiScale(gray, 1.12, 5) 
  
            for (x,y,w,h) in faces: 
                # To draw a rectangle in a face 
                cv2.rectangle(img,(x,y),(x+w,y+h),(255,255,0),2) 
                roi_gray = gray[y:y+h, x:x+w] 
                roi_color = img[y:y+h, x:x+w]
                
            # Display an image in a window 
            cv2.imshow('img',img)
                
            if len(faces) > 0:
                print("Cat face detected")
                try:

                    #Turn the servo to open
                    angle = 35
                    servo.ChangeDutyCycle(2+(angle/18))
                    print("Dispensing Food!")
                    time.sleep(0.5)
                    servo.ChangeDutyCycle(0)
                    time.sleep(3)
                    #Turn the servo to close
                    angle = 0
                    servo.ChangeDutyCycle(2+(angle/18))
                    time.sleep(0.5)
                    servo.ChangeDutyCycle(0)

                finally:
                    #Clean things up at the end
                    servo.stop()
                    GPIO.cleanup()
                    print("Stopping dispensing")
                
            else:
                print("No cat face detected")
               
            
            # Wait for Esc key to stop 
            k = cv2.waitKey(30) & 0xff
            if k == 27:
                break

        # Close the window 
        cap.release()
  
  





