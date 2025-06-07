import socket
import json
import base64
import logging


server_address = ('172.16.16.101', 6665)








def send_command(command_str=""):
    global server_address
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(5)  # Set timeout to avoid indefinite blocking


    try:
        sock.connect(server_address)
        logging.warning(f"connecting to {server_address}")


        logging.warning(f"sending message")
        sock.sendall(command_str.encode())


        # Look for the response, waiting until socket is done (no more data)
        data_received = ""  # empty string
        while True:
            try:
                data = sock.recv(1024)
                if data:
                    data_received += data.decode()
                    if "\r\n\r\n" in data_received:
                        break
                else:
                    break
            except socket.timeout:
                logging.warning("socket timeout during recv")
                break


        if not data_received:
            raise Exception("No data received")


        hasil = json.loads(data_received)
        logging.warning("data received from server:")
        return hasil


    except Exception as e:
        logging.warning(f"error during data receiving: {e}")
        return False


    finally:
        sock.close()


def remote_list():
    command_str = f"LIST"
    hasil = send_command(command_str)
    if hasil and hasil.get('status') == 'OK':
        print("daftar file : ")
        for nmfile in hasil['data']:
            print(f"- {nmfile}")
        return True
    else:
        print("[!] Gagal mengambil daftar file")
        return False


def remote_upload(filename=""):
    try:
        with open(f'files/{filename}', 'rb') as f:
            content = f.read()
            encoded_content = base64.b64encode(content).decode()
    except Exception as e:
        print(f"Error baca file: {e}")
        return False


    command_str = f"UPLOAD {filename} {encoded_content}"
    hasil = send_command(command_str)
    if hasil and hasil.get('status') == 'OK':
        print("[+] File uploaded successfully")
        return True
    else:
        print("[!] Upload failed:", hasil['data'] if hasil else 'No response from server')
        return False


def remote_delete(filename=""):
    command_str = f"DELETE {filename}"
    hasil = send_command(command_str)
    if hasil and hasil.get('status') == 'OK':
        print("[+] File deleted successfully")
        return True
    else:
        print("[!] Delete failed:", hasil['data'] if hasil else 'No response from server')
        return False


def remote_get(filename=""):
    command_str = f"GET {filename}"
    hasil = send_command(command_str)
    if hasil and hasil.get('status') == 'OK':
        namafile = hasil['data_namafile']
        isifile = base64.b64decode(hasil['data_file'])
        with open(namafile, 'wb') as fp:
            fp.write(isifile)
        print(f"[+] File '{namafile}' berhasil disimpan")
        return True
    else:
        print("[!] Gagal mengambil file:", hasil['data'] if hasil else 'No response from server')
        return False


if __name__ == '__main__':
    logging.basicConfig(level=logging.WARNING)
    server_address = ('172.16.16.101', 6665)
    remote_list()
    remote_get('donalbebek.jpg')
    remote_delete('donalbebek.jpg')