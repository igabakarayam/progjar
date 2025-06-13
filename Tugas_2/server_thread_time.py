from socket import *
import socket
import threading
import logging
from datetime import datetime

def proses_string(request_string):
    balas = "ERROR\r\n"
    if request_string.startswith("TIME") and request_string.endswith("\r\n"):
        now = datetime.now()
        waktu = now.strftime("%H:%M:%S")
        balas = f"JAM {waktu}\r\n"
    elif request_string.startswith("QUIT") and request_string.endswith("\r\n"):
        balas = "XXX"
    return balas

class ProcessTheClient(threading.Thread):
    def __init__(self, connection, address):
        self.connection = connection
        self.address = address
        threading.Thread.__init__(self)

    def run(self):
        while True:
            try:
                data = self.connection.recv(1024)
                if data:
                    request_s = data.decode()
                    logging.warning(f"Received from {self.address}: {repr(request_s)}")
                    balas = proses_string(request_s)
                    if balas == "XXX":
                        self.connection.close()
                        break
                    self.connection.sendall(balas.encode())
                else:
                    break
            except Exception as e:
                logging.error(f"Error: {e}")
                break
        self.connection.close()

class Server(threading.Thread):
    def __init__(self):
        self.the_clients = []
        self.my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        threading.Thread.__init__(self)

    def run(self):
        self.my_socket.bind(('0.0.0.0', 45000))
        self.my_socket.listen(5)
        logging.warning("Server listening on port 45000...")
        while True:
            connection, client_address = self.my_socket.accept()
            logging.warning(f"Connection from {client_address}")
            clt = ProcessTheClient(connection, client_address)
            clt.start()
            self.the_clients.append(clt)

def main():
    logging.basicConfig(level=logging.WARNING, format='%(asctime)s - %(message)s')
    svr = Server()
    svr.start()

if __name__ == "__main__":
    main()
