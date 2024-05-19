from website import create_app

app, socketio = create_app()

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=8080, debug=True)
    # app.run(host='0.0.0.0', port=8080, debug=True)