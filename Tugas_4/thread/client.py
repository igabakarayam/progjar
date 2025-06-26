import socket
import json
import base64
import os

class HttpClient:
    def __init__(self, host='127.0.0.1', port=9001):
        self.host = host
        self.port = port

    def _send_request(self, request):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((self.host, self.port))
            s.sendall(request)
            
            response_data = bytearray()
            while True:
                part = s.recv(4096)
                if not part:
                    break
                response_data.extend(part)
        
        return self._parse_response(response_data)

    def _parse_response(self, response_data):
        response_str = response_data.decode('utf-8', 'ignore')
        parts = response_str.split('\r\n\r\n', 1)
        header_str = parts[0]
        body_str = parts[1] if len(parts) > 1 else ""

        print("\n--- SERVER RESPONSE ---")
        print(header_str)
        
        if body_str:
            print("\nBody:")
            try:
                parsed_json = json.loads(body_str)
                print(json.dumps(parsed_json, indent=4))
            except json.JSONDecodeError:
                print(body_str)
        print("---------------------\n")
        
        return header_str, body_str

    def list_files(self):
        print("[INFO] Requesting file list...")
        request = f"GET /api/list HTTP/1.1\r\nHost: {self.host}\r\n\r\n".encode('utf-8')
        return self._send_request(request)

    def upload_file(self, local_filepath):
        if not os.path.exists(local_filepath):
            print(f"[ERROR] File not found: {local_filepath}")
            return

        filename = os.path.basename(local_filepath)
        print(f"[INFO] Uploading '{filename}'...")

        with open(local_filepath, 'rb') as f:
            file_content = f.read()
        
        encoded_content = base64.b64encode(file_content)

        request_line = f"POST /api/upload HTTP/1.1\r\n"
        headers = (
            f"Host: {self.host}\r\n"
            f"X-File-Name: {filename}\r\n"
            f"Content-Length: {len(encoded_content)}\r\n"
            f"Connection: close\r\n\r\n"
        )
        
        request = (request_line + headers).encode('utf-8') + encoded_content
        return self._send_request(request)

    def delete_file(self, filename):
        print(f"[INFO] Deleting '{filename}'...")
        request = f"DELETE /api/delete/{filename} HTTP/1.1\r\nHost: {self.host}\r\n\r\n".encode('utf-8')
        return self._send_request(request)

def run_test(port, test_file):
    client = HttpClient(port=port)
    print(f"===== STARTING CLIENT TEST (Port: {port}) =====")

    print(f"[SETUP] Creating dummy file '{test_file}'")
    with open(test_file, 'w') as f:
        f.write("This is a test file for the assignment.")
    
    client.list_files()
    client.upload_file(test_file)
    client.list_files()
    client.delete_file(test_file)
    client.list_files()
    client.delete_file(test_file) # Mencoba hapus lagi untuk tes error
    
    if os.path.exists(test_file):
        os.remove(test_file)
    
    print("===== CLIENT TEST COMPLETE =====")

if __name__ == "__main__":
    TEST_FILENAME = "dokumen_percobaan.txt"
    
    # --- Uji Server Thread Pool ---
    print("\n\n--- TESTING THREAD POOL SERVER (PORT 9001) ---")
    run_test(port=9001, test_file=TEST_FILENAME)
    