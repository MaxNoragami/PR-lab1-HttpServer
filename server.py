import socket
import os
import mimetypes

ADDRESS = "127.0.0.1"
PORT = 1337
VALID_EXTENSIONS = ["png", "pdf", "html"]

def respond(client, status, head, body):
    header = (f"HTTP/1.1 {status}\r\n" +
                        f"\r\n".join(f"{key}: {value}" for key, value in head.items()) +
                        f"\r\n\r\n")

    if isinstance(body, str):
        return client.send((header + body).encode())
    else:
        return client.send(header.encode() + body)

def respond_400(client):
    return respond(client,
                   "400 Bad Request",
                   {"Content-Type": "text/plain", "Content-Length": 11, "Connection": "close"},
                   "Bad Request")

def respond_404(client):
    return respond(client,
                   "404 Not Found",
                   {"Content-Type": "text/plain", "Content-Length": 9, "Connection": "close"},
                   "Not Found")

def respond_301(client, location):
    return respond(client,
                   "301 Moved Permanently",
                   {"Location": location, "Content-Length": 0, "Connection": "close"},
                   "")


def display_dir(actual_path, request_path):
    content = sorted(os.listdir(actual_path))
    filtered_content = []

    for item in content:
        item_path = os.path.join(actual_path, item)
        if os.path.isdir(item_path):
            filtered_content.append(item + "/")
        elif item.endswith(tuple(f".{ext}" for ext in VALID_EXTENSIONS)):
            filtered_content.append(item)

    view = "<!DOCTYPE html><html><head><title>Index of {path}</title></head><body><h1>Index of {path}</h1><ul>{items}</ul></body></html>"
    if not request_path.endswith('/'):
        request_path += '/'
    return view.format(path=request_path, items="".join(f"<li><a href='http://{ADDRESS}:{PORT}{request_path}{item}'>{item}</a></li>" for item in filtered_content))


def run_server():
    root = "."
    root = os.path.abspath(root)
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
        normalized_path = '/' + '/'.join(filter(None, path.split('/')))

        if original_path != normalized_path:
            respond_301(client, f"http://{ADDRESS}:{PORT}{normalized_path}")
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
                {"Content-Type": content_type, "Content-Length": len(data), "Connection": "close"},
                data)

        client.close()


run_server()
