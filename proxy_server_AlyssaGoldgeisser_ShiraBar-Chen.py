import socket
import json

PROXY_HOST = '127.0.0.1'
PROXY_PORT = 8000

SERVER_PORT = 7000  # Default server port

# Sample IP Blocklist
IP_BLOCKLIST = {
    "192.168.1.100",
    "10.0.0.5",
    "172.16.0.1",
    "203.0.113.42",
    "198.51.100.7",
}

def forward_to_server(server_ip, server_port, message):
    """Forward the message to the actual server and return its response."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((server_ip, server_port))
            proxy_ip = sock.getsockname()[0]
            payload = json.dumps({"proxy_ip": proxy_ip, "message": message})
            print(f"----------------------------")
            print(f"Sent to Server:")
            print(f"----------------------------")
            print(f'"{message}"')
            sock.sendall(payload.encode())
            response = sock.recv(1024).decode()
            print(f"----------------------------")
            print(f"Received from Server:")
            print(f"----------------------------")
            print(f'"{response}"')
            return response
    except ConnectionRefusedError:
        print(f"Proxy: Error, Could not connect to server at {server_ip}:{server_port}.")
        return "Server Connection Error"
    except TimeoutError:
        print(f"Proxy: Error, Connection to server timed out.")
        return "Server Timeout Error"
    except OSError as e:
        print(f"Proxy: Network error when contacting server: {e}")
        return f"Server Network Error: {e}"

def handle_client(conn, addr):
    with conn:
        raw_data = conn.recv(4096).decode()

        try:
            payload = json.loads(raw_data)
            server_ip = payload.get("server_ip")
            server_port = payload.get("server_port", SERVER_PORT)
            message = payload.get("message")

            if not server_ip or not message:
                error = "Invalid JSON: missing 'server_ip' or 'message'"
                print(f"Proxy: Error: {error}")
                conn.sendall(error.encode())
                return

            print(f"----------------------------")
            print(f"Received from Client:")
            print(f"----------------------------")
            print(f"data = {{")
            print(f'  "server_ip": "{server_ip}"')
            print(f'  "server_port": {server_port}')
            print(f'  "message": "{message}"')
            print(f"}}")

            # Check blocklist
            if server_ip in IP_BLOCKLIST:
                response = "Blocklist Error"
                print(f"Proxy: {server_ip} is BLOCKED. Replying with: '{response}'")
                conn.sendall(response.encode())
                return

            # Forward to server
            response = forward_to_server(server_ip, server_port, message)
            print(f"----------------------------")
            print(f"Sent to Client:")
            print(f"----------------------------")
            print(f'"{response}"')
            conn.sendall(response.encode())

        except json.JSONDecodeError as e:
            error = f"JSON Parse Error: {e}"
            print(f"Proxy: {error}")
            conn.sendall(error.encode())

def start_proxy():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as proxy_sock:
            proxy_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            proxy_sock.bind((PROXY_HOST, PROXY_PORT))
            proxy_sock.listen(5)
            print(f"Proxy: Listening on {PROXY_HOST}:{PROXY_PORT}")
            print(f"Proxy: Blocked IPs: {IP_BLOCKLIST}\n")

            while True:
                try:
                    conn, addr = proxy_sock.accept()
                    handle_client(conn, addr)
                except ConnectionResetError:
                    print("Proxy: Error: Client disconnected unexpectedly.")
                except OSError as e:
                    print(f"Proxy: Connection error: {e}")
    except OSError as e:
        print(f"Proxy: Failed to start proxy on {PROXY_HOST}:{PROXY_PORT}, error: {e}")

if __name__ == "__main__":
    start_proxy()