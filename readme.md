# NetWave
## Dynamic radio server with Racoder

This project is a Flask-based server that streams audio from an external URL and plays it through Docker containers running `racoder`.

### Overview
The server listens for HTTP requests at `/radio` endpoint. When a request comes in, it retrieves the URL of the audio stream (provided via query parameters) and starts playing this stream using a Docker container.

### Key Components
1. **Flask Application**: The main application is a Flask web server that handles HTTP requests and streams audio data.
2. **Docker Container**: A Docker container running `racoder` plays the provided audio stream.
3. **Configuration File (`config.ini`)**: Stores configuration parameters for the Racoder host, port, and Flask server.

### Installation
Docker is necessary for running Docker containers that are used by the NetWave server. Recommended and tested version of Python is 3.13. It is required to install packages in virtual enviromnent - virtualenv.

#### Docker
Tested on Arch-based distros:
```
sudo pacman -S docker docker-compose
```

User should be added to docker group (reboot after this step):
```
sudo usermod -aG docker your_username
```

Docker service should be stared:
```
sudo systemctl start docker.service
```

If you need to enable docker service on start use this command:
```
sudo systemctl enable --now docker.service
```

#### Python
Create virtual environment using virtualenv package.
```
python -m venv .venv
```

Enter to created environment by source command on Linux:
```
source .venv/bin/activate
```

Install required packages using requirements.txt file which is attached to this project:
```
pip install -r requirements.txt
```

### Configuration
- The configuration is read from a file named `config.ini`.
  - `racoder.host`: Hostname or IP address for the Racoder server.
  - `racoder.port`: Port number on which the Racoder server listens (1000-40000 is allowed).
  - `racoder.bitrate`: Bitrate value for MP3 stream output (16-320 kbps is allowed).
  - `flask.port`: Port number for the Flask server to listen on.

### Configuration sample
```
[flask]
port = 5000

[racoder]
host = racoder.example.com
port = 3000
bitrate = 128
```

### Running the server
Now that everything is installed and configured, you can run the NetWave server.

To run the NetWave server in debug mode, use the following command:

```
python radio.py
```

### Contact
In case of issues or suggestions you can use `Issues` section on Github.<br/>
You can join to Discord server "Polska Społeczność Linuksa" (The server is in Polish, but the use of English is welcome).<br/>
Click here to join now: [https://discord.gg/AnG2Kv6axS](https://discord.gg/AnG2Kv6axS)