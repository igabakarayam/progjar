import os
import socket
import json
import base64
import logging
from multiprocessing import Process, Manager
import signal
import sys

SERVER_HOST = '0.0.0.0'
SERVER_PORT = 6665
SERVER_WORKER_LIMIT = 50  # Jumlah maksimum worker aktif secara bersamaan

logging.basicConfig(level=logging.WARNING)

def handle_client(conn, addr, stats):
    try:
        buffer = ""
        while True:
            data = conn.recv(4096)
            if not data:
                break
            buffer += data.decode()
            if "\r\n\r\n" in buffer:
                break

        command_str = buffer.strip().split("\r\n\r\n")[0]
        command_json = json.loads(command_str)
        logging.warning(f"Processing from {addr}: {command_json}")

        command = command_json.get('command')
        filename = command_json.get('filename')

        if command == 'UPLOAD':
            filedata = command_json.get('filedata')
            if not filename or not filedata:
                response = {'status': 'ERROR', 'data': 'Missing filename or filedata'}
                stats['fail'] += 1
            else:
                filebytes = base64.b64decode(filedata)
                os.makedirs('server_files', exist_ok=True)
                filepath = os.path.join('server_files', filename)
                with open(filepath, 'wb') as f:
                    f.write(filebytes)
                response = {'status': 'OK', 'data': f'File {filename} uploaded'}
                stats['success'] += 1

        elif command == 'GET':
            if not filename:
                response = {'status': 'ERROR', 'data': 'Missing filename'}
                stats['fail'] += 1
            else:
                filepath = os.path.join('server_files', filename)
                if not os.path.exists(filepath):
                    response = {'status': 'ERROR', 'data': 'File not found'}
                    stats['fail'] += 1
                else:
                    with open(filepath, 'rb') as f:
                        content = f.read()
                    encoded = base64.b64encode(content).decode()
                    response = {'status': 'OK', 'filedata': encoded}
                    stats['success'] += 1
        else:
            response = {'status': 'ERROR', 'data': 'Unknown command'}
            stats['fail'] += 1

    except Exception as e:
        logging.warning(f"Error handling client {addr}: {e}")
        response = {'status': 'ERROR', 'data': str(e)}
        stats['fail'] += 1

    response_str = json.dumps(response) + "\r\n\r\n"
    try:
        conn.sendall(response_str.encode())
    except Exception as e:
        logging.warning(f"Error sending response to {addr}: {e}")
    finally:
        conn.close()

def start_server():
    manager = Manager()
    stats = manager.dict()
    stats['success'] = 0
    stats['fail'] = 0

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((SERVER_HOST, SERVER_PORT))
    server_socket.listen(100)
    logging.warning(f"Server listening on {SERVER_HOST}:{SERVER_PORT} with multiprocessing")

    active_processes = []

    def shutdown_handler(sig, frame):
        print("\nShutting down server...")
        for p in active_processes:
            if p.is_alive():
                p.terminate()
        server_socket.close()
        print(f"Jumlah worker pool server:\t{SERVER_WORKER_LIMIT}")
        print(f"Jumlah worker sukses:\t{stats['success']}")
        print(f"Jumlah worker gagal:\t{stats['fail']}")
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown_handler)

    while True:
        conn, addr = server_socket.accept()
        logging.warning(f"Connection from {addr}")
        if len(active_processes) >= SERVER_WORKER_LIMIT:
            logging.warning("Server worker limit reached. Dropping connection.")
            conn.close()
            continue

        p = Process(target=handle_client, args=(conn, addr, stats))
        p.start()
        active_processes.append(p)

        # Clean up finished processes
        active_processes = [proc for proc in active_processes if proc.is_alive()]

if __name__ == '__main__':
    start_server()
