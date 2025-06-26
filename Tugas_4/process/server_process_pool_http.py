import socket
import os
import json
import base64
from concurrent.futures import ProcessPoolExecutor

def process_worker_task(client_connection, client_address):
    worker_pid = os.getpid()
    print(f"[PEKERJA {worker_pid}] Menerima tugas untuk {client_address}")
    
    try:
        # Gunakan loop untuk memastikan semua request terbaca
        request_data = bytearray()
        while True:
            part = client_connection.recv(4096)
            if not part:
                break
            request_data.extend(part)

        if not request_data:
            return

        request_string = request_data.decode('utf-8', 'ignore')
        lines = request_string.split('\r\n')
        request_line = lines[0]
        parts = request_line.split()
        if len(parts) < 3:
            return
        
        http_method, url_path, _ = parts
        
        headers = {}
        body_start_pos = request_string.find('\r\n\r\n') + 4
        for line in request_string[:body_start_pos].split('\r\n')[1:]:
            if ": " in line:
                key, value = line.split(": ", 1)
                headers[key] = value
        request_body = request_data[body_start_pos:]
        
        # Logika endpoint (tidak berubah)
        if http_method == 'GET' and url_path == '/api/list':
            file_list = os.listdir('storage')
            json_body = json.dumps({"result": "success", "data": file_list})
            full_response = f"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: {len(json_body)}\r\n\r\n{json_body}"
        elif http_method == 'POST' and url_path == '/api/upload':
            file_to_upload = headers.get('X-File-Name')
            if file_to_upload:
                file_path_on_server = os.path.join('storage', file_to_upload)
                decoded_content = base64.b64decode(request_body)
                with open(file_path_on_server, 'wb') as f:
                    f.write(decoded_content)
                json_body = json.dumps({"result": "success", "details": f"File '{file_to_upload}' telah diterima."})
                full_response = f"HTTP/1.1 201 Created\r\nContent-Type: application/json\r\nContent-Length: {len(json_body)}\r\n\r\n{json_body}"
        elif http_method == 'DELETE' and url_path.startswith('/api/delete/'):
            file_to_delete = url_path.split('/')[-1]
            file_path_on_server = os.path.join('storage', file_to_delete)
            if os.path.exists(file_path_on_server):
                os.remove(file_path_on_server)
                json_body = json.dumps({"result": "success", "details": f"File '{file_to_delete}' telah dihapus."})
                full_response = f"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: {len(json_body)}\r\n\r\n{json_body}"
            else:
                json_body = json.dumps({"result": "error", "details": f"File '{file_to_delete}' tidak ada."})
                full_response = f"HTTP/1.1 404 Not Found\r\nContent-Type: application/json\r\nContent-Length: {len(json_body)}\r\n\r\n{json_body}"
        else:
            full_response = "HTTP/1.1 404 Not Found\r\n\r\nEndpoint tidak dikenali."

        # Kirim response
        client_connection.sendall(full_response.encode('utf-8'))
        
        # === INI KUNCINYA UNTUK MENGHINDARI RACE CONDITION ===
        # Beri sinyal bahwa server selesai mengirim, ini akan "memaksa" OS mengirim buffer
        client_connection.shutdown(socket.SHUT_WR)
        
    except Exception as e:
        print(f"[PEKERJA {worker_pid}] Terjadi error: {e}")
    finally:
        client_connection.close()
        print(f"[PEKERJA {worker_pid}] Tugas untuk {client_address} selesai, koneksi ditutup.")

def main():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(('0.0.0.0', 9002))
    server_socket.listen(10)
    
    if not os.path.exists('storage'):
        os.makedirs('storage')

    print("Process Pool Server (Model Benar) aktif di port 9002...")

    with ProcessPoolExecutor(max_workers=10) as executor:
        while True:
            conn, addr = server_socket.accept()
            executor.submit(process_worker_task, conn, addr)

if __name__ == "__main__":
    main()