import socket
import os
import mimetypes
import time
import urllib.parse
import argparse

ADDRESS = "0.0.0.0"
PORT = 1337
VALID_EXTENSIONS = ["png", "pdf", "html"]

def respond(client, status, head, body):
    if isinstance(body, str):
        body_bytes = body.encode()
    else:
        body_bytes = body

    head["Content-Length"] = len(body_bytes)

    header = (f"HTTP/1.1 {status}\r\n" +
              f"\r\n".join(f"{key}: {value}" for key, value in head.items()) +
              f"\r\n\r\n")

    return client.send(header.encode() + body_bytes)

def respond_400(client):
    return respond(client,
                   "400 Bad Request",
                   {"Content-Type": "text/plain", "Connection": "close"},
                   "Bad Request")

def respond_404(client):
    return respond(client,
                   "404 Not Found",
                   {"Content-Type": "text/plain", "Connection": "close"},
                   "Not Found")

def respond_301(client, location):
    return respond(client,
                   "301 Moved Permanently",
                   {"Location": location, "Connection": "close"},
                   "")

def format_size(size):
    return (f"{size} B" if size < 1024 else
           f"{size/1024:.1f} KB" if size < 1024**2 else
           f"{size/1024**2:.1f} MB" if size < 1024**3 else
           f"{size/1024**3:.1f} GB")

def format_modified_time(timestamp):
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp))

def display_dir(actual_path, request_path):
    content = sorted(os.listdir(actual_path))
    filtered_content = []
    if request_path != '/':
        filtered_content.append(("⬆️", "../", "", ""))

    for item in content:
        item_path = os.path.join(actual_path, item)
        modified_time = format_modified_time(os.path.getmtime(item_path))
        if os.path.isdir(item_path):
            filtered_content.append(("📁", item + "/", modified_time, "-"))
        elif item.endswith(tuple(f".{ext}" for ext in VALID_EXTENSIONS)):
            file_type = ("📄" if item.endswith('.pdf') else
                         "🖼️" if item.endswith('.png') else
                         "🌐" if item.endswith('.html') else
                         "❓")
            size = format_size(os.path.getsize(item_path))
            filtered_content.append((file_type, item, modified_time, size))

    view = r"""
    <!DOCTYPE html>
<html>
<head>
    <meta charset='UTF-8'>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@picocss/pico@2/css/pico.jade.min.css">
    <link rel="icon" type="image/x-icon" href="https://files.catbox.moe/6u1gw2.ico">
    <title>=(^.^)= {path}</title></head>
<body>
    <main class="container">
        <h1 style="text-align: center;">{path}</h1>
        <div style="display: flex; justify-content: center;">
        <pre style="background: none;">
      |\      _,,,---,,_
ZZZzz /,`.-'`'    -.  ;-;;,_
     |,4-  ) )-,_. ,\ (  `'-'
    '---''(_/--'  `-'\_)</pre>
        </div>
    <div>
        <table class="striped">    
        <tr>
            <th></th>
            <th>Name</th>
            <th>Last Modified</th>
            <th>Size</th>
        </tr>    
        {items}
        </table>
    </div>
    </main>
</body>
</html>
    """
    if not request_path.endswith('/'):
        request_path += '/'
    return view.format(path=request_path, items="".join(f"<tr><td>{file_type}</td><td><a href='{request_path}{name}'>{name}</a></td><td>{modified}</td><td>{size}</td></tr>" for file_type, name, modified, size in filtered_content))

def normalize_path(path):
    segments = [seg for seg in path.split('/') if seg]

    normalized_segments = []
    for segment in segments:
        if len(segment) >= 3 and segment == '.' * len(segment):
            continue
        normalized_segments.append(segment)

    return '/' + '/'.join(normalized_segments)

def run_server():
    parser = argparse.ArgumentParser(description="Simple HTTP File Server")
    parser.add_argument("-d", "--directory", default=".",
                        help="Root dir to serve")
    args = parser.parse_args()
    root = os.path.abspath(args.directory)
    print(root)

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((ADDRESS, PORT))

    server.listen(1)

    print("Server listening on port 1337")

    while True:
        client, addr = server.accept()

        client_request = client.recv(1024).decode(errors='ignore')

        try:
            method, path, protocol = client_request.split("\r\n")[0].split(" ")
            path = urllib.parse.unquote(path)
        except ValueError:
            respond_400(client)
            client.close()
            continue

        if path == "/favicon.ico":
            client.close()
            continue

        print(f"Request: {method} {path} {protocol} from {addr}")
        print(f"Serving {path} to {addr}")

        original_path = path
        normalized_path = normalize_path(path)

        if original_path != normalized_path:
            respond_301(client, f"{normalized_path}")
            client.close()
            continue

        path = normalized_path
        actual_path = os.path.realpath(os.path.join(root, path.lstrip("/")))

        if not os.path.exists(actual_path):
            respond_404(client)
            client.close()
            continue

        if os.path.isdir(actual_path):
            content_type = "text/html"
            data = display_dir(actual_path, path)
        else:
            if not path.endswith(tuple(f".{ext}" for ext in VALID_EXTENSIONS)):
                respond_404(client)
                client.close()
                continue

            content_type, _ = mimetypes.guess_type(actual_path)
            with open(actual_path, "rb") as requested_file:
                data = requested_file.read()

        respond(client,
                "200 OK",
                {"Content-Type": content_type, "Connection": "close"},
                data)

        client.close()


run_server()
