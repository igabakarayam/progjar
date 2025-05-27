import os
import socket
import json
import base64
import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

SERVER_ADDRESS = ('127.0.0.1', 6665)

FILES_TO_TEST = [
    'test_10mb.bin'
]

CLIENT_WORKERS = 50  # Jumlah client worker pool
SERVER_WORKER_POOL_SIZE = 5  # Cocokkan dengan server

logging.basicConfig(level=logging.INFO)

def send_command_json(command_obj):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(220)
    try:
        sock.connect(SERVER_ADDRESS)
        command_str = json.dumps(command_obj) + "\r\n\r\n"
        sock.sendall(command_str.encode())

        data_received = ""
        while True:
            data = sock.recv(4096)
            if not data:
                break
            data_received += data.decode()
            if "\r\n\r\n" in data_received:
                break

        if not data_received:
            return None

        response_str = data_received.strip().split("\r\n\r\n")[0]
        return json.loads(response_str)
    except Exception as e:
        return {'status': 'ERROR', 'data': str(e)}
    finally:
        sock.close()

def task_upload(worker_id, filename):
    try:
        filepath = os.path.join('files', filename)
        with open(filepath, 'rb') as f:
            content = f.read()
        encoded_content = base64.b64encode(content).decode()
        logging.info(f"Worker {worker_id}: Read file {filename} size {len(content)} bytes")

        command = {
            'command': 'UPLOAD',
            'filename': filename,
            'filedata': encoded_content
        }

        start = time.time()
        result = send_command_json(command)
        end = time.time()

        if result.get('status') == 'OK':
            logging.info(f"Worker {worker_id}: Upload success for {filename}")
            return (True, end - start, len(content))
        else:
            logging.error(f"Worker {worker_id}: Upload failed for {filename} with message: {result.get('data')}")
            return (False, end - start, 0)

    except Exception as e:
        logging.error(f"Worker {worker_id}: Exception {e}")
        return (False, 0, 0)

def task_download(worker_id, filename):
    try:
        command = {'command': 'GET', 'filename': filename}
        start = time.time()
        result = send_command_json(command)
        end = time.time()

        if result.get('status') == 'OK':
            content = base64.b64decode(result['filedata'])
            os.makedirs('downloads', exist_ok=True)
            filepath = os.path.join('downloads', filename)
            with open(filepath, 'wb') as f:
                f.write(content)

            logging.info(f"Worker {worker_id}: Download success for {filename}, saved to {filepath}")
            return (True, end - start, len(content))
        else:
            logging.error(f"Worker {worker_id}: Download failed for {filename} with message: {result.get('data')}")
            return (False, end - start, 0)
    except Exception as e:
        logging.error(f"Worker {worker_id}: Exception {e}")
        return (False, 0, 0)

def run_operation(filename, operation, workers):
    print(f"\nStarting {operation} for file: {filename} with {workers} workers")
    task_func = task_upload if operation == 'UPLOAD' else task_download

    total_success = 0
    total_fail = 0
    total_bytes = 0
    total_time = []

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [executor.submit(task_func, i, filename) for i in range(workers)]
        for future in as_completed(futures):
            success, elapsed, nbytes = future.result()
            if success:
                total_success += 1
                total_bytes += nbytes
                total_time.append(elapsed)
            else:
                total_fail += 1

    avg_time = sum(total_time) / total_success if total_success else 0
    throughput = total_bytes / sum(total_time) if total_time else 0

    return {
        'operation': operation,
        'filename': filename,
        'workers': workers,
        'success': total_success,
        'fail': total_fail,
        'avg_time': avg_time,
        'throughput': throughput
    }

if __name__ == '__main__':
    report = []
    nomor = 1

    for filename in FILES_TO_TEST:
        # Upload
        upload_stats = run_operation(filename, 'UPLOAD', CLIENT_WORKERS)
        # Download
        download_stats = run_operation(filename, 'DOWNLOAD', CLIENT_WORKERS)

        report.append((nomor, upload_stats))
        nomor += 1
        report.append((nomor, download_stats))
        nomor += 1

    # Print report tab-separated for Excel
    print("\n=== FINAL REPORT ===")
    print("\n=== FINAL REPORT ===")
    print("Nomor;Operasi;Volume;Jumlah client worker pool;Jumlah server worker pool;Waktu total per client (s);Throughput per client (bytes/s);Jumlah worker client sukses;Jumlah worker client gagal;Jumlah worker server sukses;Jumlah worker server gagal")
    
    for nomor, stats in report:
        volume = stats['filename']
        operasi = stats['operation']
        client_workers = stats['workers']
        server_workers = SERVER_WORKER_POOL_SIZE
        waktu = f"{stats['avg_time']:.2f}"
        throughput = f"{stats['throughput']:.2f}"
        success = stats['success']
        fail = stats['fail']
    
        # Server success/fail per file tidak tersedia, isi '-'
        server_success = '-'
        server_fail = '-'
    
        print(f"{nomor};{operasi};{volume};{client_workers};{server_workers};{waktu};{throughput};{success};{fail};{server_success};{server_fail}")
