import socket
import json
import sys

PROXY_HOST = '127.0.0.1'
PROXY_PORT = 8000

DEFAULT_SERVER_IP = '127.0.0.1'  # The actual server's IP

def send_to_proxy(message, server_ip):
    payload = {
        "server_ip": server_ip,
        "message": message
    }
    json_payload = json.dumps(payload)

    print(f"Client: Sending to proxy at {PROXY_HOST}:{PROXY_PORT}")
    print(f"Client: JSON payload: {json_payload}")

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((PROXY_HOST, PROXY_PORT))
            sock.sendall(json_payload.encode())
            response = sock.recv(1024).decode()
            print(f"Client: Response received: '{response}'")
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
    if len(sys.argv) > 2:
        server_ip = sys.argv[2]
    else:
        server_ip = DEFAULT_SERVER_IP

    if len(message) != 4:
        print(f"Client: Warning, '{message}' is not exactly 4 characters.")

    print(f"Client: Input message - '{message}' ")
    print(f"Client: Target server IP - {server_ip}")
    send_to_proxy(message, server_ip)

if __name__ == "__main__":
    main()

