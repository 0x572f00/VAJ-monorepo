import cv2
import sys
import datetime as dt
from time import sleep
cascPath = "cascade.xml"
faceCascade = cv2.CascadeClassifier(cascPath)
video_capture = cv2.VideoCapture(0)
anterior = 0
while True:
    if not video_capture.isOpened():
        print('Невозможно загрузить видео с камеры!')
        sleep(5)
        pass
    ret, frame = video_capture.read()
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = faceCascade.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=5,
        minSize=(30, 30)
    )
    for (x, y, w, h) in faces:
        cv2.rectangle(
            frame,
            (x, y),
            (x+w, y+h),
            (0, 255, 0),
            2
        )
    if anterior != len(faces):
        anterior = len(faces)
    cv2.imshow('Video', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
    cv2.imshow('Video', frame)
video_capture.release()
cv2.destroyAllWindows()



































