import argparse
import threading
import socket
import sys
import os
import traceback
import logging
import json
import logging
import paramiko
from datetime import datetime
from binascii import hexlify
from paramiko.py3compat import b, u, decodebytes


class SshHoneypot(paramiko.ServerInterface):

    client_ip = None
    def __init__(self, client_ip):
        self.client_ip = client_ip
        self.event = threading.Event()
    def check_channel_request(self, kind, chanid):
        pass
    def get_allowed_auths(self, username):
        pass
    def check_auth_publickey(self, username, key):
        pass
    def check_auth_password(self, username, password):
        pass
    def check_channel_shell_request(self, channel):
        pass
    def check_channel_pty_request(self, channel, term, width, height, pixelwidth, pixelheight, modes):
        pass
    def check_channel_exec_request(self, channel, command):
        pass