import time
import traceback
from test import *
from test_functions import *
import socket
import json
import sys
import socket

# Raspberry Pi in here is the server, it will listen triggering message from client

HOST = "192.168.1.1"  # replace this to your Raspberry Pi local IP
PORT = 2660  # Port to listen on (non-privileged ports are > 1023)

try:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()
        
        count = 0
        while True:
            conn, addr = s.accept()
            print(f"Connected by {addr}")
            try:
                data = conn.recv(1024)

                if not data:
                    print("No data received. Closing connection.")
                    conn.close()
                    break

                print(f"Received message from {addr}, Message: {data.decode('utf-8')}")
                testing(conn)

            except socket.timeout:
                print("Socket timed out waiting for data, you might want to handle this specifically.")
                continue  

            except socket.error as e:
                #print(f"Socket error occurred: {e}")
                break

            except OSError as e:
                if e.errno == errno.EBADF:
                    print("Bad file descriptor. This likely means the socket is no longer open.")
                else:
                    print(f"An OS error occurred: {e}")
                break

            except Exception as e:
                print(f"An unexpected error occurred: {e}")
                break
        conn.close()

except Exception as e:
    print(f"An error occurred setting up the server: {e}")

