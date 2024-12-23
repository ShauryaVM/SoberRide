import tflite_runtime.interpreter as tflite
from PIL import Image
import numpy as np
import cv2
from picamera2 import Picamera2, Preview
from time import sleep

face_cascade = cv2.CascadeClassifier("/home/pi/object_detection/haarcascade_frontalface_default.xml")

picam2 = Picamera2()
camera_config = picam2.create_preview_configuration()
picam2.configure(camera_config)
picam2.start()
sleep(1)
image_counter = 1

interpreter = tflite.Interpreter(model_path="/home/pi/Downloads/drunk_sober_face_adamax.tflite")
interpreter.allocate_tensors()

input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()

input_shape = input_details[0]['shape']
input_scale, input_zero_point = input_details[0]['quantization']

while (True):
    print(image_counter)
    frame = picam2.capture_array()
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, scaleFactor = 1.1, minNeighbors = 5)
    for(x,y,w,h) in faces:
        cv2.rectangle(frame, (x,y), (x+w, y+h), (255,0,0), 2)
        roi = gray[y:y + h, x:x+w]
        cv2.imshow("Face Detection", frame)
        cv2.imwrite(f"/home/pi/object_detection/faces/face_detection_{image_counter}.jpg", frame)
        tfl_img = Image.open(f"/home/pi/object_detection/faces/face_detection_{image_counter}.jpg")
        tfl_img = tfl_img.resize((224, 224))
        tfl_img = np.array(tfl_img, dtype=np.float32)
        tfl_img = (tfl_img/255.0 - input_zero_point) / input_scale
        tfl_img = np.round(tfl_img).astype(np.int8)
        tfl_img = np.expand_dims(tfl_img, axis=0)

        interpreter.set_tensor(input_details[0]['index'], tfl_img)

        interpreter.invoke()

        output_data = interpreter.get_tensor(output_details[0]['index'])
        print(output_data)

        if output_details[0]['quantization'] != (0.0, 0):
          output_scale, output_zero_point = output_details[0]['quantization']
          output_data = (output_data.astype(np.float32) - output_zero_point) *output_scale
          print("Dequantized Output:", output_data)

        print("Chance of Intoxication:" + str(output_data[0][1]))
        print("Chance of Sobriety:" + str(output_data[0][0]))
        if(output_data[0][1] > 0.3):
          print("Drunk")
        else:
          print("Sober")
        image_counter += 1