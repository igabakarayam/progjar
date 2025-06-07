import socket
import logging

logging.basicConfig(level=logging.INFO)

try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    server_address = ('0.0.0.0', 10000)  
    logging.info(f"starting up on {server_address}")
    sock.bind(server_address)

    sock.listen(1)
    while True:
        logging.info("waiting for a connection")
        connection, client_address = sock.accept()
        logging.info(f"connection from {client_address}")

        while True:
            data = connection.recv(1024)
            if data:
                logging.info(f"received: {data.decode()}")
                connection.sendall(data)  # echo back
            else:
                break

        connection.close()

except Exception as ee:
    logging.info(f"ERROR: {str(ee)}")
finally:
    logging.info('closing')
    sock.close()
