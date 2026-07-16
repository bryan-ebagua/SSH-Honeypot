#  Python SSH Honeypot

A custom, lightweight SSH server built in Python designed to emulate a vulnerable Linux machine. This honeypot intercepts unauthorized login attempts, captures credentials, and provides attackers with a fake interactive shell to log their keystrokes and malicious commands.

**Note:** This is an active work-in-progress. Current functionality covers the core SSH emulation engine. Future phases include Docker containerization, Azure deployment, and SIEM integration.

## 🚀 Features

* **Custom SSH Server:** Built from the ground up using the `paramiko` library to intercept raw TCP connections and negotiate SSH handshakes.
* **Universal Authentication:** Bypasses standard authentication protocols to accept *any* username and password combination, logging the credentials for threat analysis.
* **Interactive Fake Shell:** Emulates a standard Ubuntu bash environment. Attackers are provided a pseudo-terminal (PTY) that echoes their inputs and simulates generic shell errors to keep them engaged.
* **Concurrent Connection Handling:** Utilizes Python's `threading` module to manage multiple concurrent attacks simultaneously.

## ⚠️ Security Disclaimer

**DO NOT run this script on a production machine, bare metal, or bind it to a privileged port (like 22) without strict isolation.** This software is intentionally designed to accept unauthorized connections. It should only be run inside a sandboxed environment (like an isolated VM or a strictly bound Docker container) to prevent lateral movement on your local network.

## 🛠️ Tech Stack

* **Language:** Python 3.11+
* **Core Libraries:** `paramiko`, `socket`, `threading`, `cryptography`

## ⚙️ Quick Start

### Prerequisites
Ensure you have Python installed, then install the required cryptographic and SSH libraries:

```bash
pip install paramiko cryptography
```
### Running the Honeypot
Start the server. By default, it binds to 0.0.0.0 on port 2222 to avoid conflicting with actual SSH daemons.

```Bash
python honeypot.py
```

Open a separate terminal window and attempt to connect to the honeypot. You can use any username or password.

```Bash
ssh -p 2222 root@localhost
```
Once inside the fake shell, try typing standard Linux commands (e.g., whoami, ls -la) and watch the honeypot log your inputs in the server terminal.
