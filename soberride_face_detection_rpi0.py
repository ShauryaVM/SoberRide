import tflite_runtime.interpreter as tflite
from PIL import Image, ImageDraw
import numpy as np
import face_recognition
from picamera2 import Picamera2, Preview
from time import sleep
import subprocess
import json

picam2 = Picamera2()
camera_config = picam2.create_preview_configuration()
picam2.configure(camera_config)
picam2.start()
sleep(1)
image_counter = 1

interpreter = tflite.Interpreter(model_path="/home/swayam/soberride/drunk_sober_face_adamax.tflite")
interpreter.allocate_tensors()

input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()

input_shape = input_details[0]['shape']
input_scale, input_zero_point = input_details[0]['quantization']

while (True):
    frame = picam2.capture_array()
    image = Image.fromarray(frame).convert("RGB")
    image.show()
    image_array = np.array(image)
    faces = face_recognition.face_locations(image_array)
    draw = ImageDraw.Draw(image)
    if not faces:
        print("No face detected")
        sleep(10)
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

        print("Chance of Intoxication:" + str(output_data[0][1]))
        print("Chance of Sobriety:" + str(output_data[0][0]))
        if(output_data[0][1] >= 0.3):
          print("Driver face indicates Drunk")
        else:
          print("Driver face indicates Sober")
        face_chance = output_data[0][1]
        result = {"face_drunk_chance": float(face_chance)}
        with open('/home/swayam/soberride/face_drunk_result.json','w') as f:
            json.dump(result, f)
    
        breathalyzer = subprocess.run(["python3", "soberride_mq3.py"], capture_output = True, text = True)
        final_output = breathalyzer.stdout.strip()
        print(final_output)
        image_counter += 1
        sleep(3)
