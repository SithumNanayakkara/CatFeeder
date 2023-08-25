import RPi.GPIO as GPIO
import time
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BOARD)
GPIO.setup(29,GPIO.IN)

while True:
 i = GPIO.input(29)
 if i==0:
  print ("No motion detected!")
  time.sleep(0.1)
 elif i==1:
  print ("Motion detected!")
  time.sleep(0.1)
