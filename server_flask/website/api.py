from flask import Blueprint, request, jsonify, redirect, url_for, render_template
from flask_socketio import SocketIO, emit

api = Blueprint('api', __name__)
socketio = SocketIO()

# Function to set up socketio with app
def init_socketio(app):
    socketio.init_app(app)
    return socketio
    # CONSTANTS

@api.route('/display-home', methods=['GET'])
def display_home():
    target_url = request.host_url
    socketio.emit('change_page', {'url': target_url})
    return 'redirecting to -> HOME'

@api.route('/display-painting', methods=['GET', 'POST'])
def display_painting():

    target_url = request.host_url + 'painting'

    if request.method == 'GET':
        socketio.emit('change_page', {'url': target_url})
        return 'redirecting to -> PAINTING '

    # Get the JSON data from the request
    data = request.json
    detail = data['detail']
    if detail:
        target_url = target_url + '?detail=' + detail

    socketio.emit('change_page', {'url': target_url})
    return 'redirecting to -> PAINTING ' + detail

@api.route('/display-quiz', methods=['POST'])
def display_quiz():

    # Get the JSON data from the request
    data = request.json
    difficulty = data['difficulty']
    target_url = request.host_url + 'quiz' + '?difficulty=' + difficulty

    socketio.emit('change_page', {'url': target_url})
    return 'redirecting to -> QUIZ ' + difficulty

@api.route('/display-results', methods=['POST'])
def display_results():

    # Get the JSON data from the request
    data = request.json
    percentage = data['percentage']
    age = data['age']
    target_url = request.host_url + 'results' + '?percentage=' + percentage + '&age=' + age

    socketio.emit('change_page', {'url': target_url})
    return 'redirecting to -> QUIZ ' + percentage + ' ' + age

@api.route('/display-loading', methods=['GET'])
def display_loading():
    target_url = request.host_url + 'loading'
    socketio.emit('change_page', {'url': target_url})
    return 'redirecting to -> LOADING'