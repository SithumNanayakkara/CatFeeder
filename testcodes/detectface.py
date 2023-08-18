# import required libraries
import cv2

# read the input image
img = cv2.imread('../images/cat.jpg')

# convert the input image to grayscale
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

# read the haarcascade to detect cat faces
#cat_cascade = cv2.CascadeClassifier('haarcascades/haarcascade_frontalcatface_extended.xml')
cat_cascade = cv2.CascadeClassifier('../haarcascades/haarcascade_frontalcatface.xml')

# Detects cat faces in the input image
faces = cat_cascade.detectMultiScale(gray, 1.12, 5)
print('Number of detected cat faces:', len(faces))

# if atleast one cat face id detected
if len(faces) > 0:
   print("Cat face detected")
   for (x,y,w,h) in faces:

      # To draw a rectangle in a face
      cv2.rectangle(img,(x,y),(x+w,y+h),(0,255,255),2)
      cv2.putText(img, 'Zorro', (x, y-3),
      cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,0), 1)
else:
   print("No cat face detected")

scaled_down= cv2.pyrDown(img)
scaled_down2= cv2.pyrDown(scaled_down)

# Display an image in a window
cv2.imshow('Cat Image',scaled_down2)
cv2.waitKey(0)
cv2.destroyAllWindows()
