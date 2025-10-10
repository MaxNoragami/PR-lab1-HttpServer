import socket
import os
import argparse
import urllib.parse


def normalize_path(path):
    segments = [seg for seg in path.split('/') if seg]

    normalized_segments = []
    for segment in segments:
        if len(segment) >= 3 and segment == '.' * len(segment):
            continue
        normalized_segments.append(segment)

    return '/' + '/'.join(normalized_segments)


def parse_http_response(response):
    try:
        header_end = response.find(b'\r\n\r\n')
        if header_end == -1:
            return None, {}, b''

        header_part = response[:header_end].decode('utf-8')
        body_part = response[header_end + 4:]

        lines = header_part.split('\r\n')
        status_line = lines[0]
        status_code = int(status_line.split()[1])

        headers = {}
        for line in lines[1:]:
            if ':' in line:
                key, value = line.split(':', 1)
                headers[key.strip().lower()] = value.strip()

        return status_code, headers, body_part
    except (ValueError, IndexError):
        return None, {}, b''


def get_file_extension(parsed_path):
    if '.' in parsed_path:
        return parsed_path.split('.')[-1].lower()
    return None


def make_http_request(host, port, normalized_path, max_redirects=5):
    current_path = normalized_path

    for redirect_count in range(max_redirects + 1):
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect((host, port))

            encoded_path = urllib.parse.quote(current_path, safe='/')

            request = f"GET {encoded_path} HTTP/1.1\r\nHost: {host}\r\nConnection: close\r\n\r\n"
            client_socket.send(request.encode())

            response = b''
            while True:
                data = client_socket.recv(4096)
                if not data:
                    break
                response += data

            client_socket.close()

            status_code, headers, body = parse_http_response(response)

            if status_code is None:
                print("Error: Could not parse HTTP response")
                return None, {}, b''

            if status_code in [301, 302, 307, 308]:
                location = headers.get('location')
                if location:
                    print(f"Redirected to: {location}")
                    current_path = normalize_path(location)
                    continue
                else:
                    print("Redirect without Location header")
                    return status_code, headers, body

            return status_code, headers, body
        except socket.error as e:
            print(f"Error connecting to server: {e}")
            return None, {}, b''

    print(f"Too many redirects (>{max_redirects})")
    return None, {}, b''


def save_file(content, directory, normalized_path):
    if not os.path.exists(directory):
        print(f"Error: Directory '{directory}' does not exist")
        return

    filename = os.path.basename(normalized_path)
    filepath = os.path.join(directory, filename)

    try:
        with open(filepath, 'wb') as f:
            f.write(content)
        print(f"File saved: {filepath}")
    except PermissionError:
        print(f"Error: Permission denied - cannot write to '{filepath}'")
        print("Check if the directory is writable or run with appropriate permissions")
    except OSError as e:
        print(f"Error: Could not save file '{filepath}': {e}")
    except Exception as e:
        print(f"Unexpected error saving file '{filepath}': {e}")


def main():
    parser = argparse.ArgumentParser(description="Simple HTTP Client")
    parser.add_argument("-H", "--host", required=True, help="Server hostname or IP address")
    parser.add_argument("-p", "--port", type=int, required=True, help="Server port number")
    parser.add_argument("-u", "--url", required=True, help="URL path to request")
    parser.add_argument("-d", "--directory", required=True, help="Directory to save files")

    args = parser.parse_args()

    parsed_url = urllib.parse.urlparse(args.url)
    normalized_path = normalize_path(parsed_url.path)

    status_code, headers, body = make_http_request(args.host, args.port, normalized_path)
    if status_code is None:
        return

    print(f"HTTP {status_code}")

    if status_code != 200:
        print(f"Error response: {body.decode('utf-8', errors='ignore')}")
        return

    file_extension = get_file_extension(normalized_path)
    content_type = headers.get('content-type', '').lower()

    if (file_extension == 'html' or
            content_type.startswith('text/html')):
        print("HTML Content:")
        print("=" * 50)
        print(body.decode('utf-8', errors='ignore'))
    elif file_extension in ['png', 'pdf']:
        save_file(body, args.directory, normalized_path)
    else:
        print(f"Unknown file type: {file_extension}")
        print("Content preview:")
        print(body[:200].decode('utf-8', errors='ignore'))


if __name__ == "__main__":
    main()
