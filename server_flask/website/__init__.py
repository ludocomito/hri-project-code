from .api import init_socketio
from flask import Flask, send_file
from flask_socketio import SocketIO, emit

def create_app():

    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'HRI'
    socketio = init_socketio(app)

    from .views import views
    from .api import api

    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(api, url_prefix='/')
    

    return app, socketio