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
        session.say("Alright let's move on to the next part")
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
            session.say("Your questions were indeed very interesting. Let's move on to the next part.")
            user_satisfied = True
        else:
            question = user.characterization_prompt + answer
    return



    
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

    if session.connected:
        print('Connected_succesfully to naoqi')

    user = User()
    
    # greet person
    #session.tts_service.say("Hello! I am a robot. What is your name?")
    #wait 1 second
    
    time.sleep(1)

    session.say("""Hello human! I hope you are appreciating our museum. 
                I am here to tell you all the secrets about Mona Lisa. 
                But first, tell me your name please""")
    
    print("------------ SPEAK ---------------")
    name = session.listen()
    user.update_name(name)
    session.say('Alright ' + user.name + 'let me take a picture of you')
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
