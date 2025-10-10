# HTTP Server with TCP Sockets in Python =(^.^)=

## Project Structure

Self-explanatory from the comments:

```
PR-lab1-HttpServer/
├── client.py           # HTTP client for making requests, displays HTML, saves PDF/PNG
├── server.py           # HTTP file server that serves files from specified directory
├── Dockerfile.client   # Docker image for the client application
├── Dockerfile.server   # Docker image for the server application
├── docker-compose.yml  # Orchestrates both server and client containers
├── content/            # Directory containing files to be served by the server
│   ├── ...             # Various files (HTML, PDF, PNG, etc.)
│   ├── downloads/      # Subdirectory for downloaded files via the client
│   ├── .../            # Subdirectories with other files
│   │   └── ...         # More files
└──────
```

## Dockerfiles

I decided to create two Dockerfiles, so one for the `server.py` and another one for `client.py`.

#### Dockerfile.server

```docker
# Dockerfile.server
FROM python:3.13-slim
WORKDIR /app
COPY server.py .
RUN useradd -m labuser && chown -R labuser:labuser /app
USER labuser
EXPOSE 1337
CMD ["python", "server.py", "-d", "/app/content"]
```

#### Dockerfile.client

```docker
FROM python:3.13-slim
WORKDIR /app
COPY client.py .
RUN useradd -m labuser && chown -R labuser:labuser /app
USER labuser
```

#### Docker Compose

```yaml
services:
  server:
    build:
      context: .
      dockerfile: Dockerfile.server
    ports:
      - "1337:1337"
    volumes:
      - "./content:/app/content:ro"
    command: [ "python", "server.py", "-d", "/app/content" ]

  client:
    build:
      context: .
      dockerfile: Dockerfile.client
    volumes:
      - "./content/downloads:/app/content/downloads"
    command: [ "tail", "-f", "/dev/null" ]
    extra_hosts:
      - "host.docker.internal:host-gateway"
```

**_Why have I done things this way?_**

- **Separate Dockerfiles** - Each service uses its own Dockerfile for clean
  separation of concerns
- **Volume Mounts:**
    - _Server_ - `./content:/app/content:ro` mounts the content directory as read-only so the server can serve files
      without being able to modify them
    - _Client_ - `./content/downloads:/app/content/downloads` mounts the downloads directory with write permissions so
      the client can save downloaded files
- **Client Command** - `tail -f /dev/null` keeps the client container running indefinitely, as without this, the container
  would exit immediately since client.py isn't a long-running process, so this allows me to run
  `docker-compose exec client python client.py ...` to execute client commands without starting a new container
  instance
- **extra_hosts** - Adds `host.docker.internal` DNS entry pointing to the host machine's gateway, which allows the client to
  make requests to services running on the host machine, outside Docker, in case I want to run other HTTP servers locally, such as one written in Pascal (RIP)

## Server Usage

#### Syntax

```bash
# Docker execution (using docker-compose)
docker-compose up -d

# Local execution
python server.py -d [SERVE_DIRECTORY]
```

- `-d [SERVE_DIRECTORY]`: Specifies the directory to serve files from. Defaults to the current directory if not
  provided.
- The server listens on port `1337`.
- Access the server via `http://localhost:1337` in a web browser or use the client to make requests.
- To stop the server, use `docker-compose down` if using Docker.

#### Example Usage

<details>
<summary>Contents of the served content dir 📁</summary>
<img src="https://files.catbox.moe/e0atdw.png" alt="Directory Structure" />
The `content/` in this case acts as the root directory, and it contains various files and subdirectories to test the server's functionality.

```shell
# Output from server logs when accessing the root of the server
Request: GET / HTTP/1.1 from ('127.0.0.1', 56684)
Serving / to ('127.0.0.1', 56684)
```

<details>
<summary>Accessing a subdir 📂</summary>
    <img src="https://files.catbox.moe/2wp2lc.png" alt="Subdirectory Listing" />

```shell
# Output from server logs when accessing /homework
Request: GET /homework HTTP/1.1 from ('127.0.0.1', 56676)
Serving /homework to ('127.0.0.1', 56676)
```

</details>
</details>

<details>
<summary>Requests of 4 file types 📂</summary>

#### Request for an HTML File, referencing two PNG files

<img src="https://files.catbox.moe/6uyajf.png" alt="Requested HTML File with references" />

```shell
# Output from server logs when accessing homework/hw.html
Request: GET /homework/hw.html HTTP/1.1 from ('127.0.0.1', 55132)
Serving /homework/hw.html to ('127.0.0.1', 55132)
Request: GET /homework/cock.png HTTP/1.1 from ('127.0.0.1', 55133)
Serving /homework/cock.png to ('127.0.0.1', 55133)
Request: GET /homework/cute_chicks.png HTTP/1.1 from ('127.0.0.1', 55134)
Serving /homework/cute_chicks.png to ('127.0.0.1', 55134)
```

#### Request for a PNG File

<img src="https://files.catbox.moe/vc1bh4.png" alt="Requested PNG" />

```shell
# Output from server logs when accessing /homework/cute_chicks.png
Request: GET /homework/cute_chicks.png HTTP/1.1 from ('127.0.0.1', 57048)
Serving /homework/cute_chicks.png to ('127.0.0.1', 57048)
```

#### Request for a PDF File

<img src="https://files.catbox.moe/70a9al.png" alt="Requested PDF" />

```shell
# Output from server logs when accessing `Lucrare de laborator nr. 1. Cifrul Cezar + (1).pdf`
Request: GET /Lucrare de laborator nr. 1. Cifrul Cezar + (1).pdf HTTP/1.1 from ('127.0.0.1', 61912)
Serving /Lucrare de laborator nr. 1. Cifrul Cezar + (1).pdf to ('127.0.0.1', 61912)
```

#### Request for a nonexistent File

<img src="https://files.catbox.moe/t3fem7.png" alt="Request to nonexistent file" />

```shell
# Output from server logs when accessing /nonexistent.html
Request: GET /nonexistent.html HTTP/1.1 from ('127.0.0.1', 61959)
Serving /nonexistent.html to ('127.0.0.1', 61959)
```

</details>

<details>
<summary>Redirects ↪️</summary>
<img src="https://files.catbox.moe/hvobyg.png" alt="Response to unnormalized path with redirection" />

```shell
# Output from server logs when accessing ////////.......///....///rock-paper-scissors.html
Server listening on port 1337 :3
Request: GET ////////.......///....///rock-paper-scissors.html HTTP/1.1 from ('127.0.0.1', 52028)
Serving ////////.......///....///rock-paper-scissors.html to ('127.0.0.1', 52028)
Request: GET /rock-paper-scissors.html HTTP/1.1 from ('127.0.0.1', 52029)
Serving /rock-paper-scissors.html to ('127.0.0.1', 52029)
```

</details>

## Client Usage

```bash
# Ensure docker-compose is running
docker-compose up -d

# Execute client commands
docker-compose exec client python client.py -H [HOST] -p [PORT] -u [URL] -d [DOWNLOAD_DIR]

# Example: Try fetching and displaying an HTML file
docker-compose exec client python client.py -H server -p 1337 -u /nonexistent.html -d ./content/downloads 

# Output:
# HTTP 404
# Error response: Not Found

# Locally
python client.py -H [HOST] -p [PORT] -u [URL] -d [DOWNLOAD_DIR]
```

## Requests to Adrian Vremere's server

In order to achieve this, both my machine and Adrian's server needed to be connected to the same network. I used my
phone's hotspot for this purpose.

- His IP address was `10.202.125.62` (he got it by running `ifconfig` on his machine)
- The port he was using: `6969` (nice x2)

<details><summary>Via the dockerized client 🐋</summary>
<img src="https://files.catbox.moe/uo5ofe.png" alt="Request via dockerized client to Adrian's server" />
Managed to download an amazing picture of Saitama :D
</details>

<details><summary>Via browser 🌐</summary>
<img src="https://files.catbox.moe/xgioo4.png" alt="Request via browser to Adrian's server" />
#h4ckervibes
</details>

## Features

#### Server

- **TCP Socket-based HTTP Server** - Built from scratch using Python's socket module
- **Multi-file Type Support** - Serves HTML, PDF, and PNG files
- **Automatic Directory Listing** - Generates styled HTML pages for directory browsing
- **Nested Directory Navigation** - Supports subdirectories with parent directory navigation, `../`
- **Path Normalization & Validation** - Handles malformed paths with multiple dots like `....` or `.....`, prevent dir
  traversal
- **HTTP 301 Redirects** - Automatically redirects unnormalized paths to normalized versions
- **File Metadata Display** - Shows file type icons, last modified timestamps, and file sizes
- **Styled UI with PicoCSS** - Clean directory listings with custom theming
- **Cute ASCII Art** - Features a cute sleeping cat in directory listings and error pages
- **Error Handling** - Proper 400 Bad Request and 404 Not Found responses
- **Configurable Root Directory** - Command-line argument to specify serving directory
- **Docker Integration** - Can run inside Docker container with volume mounting

#### Client

- **TCP Socket-based HTTP Client** - Makes HTTP requests using raw sockets
- **Command-line Interface** - Accepts host, port, URL, and download directory arguments
- **Path Normalization** - Normalizes URLs before sending requests
- **HTTP Redirect Following** - Automatically follows 301 redirects
- **HTML Display** - Prints HTML content directly to terminal with formatting
- **Binary File Download** - Saves PDF and PNG files to specified directory
- **Error Handling** - Connection error reporting, invalid directory detection, etc
- **Docker Integration** - Can run inside Docker container with volume mounting

****
<div style="display: flex; justify-content: center;">
<pre style="background: none;">
      |\      _,,,---,,_
ZZZzz /,`.-'`'    -.  ;-;;,_
     |,4-  ) )-,_. ,\ (  `'-'
    '---''(_/--'  `-'\_)</pre>
</div>
