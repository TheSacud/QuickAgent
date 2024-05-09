import base64
import json
import threading

from flask import Flask, render_template
from flask_sockets import Sockets

from deepgram import (
    DeepgramClient,
    DeepgramClientOptions,
    LiveTranscriptionEvents,
    LiveOptions,
    Microphone,
)

HTTP_SERVER_PORT = 8080

app = Flask(__name__)
sockets = Sockets(app)


@app.route("/twiml", methods=["POST"])
def return_twiml():
    print("POST TwiML")
    return render_template("streams.xml")


def on_transcription_response(response):
    if not response.results:
        return

    result = response.results[0]
    if not result.alternatives:
        return

    transcription = result.alternatives[0].transcript
    print("Transcription: " + transcription)


@sockets.route("/")
def transcript(ws):
    print("WS connection opened")

    while not ws.closed:
        message = ws.receive()
        if message:
            data = json.loads(message)
            if data['event'] == 'media':
                # Decodifica o payload de base64 para binário
                chunk = base64.b64decode(data['media']['payload'])
                # Aqui você enviaria 'chunk' para o Deepgram ou outro serviço de transcrição
                send_to_deepgram(chunk)
            elif data['event'] == 'stop':
                print("Stream stopped.")
                break

    print("WebSocket connection closed.")


if __name__ == "__main__":
    from gevent import pywsgi
    from geventwebsocket.handler import WebSocketHandler

    server = pywsgi.WSGIServer(
        ("", HTTP_SERVER_PORT), app, handler_class=WebSocketHandler
    )
    print("Server listening on: http://localhost:" + str(HTTP_SERVER_PORT))
    server.serve_forever()