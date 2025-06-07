import socket
import threading
import os
import base64
import json
import logging


# Folder penyimpanan file di server
SERVER_FILE_DIR = 'server_files'
os.makedirs(SERVER_FILE_DIR, exist_ok=True)


class ProcessTheClient(threading.Thread):
    def __init__(self, connection, address):
        threading.Thread.__init__(self)
        self.connection = connection
        self.address = address
        self.running = True


    def run(self):
        while self.running:
            try:
                data_received = ""
                while True:
                    data = self.connection.recv(1024)
                    if not data:
                        break
                    data_received += data.decode()
                    if "\r\n\r\n" in data_received:
                        break


                if data_received:
                    logging.warning(f"memproses request: {data_received.strip()}")
                    hasil = self.process_command(data_received.strip())
                    response = json.dumps(hasil) + "\r\n\r\n"
                    self.connection.sendall(response.encode())
                break


            except Exception as e:
                logging.warning(f"error during processing: {e}")
                break


    def process_command(self, command_str):
        tokens = command_str.strip().split(" ", 2)
        if not tokens:
            return {'status': 'ERROR', 'data': 'No command'}


        cmd = tokens[0].upper()
        logging.warning(f"string diproses: {command_str}")


        if cmd == 'LIST':
            files = os.listdir(SERVER_FILE_DIR)
            return {'status': 'OK', 'data': files}


        elif cmd == 'UPLOAD' and len(tokens) == 3:
            filename = tokens[1]
            filedata = base64.b64decode(tokens[2])
            filepath = os.path.join(SERVER_FILE_DIR, filename)
            with open(filepath, 'wb') as f:
                f.write(filedata)
            return {'status': 'OK', 'data': f'{filename} uploaded'}


        elif cmd == 'DELETE' and len(tokens) >= 2:
            filename = tokens[1]
            filepath = os.path.join(SERVER_FILE_DIR, filename)
            if os.path.exists(filepath):
                os.remove(filepath)
                return {'status': 'OK', 'data': f'{filename} deleted'}
            else:
                return {'status': 'ERROR', 'data': 'File not found'}


        elif cmd == 'GET' and len(tokens) >= 2:
            filename = tokens[1]
            filepath = os.path.join(SERVER_FILE_DIR, filename)
            if os.path.exists(filepath):
                with open(filepath, 'rb') as f:
                    filedata = base64.b64encode(f.read()).decode()
                return {
                    'status': 'OK',
                    'data_namafile': filename,
                    'data_file': filedata
                }
            else:
                return {'status': 'ERROR', 'data': 'File not found'}


        else:
            return {'status': 'ERROR', 'data': 'Unknown command'}


class Server:
    def __init__(self, ip_address='0.0.0.0', port=6665):
        self.the_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.ip_address = ip_address
        self.port = port
        self.the_server.bind((self.ip_address, self.port))
        self.the_server.listen(5)
        logging.warning(f"Server listening on {self.ip_address}:{self.port}")


    def run(self):
        try:
            while True:
                conn, addr = self.the_server.accept()
                logging.warning(f"connection from {addr}")
                clt = ProcessTheClient(conn, addr)
                clt.start()
        except KeyboardInterrupt:
            self.the_server.close()
            logging.warning("Server stopped manually")


if __name__ == '__main__':
    logging.basicConfig(level=logging.WARNING)
    svr = Server()
    svr.run()


