import socket
import threading
import ollama
import json
from transformers import pipeline
import requests
from PIL import Image
from io import BytesIO
import cv2
import numpy as np

pipe = pipeline("image-classification", model="nateraw/vit-age-classifier")

def execute_function(data):
    # Example function that capitalizes the input string
    global pipe
    request_type = data['type']
    print(f'request_type: {request_type}')

    if request_type == 'question':
        answer = ollama.chat(model='llama3', messages=[
        {
            'role': 'user',
            'content': data['content'],
        },
        ])
        #print(response['message']['content'])
        status = 200
        answer = answer['message']['content']
        response = {'status': status, 'message': answer}
        return json.dumps(response)
    
    elif request_type == 'age':
        cap = cv2.VideoCapture(2)
        ret, frame = cap.read()
        cv2.imwrite('img.jpg', frame)
        cap.release()

        im = Image.open('img.jpg')
        result = pipe(im)[0]['label']
        status = 200
        response = {'status': status, 'message': result}
        return json.dumps(response)
    else:
        return json.dumps({'status': 404, 'message': 'Invalid request type'})

def handle_client(conn, addr):
    print('Connected by', addr)
    try:
        while True:
            raw_data = conn.recv(1024)
            if not raw_data:  # Check if any data is received
                print("No data received, client may have disconnected.")
                break  # Exit the loop if no data is received
            
            try:
                data = json.loads(raw_data)
                print(f'data: {data}')
                response = execute_function(data)
                conn.sendall(response.encode())
            except json.JSONDecodeError:
                print("Received malformed data, not in JSON format.")
    finally:
        conn.close()


def server():
    host = '127.0.0.1'
    port = 50008
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((host, port))
        s.listen()
        print("Server is listening on port:", port)
        while True:
            conn, addr = s.accept()
            thread = threading.Thread(target=handle_client, args=(conn, addr))
            thread.daemon = True  # Optional: Marks threads as daemons so they won't prevent exiting
            thread.start()

if __name__ == "__main__":
    server()
