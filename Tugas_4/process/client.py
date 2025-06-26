import sys
import socket
import json
import logging
import base64
import os

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

def make_socket(destination_address='localhost', port=12000):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_address = (destination_address, port)
        sock.connect(server_address)
        return sock
    except Exception as ee:
        logging.error(f"Error connecting to server: {str(ee)}")
        return None

def send_request(request_str, server_host, server_port):
    sock = make_socket(server_host, server_port)
    if not sock:
        return ""
    try:
        # Kirim request
        sock.sendall(request_str.encode())
        
        # === INI JUGA KUNCI: Beri sinyal bahwa client selesai mengirim ===
        sock.shutdown(socket.SHUT_WR)
        
        # Tunggu balasan dari server
        data_received = b""
        while True:
            part = sock.recv(2048)
            if not part:
                break
            data_received += part
        
        return data_received.decode('utf-8', 'ignore')
    except Exception as ee:
        logging.error(f"Error during communication: {str(ee)}")
        return ""
    finally:
        sock.close()

# ... sisa file tidak berubah ...
def parse_and_print_response(response_str):
    if not response_str:
        logging.warning("No response from server.")
        return
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

def list_files_on_server(host, port):
    logging.info("Requesting file list...")
    request = f"GET /api/list HTTP/1.1\r\nHost: {host}\r\n\r\n"
    response = send_request(request, host, port)
    parse_and_print_response(response)

def upload_file_to_server(host, port, filepath):
    if not os.path.exists(filepath):
        logging.error(f"File not found: {filepath}")
        return
    filename = os.path.basename(filepath)
    logging.info(f"Uploading '{filename}'...")
    with open(filepath, 'rb') as f:
        file_content_binary = f.read()
    encoded_content = base64.b64encode(file_content_binary)
    body = encoded_content.decode('utf-8')
    request = (
        f"POST /api/upload HTTP/1.1\r\n"
        f"Host: {host}\r\n"
        f"X-File-Name: {filename}\r\n"
        f"Content-Length: {len(body)}\r\n\r\n"
        f"{body}"
    )
    response = send_request(request, host, port)
    parse_and_print_response(response)

def delete_file_on_server(host, port, filename):
    logging.info(f"Deleting '{filename}'...")
    request = f"DELETE /api/delete/{filename} HTTP/1.1\r\nHost: {host}\r\n\r\n"
    response = send_request(request, host, port)
    parse_and_print_response(response)

if __name__ == '__main__':
    HOST = '127.0.0.1'
    TEST_FILENAME = "dokumen_tugas_final.txt"
    def run_test_scenario(port):
        print(f"\n\n===== STARTING CLIENT TEST ON PORT {port} =====\n")
        with open(TEST_FILENAME, "w") as f:
            f.write("Ini adalah isi dari file percobaan.")
        list_files_on_server(HOST, port)
        upload_file_to_server(HOST, port, TEST_FILENAME)
        list_files_on_server(HOST, port)
        delete_file_on_server(HOST, port, TEST_FILENAME)
        list_files_on_server(HOST, port)
        delete_file_on_server(HOST, port, TEST_FILENAME)
        os.remove(TEST_FILENAME)
        print(f"\n===== CLIENT TEST ON PORT {port} COMPLETE =====\n")
    
    run_test_scenario(port=9002)