import os
import socket
import json
import base64
import logging
import threading
from concurrent.futures import ThreadPoolExecutor
import atexit

SERVER_HOST = '0.0.0.0'
SERVER_PORT = 6665
SERVER_WORKER_POOL_SIZE = 1  # Atur sesuai kebutuhan

server_success_count = 0
server_fail_count = 0
server_lock = threading.Lock()

logging.basicConfig(level=logging.WARNING)

class ClientHandler:
    def __init__(self, connection, address):
        self.connection = connection
        self.address = address

    def receive_full_message(self):
        buffer = ""
        while True:
            data = self.connection.recv(4096)
            if not data:
                break
            buffer += data.decode()
            if "\r\n\r\n" in buffer:
                break
        return buffer.strip().split("\r\n\r\n")[0]

    def send_response(self, response_obj):
        response_str = json.dumps(response_obj) + "\r\n\r\n"
        self.connection.sendall(response_str.encode())

    def process_command(self, command_json):
        try:
            command = command_json.get('command')
            filename = command_json.get('filename')

            if command == 'UPLOAD':
                filedata = command_json.get('filedata')
                if not filename or not filedata:
                    return {'status': 'ERROR', 'data': 'Missing filename or filedata'}

                filebytes = base64.b64decode(filedata)
                os.makedirs('server_files', exist_ok=True)
                filepath = os.path.join('server_files', filename)
                with open(filepath, 'wb') as f:
                    f.write(filebytes)
                return {'status': 'OK', 'data': f'File {filename} uploaded'}

            elif command == 'GET':
                if not filename:
                    return {'status': 'ERROR', 'data': 'Missing filename'}

                filepath = os.path.join('server_files', filename)
                if not os.path.exists(filepath):
                    return {'status': 'ERROR', 'data': 'File not found'}

                with open(filepath, 'rb') as f:
                    content = f.read()
                encoded_content = base64.b64encode(content).decode()
                return {'status': 'OK', 'filedata': encoded_content}

            else:
                return {'status': 'ERROR', 'data': 'Unknown command'}

        except Exception as e:
            return {'status': 'ERROR', 'data': str(e)}

    def handle(self):
        global server_success_count, server_fail_count
        try:
            command_str = self.receive_full_message()
            if not command_str:
                raise Exception("Empty command received")
            command_json = json.loads(command_str)
            logging.warning(f"string diproses: {command_json}")

            response = self.process_command(command_json)

            with server_lock:
                if response.get('status') == 'OK':
                    server_success_count += 1
                else:
                    server_fail_count += 1

            self.send_response(response)
        except Exception as e:
            with server_lock:
                server_fail_count += 1
            logging.warning(f"error during processing: {e}")
        finally:
            self.connection.close()

class Server:
    def __init__(self, ip_address=SERVER_HOST, port=SERVER_PORT, max_workers=SERVER_WORKER_POOL_SIZE):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((ip_address, port))
        self.server_socket.listen(100)
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        logging.warning(f"Server listening on {ip_address}:{port} with {max_workers} workers")

    def serve_forever(self):
        try:
            while True:
                conn, addr = self.server_socket.accept()
                logging.warning(f"Connection from {addr}")
                handler = ClientHandler(conn, addr)
                self.executor.submit(handler.handle)
        except KeyboardInterrupt:
            print("\nServer stopped by user.")
        finally:
            self.server_socket.close()

def print_server_report():
    print("\n=== SERVER REPORT ===")
    print(f"Jumlah worker pool server:\t{SERVER_WORKER_POOL_SIZE}")
    print(f"Jumlah worker sukses:\t{server_success_count}")
    print(f"Jumlah worker gagal:\t{server_fail_count}")

atexit.register(print_server_report)

if __name__ == '__main__':
    server = Server()
    server.serve_forever()


