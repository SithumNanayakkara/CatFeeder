#!/var/www/CatFeeder/catenv/bin/python
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

# Find config file
configFilePath = '/var/www/CatFeeder/app.cfg'
configParser = configparser.RawConfigParser()
configParser.read(configFilePath)

# Read in config variables
pirsensorGPIO = configParser.get('CatFeederConfig', 'PIR_GPIO_Pin')
hopperGPIO = configParser.get('CatFeederConfig', 'Servo_GPIO_Pin')
hopperTime = configParser.get('CatFeederConfig', 'Servo_Open_Time')
LOG_WalkInService_FILENAME = configParser.get('CatFeederConfig', 'Log_WalkInService_Filename')
delayBetweenButtonPushes = configParser.get('CatFeederConfig', 'Seconds_Delay_After_Button_Push')

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

print("End Start up. Starting while loop")
print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
while True:
    pirValue = GPIO.input(pirSensor)

    if pirValue ==0:
     
        print ("No motion detected!")
        time.sleep(0.1)
  
    elif pirValue ==1:
     
        print ("Motion detected!")
        motionDetect = commonTasks.print_to_LCDScreen(">>Motion Detected!<<")
        time.sleep(2)

    if killer.kill_now: break
print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
print("End of the program loop. Killed gracefully")
print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
