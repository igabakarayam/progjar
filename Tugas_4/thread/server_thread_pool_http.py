import socket
import threading
import os
import json
import base64
from concurrent.futures import ThreadPoolExecutor

class HttpServer:
    def __init__(self, host='0.0.0.0', port=9001): # Port diubah jadi 9001
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.storage_dir = 'storage'
        if not os.path.exists(self.storage_dir):
            os.makedirs(self.storage_dir)

    def start(self):
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        print(f"Thread Pool Server running on port {self.port}.")
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            while True:
                conn, addr = self.server_socket.accept()
                executor.submit(self.handle_request, conn, addr)

    def handle_request(self, conn, addr):
        print(f"Connection from {addr}")
        try:
            request_data = bytearray()
            while True:
                part = conn.recv(4096)
                request_data.extend(part)
                if len(part) < 4096:
                    break
            
            request_str = request_data.decode('utf-8', errors='ignore')
            lines = request_str.split('\r\n')
            request_line = lines[0]
            
            parts = request_line.split()
            if len(parts) < 2:
                conn.close()
                return

            method = parts[0]
            path = parts[1]

            headers = {}
            for line in lines[1:]:
                if line == "":
                    break
                header_parts = line.split(": ", 1)
                if len(header_parts) == 2:
                    headers[header_parts[0]] = header_parts[1]
            
            body_start_index = request_str.find('\r\n\r\n') + 4
            body = request_data[body_start_index:]

            # Endpoint diubah
            if method == 'GET' and path == '/api/list':
                self.list_files(conn)
            elif method == 'POST' and path == '/api/upload':
                self.upload_file(conn, headers, body)
            elif method == 'DELETE' and path.startswith('/api/delete/'):
                self.delete_file(conn, path)
            else:
                self.send_error(conn, 404, "Not Found")

        except Exception as e:
            print(f"Error handling request: {e}")
            self.send_error(conn, 500, "Internal Server Error")
        finally:
            conn.close()

    def list_files(self, conn):
        try:
            files = os.listdir(self.storage_dir)
            # Kunci JSON diubah
            response_body = json.dumps({"result": "success", "data": files})
            self.send_response(conn, 200, "OK", response_body, "application/json")
        except Exception as e:
            self.send_error(conn, 500, f"Failed to list files: {e}")

    def upload_file(self, conn, headers, body):
        try:
            # Header diubah
            filename = headers.get('X-File-Name')
            if not filename:
                self.send_error(conn, 400, "Bad Request: X-File-Name header missing")
                return

            filepath = os.path.join(self.storage_dir, filename)
            file_content = base64.b64decode(body)

            with open(filepath, 'wb') as f:
                f.write(file_content)
            
            # Kunci JSON diubah
            response_body = json.dumps({"result": "success", "details": f"File '{filename}' uploaded."})
            self.send_response(conn, 201, "Created", response_body, "application/json")

        except Exception as e:
            self.send_error(conn, 500, f"Failed to upload file: {e}")

    def delete_file(self, conn, path):
        try:
            filename = path.split('/')[-1]
            filepath = os.path.join(self.storage_dir, filename)

            if os.path.exists(filepath):
                os.remove(filepath)
                response_body = json.dumps({"result": "success", "details": f"File '{filename}' deleted."})
                self.send_response(conn, 200, "OK", response_body, "application/json")
            else:
                response_body = json.dumps({"result": "error", "details": f"File '{filename}' not found."})
                self.send_response(conn, 404, "Not Found", response_body, "application/json")
        except Exception as e:
            self.send_error(conn, 500, f"Failed to delete file: {e}")

    def send_response(self, conn, status_code, status_text, body, content_type):
        response = f"HTTP/1.1 {status_code} {status_text}\r\n"
        response += "Server: MyPythonServer/1.0\r\n"
        response += f"Content-Type: {content_type}\r\n"
        response += f"Content-Length: {len(body)}\r\n"
        response += "Connection: close\r\n\r\n"
        
        response_bytes = response.encode('utf-8')
        if isinstance(body, str):
            response_bytes += body.encode('utf-8')
        else:
            response_bytes += body
            
        conn.sendall(response_bytes)

    def send_error(self, conn, status_code, message):
        body = json.dumps({"result": "error", "details": message})
        self.send_response(conn, status_code, message.split(':')[0], body, "application/json")

if __name__ == "__main__":
    server = HttpServer()
    server.start()