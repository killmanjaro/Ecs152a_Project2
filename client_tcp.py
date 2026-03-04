import socket
import json
import sys

PROXY_HOST = '127.0.0.1'
PROXY_PORT = 8000

DEFAULT_SERVER_IP = '127.0.0.1'
DEFAULT_SERVER_PORT = 9000

def send_to_proxy(message, server_ip, server_port):
    payload = {
        "server_ip": server_ip,
        "server_port": server_port,
        "message": message
    }
    json_payload = json.dumps(payload)

    print(f"----------------------------")
    print(f"Sent to Proxy:")
    print(f"----------------------------")
    print(f"data = {{")
    print(f'  "server_ip": "{server_ip}"')
    print(f'  "server_port": {server_port}')
    print(f'  "message": "{message}"')
    print(f"}}")

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((PROXY_HOST, PROXY_PORT))
            sock.sendall(json_payload.encode())
            response = sock.recv(1024).decode()
            print(f"----------------------------")
            print(f"Received from Proxy:")
            print(f"----------------------------")
            print(f'"{response}"')
            return response
    except ConnectionRefusedError:
        print(f"Client: Error, connection refused")
    except TimeoutError:
        print(f"Client: Error, connection timed out")
    except OSError as e:
        print(f"Client: Network error, {e}")

def main():
    if len(sys.argv) < 2:
        print("Client: Error, Not enough arguments")
        sys.exit(1)

    message = sys.argv[1]
    server_ip = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_SERVER_IP
    server_port = int(sys.argv[3]) if len(sys.argv) > 3 else DEFAULT_SERVER_PORT

    if len(message) != 4 and message not in ("Ping", "Pong"):
        print(f"Client: Warning, '{message}' is not exactly 4 characters.")

    send_to_proxy(message, server_ip, server_port)

if __name__ == "__main__":
    main()