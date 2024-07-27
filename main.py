import naoqi
import socket
import json
import qi
import argparse
import pyttsx3
import sys
import time
import wave
import StringIO
from picotts import PicoTTS
import pyaudio
import speech_recognition as sr
import random

import BaseHTTPServer
import threading
import json

import requests

import BaseHTTPServer
import threading
import json
from Queue import Queue

class RequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200, "ok")
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])  # Get the size of data
        post_data = self.rfile.read(content_length)  # Read the data
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.server.received_data_queue.put(post_data)  # Put data in the queue
        print("Received POST data: {}".format(post_data))
        # Stop the server after handling the POST request
        data = json.loads(post_data)
        if data['status'] == 'stop':
            print("Server is shutting down...")
            threading.Thread(target=self.server.shutdown).start()

def run_server(received_data_queue):
    server_address = ('', 8014)  # Serve on all available interfaces, port 8000
    httpd = BaseHTTPServer.HTTPServer(server_address, RequestHandler)
    httpd.received_data_queue = received_data_queue  # Set the queue in the server
    print("Starting server, use <Ctrl-C> to stop")
    httpd.serve_forever()



user_prompts = {
    'kid': """You are a tour guide that is explaining the Mona Lisa to a kid. You are now answering to questions. 
              Answer the following question in max 100 words: """,
    'adult': """You are a tour guide that is explaining the Mona Lisa to an adult. You are now answering to questions. 
              Answer the following question in max 100 words: """
}

class User():
    def __init__(self):
        self.name = ''
        self.age = ''
        self.expertise = "beginner"
        self.score = 0
        self.characterization_prompt = ''

    def update_name(self, name):
        self.name = name

    def update_age(self, age):
        adult_ages = ["20-29", "30-39", "40-49", "50-59"]
        if age in adult_ages:
            self.age = "adult"
            self.characterization_prompt = user_prompts['adult']
        else:
            self.age = "young"
            self.characterization_prompt = user_prompts['kid']

    def update_expertise(self, expertise):
        self.expertise = expertise
    
    def update_score(self, score):
        self.score = score


class Session():
    def __init__(self, simulation, robot_ip, robot_port, nn_server_host, nn_server_port):
        self.simulation = simulation
        self.robot_ip = robot_ip
        self.robot_port = robot_port
        self.active_session = False
        self.connected = False
        self.current_session = self.instantiate_session()
        self.nn_server_host = nn_server_host
        self.nn_server_port = nn_server_port
        self.tts_service = self.current_session.service("ALTextToSpeech")
        self.init_ttsservice()
        self.animation_player_service = self.current_session.service("ALAnimationPlayer")
        self.animated_say_service = self.current_session.service("ALAnimatedSpeech")
        self.speech_recognizer = sr.Recognizer()

    def instantiate_session(self):
        session = qi.Session()
        try:
            session.connect("tcp://" + self.robot_ip + ":" + str(self.robot_port))
            self.connected = True
            self.active_session = True
        except RuntimeError:
            print ("Can't connect to Naoqi at ip \"" + self.robot_ip + "\" on port " + str(self.robot_port) +".\n"
                    "Please check your script arguments. Run with -h option for help.")
            sys.exit(1)
        return session
    
    def init_ttsservice(self, language="English", volume=1.0, speed=100):
        self.tts_service.setLanguage(language)
        self.tts_service.setVolume(volume)
        self.tts_service.setParameter("speed", speed)

    def say(self, text):
        self.tts_service.say(text)
        play_tts_sound(text)

    def listen(self):
        with sr.Microphone() as source:
            self.speech_recognizer.adjust_for_ambient_noise(source)
            audio = self.speech_recognizer.listen(source)
            print("Listening...")
        try:
            print("Recognizing...")
            return self.speech_recognizer.recognize(audio)
        except LookupError:
            return "Could not understand audio"
    
    def animated_say(self, text, animated_text):
        #self.tts_service.say(text)
        self.animated_say_service.say(animated_text)

    def play_animation(self, animation_name):
        self.animation_player_service.run(animation_name)

def send_nn_server_request(nn_ip, nn_port, type, content):
    host = nn_ip
    port = nn_port
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((host, port))
    try:
        # Sending request
        message = json.dumps({'type': type, 'content': content})
        print("Sending:", message)
        s.sendall(message)
        
        # Receiving response
        response = s.recv(1024)
    finally:
        s.close()
        return json.loads(response)
    
def send_tablet_server_request( type ,payload="",base_url="http://127.0.0.1:8080", route=""):
    if type=="POST":
        requests.post(base_url+route, json=payload)
    elif type=="GET":
        requests.get(base_url+route)
    else:
        print("Invalid request type")
        # throw error
        RuntimeError("Invalid request type")


def explain_painting(session, user):
    send_tablet_server_request("GET",route="/display-painting")

    if user.age == "young":
        session.say("""Alright, let's imagine we're standing right in front of one of the most famous paintings in the world the Mona Lisa! 
                    This masterpiece was painted by an incredible artist named Leonardo da Vinci, who came from Italy. When Leonardo first 
                    made this painting, he called it La Gioconda, which means the happy or jovial lady, because the woman in the painting seems to be smiling.""")
        payload = {
            "detail": "mouth"
        }
        send_tablet_server_request("POST",payload=payload,route="/display-painting")
        session.say("""The Mona Lisa is quite small, only about the size of a typical school poster, around 21 by 30 inches. Leonardo painted it using oil paints on a wooden panel, which was pretty common back then. 
                    The woman in the painting, believed to be Lisa Gherardini, looks right at us no matter where we stand, thanks to her eyes that seem to follow us around. pretty cool, right?""")
        
        payload = {
            "detail": "eyes"
        }
        send_tablet_server_request("POST",payload=payload,route="/display-painting")
        

        session.say("Now, looking at her mouth, she has a very soft and mysterious smile which has made people curious for hundreds of years. ")

        payload = {
            "detail": "mouth"
        }

        send_tablet_server_request("POST",payload=payload,route="/display-painting")
        
        session.say(""" The background is a dreamy, almost magical landscape 
                        that seems to stretch far into the distance, adding to the mystery of her smile.""")
        
        payload = {
            "detail": "landscape_r"
        }

        send_tablet_server_request("POST",payload=payload,route="/display-painting")

        session.say("And guess what? This painting was so loved that someone actually stole it in 1911 from the Louvre Museum in Paris! But thankfully, it was returned and now millions of people can enjoy it. Isn't that exciting?")
    else:
        session.say("""
                    The Mona Lisa, painted by Leonardo da Vinci, an illustrious figure of the Italian Renaissance, remains one of the most celebrated and scrutinized works of art. Officially titled La Gioconda, it portrays Lisa Gherardini, the wife of a Florentine merchant, and is renowned for its enigmatic quality. This painting stands out not only for its delicate portrayal but also for Leonardo's masterful use of techniques.

                    Crafted between 1503 and 1506, though some suggest work continued until 1517, the Mona Lisa is relatively small, measuring 30 by 21 inches. Leonardo employed a sfumato technique, a method of allowing tones and colors to shade gradually into one another, producing softened outlines or hazy forms. This technique is particularly evident in Lisa's famously ambiguous smile, which seems to change with the viewer's perspective and has intrigued audiences for centuries.
                    """)
        payload = {
            "detail": "mouth"
        }
        send_tablet_server_request("POST",payload=payload,route="/display-painting")

        session.say("""
                    The backdrop of the painting features a fantastical, rugged landscape that seems to recede to an infinite horizon, adding to the painting's allure and sense of mystery. 
                    """)
        
        payload = {
            "detail": "landscape_r"
        }

        send_tablet_server_request("POST",payload=payload,route="/display-painting")

        session.say("""
                    Perhaps one of the most intriguing aspects is her eyes, which appear to follow the viewer around the room, a testament to Leonardo's skill in perspective.
                    """)
        
        payload = {
            "detail": "eyes"
        }
        send_tablet_server_request("POST",payload=payload,route="/display-painting")

        session.say("""
                    The painting's fame was amplified when it was stolen in 1911 from the Louvre Museum, an event that made headlines worldwide. It was later recovered and returned, further cementing its status as a priceless treasure of global cultural heritage.
                    """)


# Initialize PicoTTS
picotts = PicoTTS()
# Initialize speech recognition
r = sr.Recognizer()

def play_tts_sound(text):
    global picotts
    # Synthesize speech
    wavs = picotts.synth_wav(text)
    
    # Use StringIO to simulate a file with the audio data
    wav = wave.open(StringIO.StringIO(wavs))
    
    # Set up PyAudio
    p = pyaudio.PyAudio()
    
    # Open a stream with the right parameters
    stream = p.open(format=p.get_format_from_width(wav.getsampwidth()),
                    channels=wav.getnchannels(),
                    rate=wav.getframerate(),
                    output=True)
    
    # Read data from the WAV file
    data = wav.readframes(1024)
    while data:
        stream.write(data)
        data = wav.readframes(1024)
    
    # Close the stream and PyAudio
    stream.stop_stream()
    stream.close()
    p.terminate()
    
    print(wav.getnchannels(), wav.getframerate(), wav.getnframes())

def take_pre_test(session, user):
    questions = ["Do you know the author of Mona Lisa?",
                 "In which epoch was Mona Lisa painted?",
                 "In what style was Mona Lisa painted?",]
    # pick a random question
    question = random.choice(questions)
    session.say("Let me ask you a quick question to understand if you are an art wizard: " +  question)
    answer = session.listen()
    prompt = 'I asked the following question to a user: "' + question + '". The user answered: "' + answer + '". Tell me if the user is an expert or a beginned. Use only the words experts or beginner'
    response = send_nn_server_request(session.nn_server_host, session.nn_server_port, 'question', prompt)
    expertise = response['message']
    print("The user is a " + expertise)
    user.update_expertise(expertise)

def answer_user_questions(session, user):
    user_satisfied = False
    session.say("Do you have any questions about Mona Lisa? If you do, please ask me. If you don't, just say no.")
    answer = session.listen()
    if 'no' in answer.lower():
        user_satisfied = True
        session.say("Ok, now it's time to tell you more about Mona Lisa.")
        return
    else:
        question = user.characterization_prompt + answer

    while not user_satisfied:
        print("User asked: " + question)
        session.say("Let me think about it")
        session.play_animation(".lastUploadedChoregrapheBehavior/thinking")
        response = send_nn_server_request(session.nn_server_host, session.nn_server_port, 'question', question)
        session.say(response['message'])
        session.say("Do you have any other question? If you don't, just say no.")
        time.sleep(1)
        answer = session.listen()
        if 'no' in answer.lower():
            session.say("Now that you know a bit more about Mona Lisa, let me tell you more about the painting")
            user_satisfied = True
        else:
            question = user.characterization_prompt + answer
    return

def start_quiz(session, user):

    session.say("Let's start the quiz. I will ask you 3 questions about Mona Lisa. Let's see how much you know about it.")

    if user.age == "young":
        difficulty = "easy"
    elif user.age == "adult" and user.expertise == "beginner":
        difficulty = "medium"
    else:
        difficulty = "hard"

    payload = {
        "difficulty": difficulty
    }
    send_tablet_server_request("POST",payload=payload,route="/display-quiz")

    finished = False

    while not finished:
        try:
            # Wait for the POST request
            print("Waiting for POST request...")
            post_data = received_data_queue.get()  # Get the data from the queue
            print("POST data received: {}".format(post_data))
        except KeyboardInterrupt:
            print("Server is shutting down...")
            #threading.Thread(target=self.server.shutdown).start()

        # Continue with the rest of your code
        # For example, you can parse the JSON data
        if post_data:
            data = json.loads(post_data)
            print("Parsed data: {}".format(data))
            print(data['result'])

            status = data['status']
            result = data['result']

            if result == "correct":
                user.update_score(user.score + 33)

            if status == "stop":
                finished = True
                break
    

    if user.score == 0:
        session.say("You didn't get any question right. But that's okay, you can always learn more about Mona Lisa!")
    elif user.score == 33:
        session.say("You got one question right. That's a good start!")
    elif user.score == 66:
        session.say("You got two questions right. You are almost there!")
    else:
        session.say("You got all the questions right! You are a Mona Lisa expert!")

    payload = {
        "percentage": str(user.score),
        "age": str(user.age)
    }

    send_tablet_server_request("POST",payload=payload,route="/display-results")
    
if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("--ip", type=str, default="127.0.0.1",
                        help="Robot IP address. On robot or Local Naoqi: use '127.0.0.1'.")
    parser.add_argument("--port", type=int, default=9559,
                        help="Naoqi port number")
    parser.add_argument("--simulation", type=bool, default=True)
    parser.add_argument("--nn_server_host", type=str, default="127.0.0.1")
    parser.add_argument("--nn_server_port", type=int, default=50008)

    args = parser.parse_args()
    session = Session(args.simulation,args.ip, args.port, args.nn_server_host, args.nn_server_port)

    time.sleep(1)
    if session.connected:
        print('Connected_succesfully to naoqi')

    user = User()
    
    # greet person
    #session.tts_service.say("Hello! I am a robot. What is your name?")
    #wait 1 second
    
    # Create a queue to receive data from the server thread
    received_data_queue = Queue()
    # Start the server in a separate thread
    server_thread = threading.Thread(target=run_server, args=(received_data_queue,))
    server_thread.start()

    


    session.say("""Hello human! I hope you are appreciating our museum. 
                I am here to tell you all the secrets about Mona Lisa. 
                But first, tell me your name please""")

    # Continue with the rest of your code
    # For example, you can parse the JSON data

    
    print("------------ SPEAK ---------------")
    name = session.listen()
    user.update_name(name)
    session.say('Alright ' + user.name + ' let me take a picture of you')
    session.play_animation(".lastUploadedChoregrapheBehavior/take_photo")
    result = send_nn_server_request(args.nn_server_host, args.nn_server_port, 'age', 'photo')
    user.update_age(result['message'])
    session.say('You look you are a ' + user.age + ' human. Is that correct?')
    confirmation = session.listen()
    if 'yes' not in confirmation.lower():
        session.say("Alright I am going to correct your age.")
        if user.age == 'adult':
            user.age = 'young'
        else:
            user.age = 'adult'

    if user.age == 'adult':
        take_pre_test(session, user)
    else:
        user.expertise = 'beginner'

    answer_user_questions(session, user)
    
    explain_painting(session, user)

    start_quiz(session, user)

    send_tablet_server_request("GET",route="/display-home")

    session.say("Thank you for visiting our museum, I hope you enjoyed learning about Mona Lisa. Have a great day!")



    
    
