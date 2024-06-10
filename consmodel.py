
from confluent_kafka import Consumer, KafkaError, KafkaException
import sys
import requests
import json
import cv2
import numpy as np
import os

# YOLO model files
YOLO_CONFIG = 'yolov3.cfg'
YOLO_WEIGHTS = 'yolov3.weights'
YOLO_CLASSES = 'coco.names'

# Load YOLO model
net = cv2.dnn.readNet(YOLO_WEIGHTS, YOLO_CONFIG)
with open(YOLO_CLASSES, 'r') as f:
    classes = [line.strip() for line in f.readlines()]

layer_names = net.getLayerNames()
output_layers = [layer_names[i - 1] for i in net.getUnconnectedOutLayers()]

me = "ahmedabdelsalam1"
conf = {'bootstrap.servers': '34.68.55.43:9094,34.136.142.41:9094,34.170.19.136:9094',
        'group.id': "me",
        'enable.auto.commit': 'false',
        'auto.offset.reset': 'smallest'}

consumer = Consumer(conf)
running = True


def detect_object(image_path):
    # Load image
    img = cv2.imread(image_path)
    if img is None:
        raise FileNotFoundError(f"Image at path {image_path} not found.")
    height, width, channels = img.shape

    # Prepare the image for YOLO
    blob = cv2.dnn.blobFromImage(img, 0.00392, (416, 416), (0, 0, 0), True, crop=False)
    net.setInput(blob)
    outs = net.forward(output_layers)

    # Analyze the detections
    class_ids = []
    confidences = []
    boxes = []
    for out in outs:
        for detection in out:
            scores = detection[5:]
            class_id = np.argmax(scores)
            confidence = scores[class_id]
            if confidence > 0.5:  # Confidence threshold
                center_x = int(detection[0] * width)
                center_y = int(detection[1] * height)
                w = int(detection[2] * width)
                h = int(detection[3] * height)
                x = int(center_x - w / 2)
                y = int(center_y - h / 2)
                boxes.append([x, y, w, h])
                confidences.append(float(confidence))
                class_ids.append(class_id)

    indexes = cv2.dnn.NMSBoxes(boxes, confidences, 0.5, 0.4)
    detected_objects = [classes[class_ids[i]] for i in indexes.flatten()]  # Use .flatten() to handle the index array
    return detected_objects[0] if detected_objects else "undefined"


def msg_process(msg):
    try:
        msg_value = msg.value().decode()
        if not msg_value:
            print("Received an empty message.")
            return

        print(f"Received message: {msg_value}")

        # Construct the image path correctly
        image_path = os.path.join(r"C:\Users\a1hmm\PycharmProjects\pythonProject2\images", f"{msg_value}.jpg")

        # Detect object in the image
        detected_object = detect_object(image_path)
        requests.put(f'http://127.0.0.1:5000/object/{msg_value}', json={"object": detected_object})
    except FileNotFoundError as e:
        print(f"File not found error: {e}")
    except json.JSONDecodeError as e:
        print(f"JSON decoding error: {e}")
    except Exception as e:
        print(f"Error processing message: {e}")


def basic_consume_loop(consumer, topics):
    try:
        consumer.subscribe(topics)

        while running:
            msg = consumer.poll(timeout=1.0)
            if msg is None: continue

            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    # End of partition event
                    sys.stderr.write('%% %s [%d] reached end at offset %d\n' %
                                     (msg.topic(), msg.partition(), msg.offset()))
                elif msg.error():
                    raise KafkaException(msg.error())
            else:
                msg_process(msg)
    finally:
        # Close down consumer to commit final offsets.
        consumer.close()


def shutdown():
    global running
    running = False


basic_consume_loop(consumer, [me])
