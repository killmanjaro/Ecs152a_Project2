import socket

HOST = '127.0.0.1'
PORT = 9000

def process_message(msg):
    if msg == "Ping":
        return "Pong"
    elif msg == "Pong":
        return "Ping"
    else:
        return msg[::-1]  # Reverse the 4-character string

def start_server():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_sock:
            server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_sock.bind((HOST, PORT))
            server_sock.listen(5)
            print(f"Server: Listening on {HOST}:{PORT}")

            while True:
                try:
                    conn, addr = server_sock.accept()
                    with conn:
                        print(f"Server: Connection from {addr}")
                        data = conn.recv(1024).decode()
                        print(f"Server: Received '{data}'")

                        response = process_message(data)
                        print(f"Server: Sending response '{response}'")
                        conn.sendall(response.encode())
                except ConnectionResetError:
                    print("Server: Error, connection refused")
                except OSError as e:
                    print("Server: Connection error, {e}")
    except OSError as e:
        print(f"Server: failed to start server {e}")
        
if __name__ == "__main__":
    start_server()

