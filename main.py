import naoqi
import socket
import json
import qi
import argparse
import pyttsx3
import sys

class User():
    def __init__(self, name):
        self.name = name
        self.age
        self.expertise
        self.score

    def update_age(self, age):
        self.age = age

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
    result = send_nn_server_request(args.nn_server_host, args.nn_server_port, 'age', 'broo')

    print(result['message'])