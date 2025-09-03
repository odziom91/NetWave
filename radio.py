#
# NetWave 
# Dynamic radio server with Racoder
# Author: Krzysztof "OdzioM" Odziomek
# version: 20250903_1120
#

from datetime import datetime
from flask import Flask, Response, request, stream_with_context
import sys
import logging
import time
import docker
import requests
import configparser

# init sequence with checks
try:
    # init logs
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(f'netwave_{datetime.now().strftime("%Y-%m-%d_%H%M%S")}.log'),
            logging.StreamHandler()
        ]
    )

    logger = logging.getLogger(__name__)

    # init key

    cfg = configparser.ConfigParser()
    client = docker.from_env()
    app = Flask(__name__)
except docker.errors.DockerException:
    logger.critical('Docker service is not running.')
    sys.exit()
except Exception as e:
    logger.critical(f'Unknown error: {str(e)}')
    sys.exit()

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
    try:
        # get url and stream name (if available) from query
        stream_url = request.args.get("url")
        if request.args.get("name"):
            station_name = request.args.get("name")
        else:
            station_name = "Radio Station"
        
        # get host and port for racoder from config.ini file
        cfg.read('config.ini')
        racoder_host = cfg.get('racoder', 'host')

        # port check
        try:
            racoder_port = int(cfg.get('racoder', 'port'))
            if racoder_port < 1000 or racoder_port > 4000:
                raise ValueError(f'Incorrect port. Port should be set up between 1000 and 40000. Your bitrate: {racoder_port} kbps. Please check config.ini file.')
        except:
            raise ValueError(f'Incorrect type of port value. Please check config.ini file.')

        # bitrate check
        try:
            racoder_bitrate = int(cfg.get('racoder', 'bitrate'))
            if racoder_bitrate < 16 or racoder_bitrate > 320:
                raise ValueError(f'Incorrect bitrate. Bitrate should be set up between 16 and 320 kbps. Your bitrate: {racoder_bitrate} kbps. Please check config.ini file.')
        except:
            raise ValueError(f'Incorrect type of bitrate value. Please check config.ini file.')

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
            ports={f"{racoder_port}/tcp": racoder_port},
            environment={
                "INPUT_STREAM": f"{stream_url}",
                "BITRATE": f"{(racoder_bitrate)}k"
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
    except ValueError as e:
        logging.error(str(e))
        return Response(str(e))
    except TypeError as e:
        logging.error(str(e))
        return Response(str(e))
    except Exception as e:
        raise Exception(f'Critical error: {str(e)}')

if __name__ == '__main__':
    """
    Main block that reads configuration from 'config.ini', sets up Flask server,
    and starts the application.

    Reads:
        - flask.port: The port number for the Flask server to listen on.

    Sets up:
        - Flask server with specified host and port, running in debug mode.
    """
    try:
        logger.info('NetWave started.')
        # read flask port
        cfg.read('config.ini')
        flask_port = cfg.get('flask', 'port')
        
        logger.info('Checking for Racoder docker image...')
        if len(client.images.list('paulgalow/racoder')) > 0:
            logger.info('Racoder docker image found.')
        else:
            logger.warning('Racoder docker image not found. Trying to download now... please wait...')
            try:
                client.images.pull('paulgalow/racoder:latest')
                logger.info('Racoder docker image downloaded successfully.')
            except Exception as e:
                logger.error(f'Download failed. This is catastrophic error. This app will be terminated now.')
                raise Exception(f'Download failed.\nError:\n{str(e)}')

        # start flask
        app.run(host="0.0.0.0", port=flask_port, debug=True)
    except Exception as e:
        logger.critical(str(e))
        sys.exit()