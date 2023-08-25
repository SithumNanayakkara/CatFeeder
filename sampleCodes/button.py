import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BOARD)

buttonPin = 37

GPIO.setup(buttonPin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

while True:
  buttonState = GPIO.input(buttonPin)
  if buttonState == False:
    print("high")
  else:
    print("Low")