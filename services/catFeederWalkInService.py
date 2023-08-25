#!/usr/bin/python
import sys

sys.path.extend(['/var/www/CatFeeder'])
import logging.handlers
import argparse
import time
import signal
import commonTasks
import RPi.GPIO as GPIO
import datetime
import configparser
import os
import cv2

# Find config file
configFilePath = '/var/www/CatFeeder/app.cfg'
configParser = configparser.RawConfigParser()
configParser.read(configFilePath)

# Read in config variables
pirsensorGPIO = configParser.get('CatFeederConfig', 'PIR_GPIO_Pin')
servoGPIO = configParser.get('CatFeederConfig', 'Servo_GPIO_Pin')
servoOpenTime = configParser.get('CatFeederConfig', 'Servo_Open_Time')
LOG_WalkInService_FILENAME = configParser.get('CatFeederConfig', 'Log_WalkInService_Filename')
delayBetweenWalkIns = configParser.get('CatFeederConfig', 'Seconds_Delay_After_WalkIn')
lookingForCatSeconds = configParser.get('CatFeederConfig', 'Seconds_Wait_For_Cat')

# Define and parse command line arguments
parser = argparse.ArgumentParser(description="My simple Python service")
parser.add_argument("-l", "--log", help="file to write log to (default '" + LOG_WalkInService_FILENAME + "')")

# If the log file is specified on the command line then override the default
args = parser.parse_args()
if args.log:
    LOG_FILENAME = args.log

# Configure logging to log to a file, making a new file at midnight and keeping the last 3 day's data
# Give the logger a unique name (good practice)
logger = logging.getLogger(__name__)
# Set the log level to LOG_LEVEL
logger.setLevel(logging.INFO)  # Could be e.g. "DEBUG" or "WARNING")
# Make a handler that writes to a file, making a new file at midnight and keeping 3 backups
handler = logging.handlers.TimedRotatingFileHandler(LOG_WalkInService_FILENAME, when="midnight", backupCount=3)
# Format each log message like this
formatter = logging.Formatter('%(asctime)s %(levelname)-8s %(message)s')
# Attach the formatter to the handler
handler.setFormatter(formatter)
# Attach the handler to the logger
logger.addHandler(handler)


# Make a class we can use to capture stdout and sterr in the log
class MyLogger(object):
    def __init__(self, logger, level):
        """Needs a logger and a logger level."""
        self.logger = logger
        self.level = level

    def write(self, message):
        # Only log if there is a message (not just a new line)
        if message.rstrip() != "":
            self.logger.log(self.level, message.rstrip())


# Replace stdout with logging to file at INFO level
sys.stdout = MyLogger(logger, logging.INFO)
# Replace stderr with logging to file at ERROR level
sys.stderr = MyLogger(logger, logging.ERROR)


class GracefulKiller:
    kill_now = False

    def __init__(self):
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)

    def exit_gracefully(self, signum, frame):
        self.kill_now = True

print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
print("Starting up")

print("Create Gracekiller class")
killer = GracefulKiller()

print("Set up sensor for While Loop")
pirSensor = int(pirsensorGPIO)
GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)
GPIO.cleanup(pirSensor)
GPIO.setup(pirSensor, GPIO.IN)

#Define the trained XML classifiers
face_cascade = cv2.CascadeClassifier('/var/www/CatFeeder/haarcascades/haarcascade_frontalcatface.xml')

print("End Start up. Starting while loop")
print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
while True:
    pirValue = GPIO.input(pirSensor)

    if pirValue ==0: #No motion detected!
        time.sleep(1)
  
    elif pirValue ==1: #Motion detected!
        motionDetectDatetime = datetime.datetime.now()
        print("Motion was detected at " + str(motionDetectDatetime))
        motionDetect = commonTasks.print_to_LCDScreen("Motion Detected!")
        time.sleep(1)
        print("Message Display return status: " + str(motionDetect))
        
        # capture frames from the camera 
        cap = cv2.VideoCapture(0)
        
        #start timeout timer if capturing has been initialized
        timeout_start = time.time()

        catfound = False

        looking = commonTasks.print_to_LCDScreen("Looking for cat")
        time.sleep(1)
        print("Message Display return status: " + str(looking))

        # loop runs till timeout specified by Seconds_Wait_For_Cat in app.cfg or till cat is found
        while time.time() < timeout_start + int(lookingForCatSeconds) and not(catfound) :
            print("While loop started - looking for cat")
            print("Time left in loop: " + str(time.time() - (timeout_start + int(lookingForCatSeconds)))+ "s")
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
                catfound = True
                catDetectDatetime = datetime.datetime.now()
                print("Cat detected at " + str(catDetectDatetime))
                motionDetect = commonTasks.print_to_LCDScreen("Cat Detected!")
                time.sleep(1)
                print("Message Display return status: " + str(motionDetect))
                lastFeedDateCursor = commonTasks.db_get_last_feedtimes(1)
                lastFeedDateString = lastFeedDateCursor[0][0]
                lastFeedDateObject = datetime.datetime.strptime(lastFeedDateString, "%Y-%m-%d %H:%M:%S")
                print("Last feed time in DB was at " + str(lastFeedDateObject))
                
                tdelta = catDetectDatetime - lastFeedDateObject
                print("Difference in seconds between two: " + str(tdelta.seconds))

                if tdelta.seconds < int(delayBetweenWalkIns):
                    print("Feed times closer than " + str(delayBetweenWalkIns) + " seconds. Holding off for now.")
                    remainingTime = int(delayBetweenWalkIns) - tdelta.seconds
                    holdingOff = commonTasks.print_to_LCDScreen("Too Frequent! \nWait for: " + str(remainingTime) + "s")
                    time.sleep(1)
                    print("Message Display return status: " + str(holdingOff))
                else:
                    turn = commonTasks.rotate_servo(servoGPIO, servoOpenTime)
                    print("End Hopper return status: " + str(turn))
                    dblog = commonTasks.db_insert_feedtime(catDetectDatetime, 6)
                    print("End DB Insert return status: " + str(dblog))
                    feeding = commonTasks.print_to_LCDScreen("Feeding!")
                    print("End Message Display return status: " + str(feeding))
                    time.sleep(1)
            else:
                time.sleep(0.5)
                catfound = False

        print("Exiting while loop - looking for cat")
        if not(catfound):
            print("No cat face detected for: " + lookingForCatSeconds + "s")
            notFound = commonTasks.print_to_LCDScreen("No cat detected!\nLooked for: " + int(lookingForCatSeconds) +"s")
            time.sleep(1)

        print("End Message Display return status: " + str(notFound))
        updatescreen = commonTasks.print_to_LCDScreen(commonTasks.get_last_feedtime_string())
        if updatescreen != 'ok':
            print('Warning. Screen feedtime did not update: ' + str(updatescreen))

        # Close the video capture 
        cap.release()
             
    if killer.kill_now: break
print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
print("End of the program loop. Killed gracefully")
print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
