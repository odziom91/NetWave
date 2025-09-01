#
# NetWave 
# Dynamic radio server with Racoder
# Author: Krzysztof "OdzioM" Odziomek
#

from flask import Flask, Response, request, stream_with_context
import time
import docker
import requests
import configparser

cfg = configparser.ConfigParser()
client = docker.from_env()
app = Flask(__name__)

def generate(host, port):
    """
    Generator function that yields chunks of audio data from the specified URL.

    Args:
        host (str): The hostname or IP address of the server hosting the audio stream.
        port (int): The port number on which the audio stream is accessible.

    Yields:
        bytes: Chunks of audio data.
    """
    with requests.get(f"http://{host}:{port}/", stream=True) as r:
        for chunk in r.iter_content(chunk_size=4096):
            if chunk:
                yield chunk


@app.route('/radio', methods=['GET'])
def start_radio():
    """
    Endpoint to start a radio station. The URL of the audio stream is provided via query parameters.

    Returns:
        Response: A Flask response object containing the audio stream as an MP3 file.
    """
    # get url and stream name (if available) from query
    stream_url = request.args.get("url")
    if request.args.get("name"):
        station_name = request.args.get("name")
    else:
        station_name = "Radio Station"
    
    # get host and port for racoder from config.ini file
    cfg.read('config.ini')
    racoder_host = cfg.get('racoder', 'host')
    racoder_port = cfg.get('racoder', 'port')
    
    # stop racoder if it is running
    try:
        container = client.containers.get('racoder')
        container.stop()
    except docker.errors.NotFound as e:
        pass

    # create a playlist configuration string
    pls_content = f"""[playlist]
NumberOfEntries=1
File1=http://{racoder_host}:{racoder_port}/
Title1={station_name}
Length1=-1
Version=2
"""

    # start docker
    container = client.containers.run(
        "paulgalow/racoder:latest",
        remove=True,
        read_only=True,
        cap_drop=["ALL"],
        name="racoder",
        ports={"3000/tcp": 3000},
        environment={
            "INPUT_STREAM": f"{stream_url}"
        },
        detach=True
    )

    # sleep for a while...
    time.sleep(0.5)
    
    # return the audio stream as an MP3 file
    return Response(
        stream_with_context(generate(racoder_host, racoder_port)),
        content_type="audio/mpeg"
    )

if __name__ == '__main__':
    """
    Main block that reads configuration from 'config.ini', sets up Flask server,
    and starts the application.

    Reads:
        - flask.port: The port number for the Flask server to listen on.

    Sets up:
        - Flask server with specified host and port, running in debug mode.
    """
    # read flask port
    cfg.read('config.ini')
    flask_port = cfg.get('flask', 'port')
    
    # start flask
    app.run(host="0.0.0.0", port=flask_port, debug=True)
