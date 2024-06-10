from confluent_kafka import Consumer, KafkaError, KafkaException
import sys
import requests
import random
import json
import cv2
import numpy as np
import os
from PIL import Image, ImageDraw, ImageFont
import base64

me = "ahmedabdelsalam1"
conf = {'bootstrap.servers': '34.68.55.43:9094,34.136.142.41:9094,34.170.19.136:9094',
        'group.id': "said",
        'enable.auto.commit': 'false',
        'auto.offset.reset': 'smallest'}

Consumer = Consumer(conf)
running = True

image_dir = r"C:\Users\a1hmm\PycharmProjects\pythonProject2\images"


def detect_object(input_image_path,watermark_text):
    try:
        # Open an image file
        image = Image.open(input_image_path).convert("RGBA")

        # Make the image editable
        txt = Image.new('RGBA', image.size, (255, 255, 255, 0))

        # Choose a font and size
        font_size = 100  # You can adjust this value for larger or smaller text
        font = ImageFont.truetype("arial.ttf", font_size)  # Make sure you have arial.ttf or another .ttf file available

        # Initialize ImageDraw
        draw = ImageDraw.Draw(txt)

        # Get the image size
        width, height = image.size

        # Draw the text multiple times across the whole image
        for x in range(0, width, int(font_size * 1.5)):
            for y in range(0, height, int(font_size * 1.5)):
                draw.text((x, y), watermark_text, font=font, fill=(255, 255, 255, 128))

        # Combine the image with the watermark
        watermarked = Image.alpha_composite(image, txt)

        # Save the image
        watermarked = watermarked.convert("RGB")  # Remove alpha for saving in jpg format.
        watermarked.save(input_image_path)

        print(f"Watermark added to {input_image_path}")

    except Exception as e:
        print(f"Error adding watermark: {e}")


def msg_process(msg):
    folder_path = r"C:\Users\a1hmm\PycharmProjects\pythonProject2\images"
    image_filename = msg.value().decode()
    image_path = os.path.join(folder_path, image_filename + ".jpg")
    detect_object(image_path, "Watermark")
    print("Water_mark processed successfully")


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
    running = False


basic_consume_loop(Consumer, [me])
