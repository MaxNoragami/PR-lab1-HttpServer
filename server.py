import socket

def run_server():
    html_file = open("hello.html", "r")
    html_content = html_file.read()
    html_file.close()

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('0.0.0.0', 1337))

    server.listen(1)

    print("Server listening on port 1337")

    while True:
        client, addr = server.accept()
        print(f"Connection from {addr}")
        print(client.recv(1024).decode())
        client.send(html_content.encode())
        client.close()

run_server()