import tflite_runtime.interpreter as tflite
from PIL import Image, ImageDraw
import numpy as np
import face_recognition
from picamera2 import Picamera2, Preview
from time import sleep
import subprocess
import json
import RPi.GPIO as GPIO
import tkinter as tk
from tkinter import messagebox

root = tk.Tk()
root.withdraw()

picam2 = Picamera2()
camera_config = picam2.create_preview_configuration()
picam2.configure(camera_config)
picam2.start()
sleep(1)
image_counter = 1
rotation_checker = 0

RED_LED_PIN = 27#10
GREEN_LED_PIN = 17#8
GPIO.setmode(GPIO.BCM)
GPIO.setup(RED_LED_PIN, GPIO.OUT)
GPIO.setup(GREEN_LED_PIN, GPIO.OUT)

interpreter = tflite.Interpreter(model_path="/home/swayam/soberride/drunk_sober_face_adamax.tflite")
interpreter.allocate_tensors()

input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()

input_shape = input_details[0]['shape']
input_scale, input_zero_point = input_details[0]['quantization']

def detect_face(frame):
    global rotation_checker
    image = Image.fromarray(frame).convert("RGB")
    image_array = np.array(image)
    faces = face_recognition.face_locations(image_array)
    draw = ImageDraw.Draw(image)
    if faces:
        return image, faces, draw
    
    image2 = image.rotate(90)
    image2_array = np.array(image2)
    faces2 = face_recognition.face_locations(image2_array)
    draw2 = ImageDraw.Draw(image2)
    if faces2:
        return image2, faces2, draw2
    
    image3 = image2.rotate(90)
    image3_array = np.array(image3)
    faces3 = face_recognition.face_locations(image3_array)
    draw3 = ImageDraw.Draw(image3)
    if faces3:
        return image3, faces3, draw3
    
    image4 = image3.rotate(90)
    image4_array = np.array(image4)
    faces4 = face_recognition.face_locations(image4_array)
    draw4 = ImageDraw.Draw(image4)
    return image4, faces4, draw4

while (True):
    GPIO.output(RED_LED_PIN, GPIO.HIGH)
    GPIO.output(GREEN_LED_PIN, GPIO.HIGH)
    sleep(0.2)
    GPIO.output(RED_LED_PIN, GPIO.LOW)
    GPIO.output(GREEN_LED_PIN, GPIO.LOW)
    sleep(0.2)
    GPIO.output(RED_LED_PIN, GPIO.HIGH)
    GPIO.output(GREEN_LED_PIN, GPIO.HIGH)
    sleep(0.2)
    GPIO.output(RED_LED_PIN, GPIO.LOW)
    GPIO.output(GREEN_LED_PIN, GPIO.LOW)
    sleep(0.2)
    frame = picam2.capture_array()
    image, faces, draw = detect_face(frame)
    if not faces:
        messagebox.showinfo("Alert","No face detected")
        continue
    else:
        for face in faces:
            top, right, bottom, left = face
            draw.rectangle([left, top, right, bottom], outline="red", width=3)
        top, right, bottom, left = faces[0]
        face_img = image.crop((left, top, right, bottom))
        face_img = face_img.resize((224, 224), Image.BILINEAR)
        face_img.show()
        tfl_img = np.array(face_img, dtype=np.float32)[..., :3]
        tfl_img = (tfl_img/255.0 - input_zero_point) / input_scale
        tfl_img = np.round(tfl_img).astype(np.int8)
        tfl_img = np.expand_dims(tfl_img, axis=0)
        
        interpreter.set_tensor(input_details[0]['index'], tfl_img)

        interpreter.invoke()

        output_data = interpreter.get_tensor(output_details[0]['index'])
        
        if output_details[0]['quantization'] != (0.0, 0):
          output_scale, output_zero_point = output_details[0]['quantization']
          output_data = (output_data.astype(np.float32) - output_zero_point) *output_scale

        all_output = ""
        
        face_intox = ("Chance of Intoxication:" + str(output_data[0][1]))
        face_sober = ("Chance of Sobriety:" + str(output_data[0][0]))
        #all_output = face_intox + "\n" + face_sober
        #if(output_data[0][1] >= 0.5):
          #all_output += ("\nBased on face analysis, Driver might be Drunk\n")
        #else:
          #all_output += ("\nBased on face analysis, Driver might be Sober")
        face_img.close()
        face_chance = output_data[0][1]
        result = {"face_drunk_chance": float(face_chance)}
        with open('/home/swayam/soberride/face_drunk_result.json','w') as f:
            json.dump(result, f)
    
        breathalyzer = subprocess.run(["python3", "soberride_mq3.py"], capture_output = True, text = True)
        final_output = breathalyzer.stdout.strip()
        all_output += ("\n" + final_output)
        messagebox.showinfo("Alert", all_output)
        image_counter += 1
    image.close()