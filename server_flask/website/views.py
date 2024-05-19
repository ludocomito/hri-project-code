from flask import Blueprint, request, jsonify, redirect, url_for, render_template

views = Blueprint('views', __name__)

@views.route('/')
def home():
    return render_template('home.html')

@views.route('/painting', methods=['GET'])
def display_painting():

    # Check if there are more parameters than expected
    if len(request.args) > 2:
        return jsonify({'error': 'Too many parameters'}), 400
    
    return render_template('painting.html')

@views.route('/quiz', methods=['GET'])
def display_quiz():

    # Check if there are more parameters than expected
    if len(request.args) > 2:
        return jsonify({'error': 'Too many parameters'}), 400
    
    # Display default quiz if no parameters
    if len(request.args) < 1:
        return jsonify({'error': 'The quiz can only be displayed with the parameter "difficulty"'}), 400
    
    return render_template('quiz.html')

@views.route('/results', methods=['GET'])
def display_results():
    return render_template('results.html')

@views.route('/loading', methods=['GET'])
def display_loading():
    return render_template('loading.html')