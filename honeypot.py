import threading
import socket
import sys
import traceback
import logging
import json
import paramiko
from datetime import datetime
import time
from concurrent.futures import ThreadPoolExecutor
from collections import defaultdict
import time

# Implementing Rate limiting
MAX_THREADS = 20                   # Maximum number of active connections
MAX_ATTEMPTS_PER_IP = 5            # Maximum number of connections per IP within a window
TIME_WINDOW = 60                   # Reset window in seconds (1 minute)

ip_tracker = defaultdict(list)

def is_rate_limited(ip):
    now = time.time()
    # Remove timestamps older than the time window
    ip_tracker[ip] = [t for t in ip_tracker[ip] if now - t < TIME_WINDOW]
    
    if len(ip_tracker[ip]) >= MAX_ATTEMPTS_PER_IP:
        return True
        
    ip_tracker[ip].append(now)
    return False


HOST_KEY = paramiko.RSAKey.generate(2048)
class HoneypotServer(paramiko.ServerInterface):
    def __init__(self, client_ip):
        self.client_ip = client_ip
        self.event = threading.Event()

    def check_channel_request(self, kind, chanid):
        # Allows the client to open a session channel
        if kind == 'session':
            return paramiko.OPEN_SUCCEEDED
        return paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED

    def check_auth_password(self, username, password):
        # Logs the credentials and always lets in the attacker
        print(f"[!] Alert: Login attempt from {self.client_ip}")
        print(f"    Username: {username}")
        print(f"    Password: {password}")
        return paramiko.AUTH_SUCCESSFUL

    def get_allowed_auths(self, username):
        # Tell the client you only accept password authentication
        return "password"

    def check_channel_pty_request(self, channel, term, width, height, pixelwidth, pixelheight, modes):
        # Accept requests for a pseudo-terminal so they get a prompt
        return True

    def check_channel_shell_request(self, channel):
        # Accept requests to open a shell
        self.event.set()
        return True

def handle_connection(client_socket, client_addr):
    client_ip = client_addr[0]
    print(f"[*] Connection received from {client_ip}")

    try:
        # Wrap the raw socket in a Paramiko Transport
        transport = paramiko.Transport(client_socket)
        transport.add_server_key(HOST_KEY)
        
        server = HoneypotServer(client_ip)
        
        # Starts the SSH server negotiation
        try:
            transport.start_server(server=server)
        except paramiko.SSHException as e:
            print(f"[-] SSH negotiation failed: {e}")
            return

        # Waits for the client to authenticate and open a channel
        channel = transport.accept(20)
        if channel is None:
            print("[-] Client did not open a channel.")
            return
            
        print(f"[+] Client {client_ip} authenticated successfully.")
        
        # Waits for the client to request a shell
        server.event.wait(10)
        if not server.event.is_set():
            print("[-] Client did not request a shell.")
            channel.close()
            return

        # The Fake Shell Loop
        channel.send("\r\nWelcome to Ubuntu 22.04.2 LTS (GNU/Linux 5.15.0-76-generic x86_64)\r\n\r\n")
        
        while True:
            # Sends a fake root prompt at the beginning of each line
            channel.send("root@server:~# ")
            
            # Receive the command the attacker types up to 1024
            command = b""
            while True:
                char = channel.recv(1)
                if not char:
                    break
                # Echoes the character back to the client so they can see what they type
                channel.send(char)
                command += char
                # Break on Enter key
                if char == b'\r':
                    channel.send(b'\n')
                    break
            
            cmd_str = command.decode('utf-8').strip()
            if not cmd_str:
                continue
                
            print(f"[{client_ip}] Executed: {cmd_str}")
            
            if cmd_str.lower() in ['exit', 'quit']:
                channel.send("logout\r\n")
                break
            else:
                # Give a generic fake error for everything else (Can implement some commands like echo later)
                channel.send(f"-bash: {cmd_str.split()[0]}: command not found\r\n")

    except Exception as e:
        print(f"[-] Error handling client {client_ip}: {e}")
    finally:
        client_socket.close()
        print(f"[*] Connection with {client_ip} closed.")

def start_honeypot(host='0.0.0.0', port=2222):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((host, port))
    server_socket.listen(100)
    
    print(f"[*] Honeypot listening on {host}:{port} (Press Ctrl+C to stop)")

    #creates a bounded pool of threads instead of spawning a new one for every connection
    executor = ThreadPoolExecutor(max_workers=MAX_THREADS)
    
    try:
        while True:
            client_socket, client_addr = server_socket.accept()
            client_ip = client_addr[0]
            # Check IP Rate Limiting
            if is_rate_limited(client_ip):
                print(f"[!] Rate limit triggered for {client_ip}. Dropping connection.")
                client_socket.close()
                continue
            
            # add the connection to the bounded thread pool
            executor.submit(handle_connection, client_socket, client_addr)
    except KeyboardInterrupt:
        print("\n[*] Shutting down honeypot.")
        server_socket.close()
        sys.exit(0)

if __name__ == "__main__":
    start_honeypot()
