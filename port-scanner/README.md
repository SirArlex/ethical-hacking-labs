# Scyfix Port Scanner v2.0

A Python-based network port scanner built for reconnaissance and network enumeration during penetration testing engagements.

---

## What It Does

This tool scans a target IP address or range of IPs for open TCP ports. For each open port it discovers, it:

- Reports the port number
- Identifies the service running on that port (SSH, HTTP, FTP etc.)
- Attempts to grab the service banner to reveal software version information
- Timestamps the scan start and end for documentation purposes
- Supports scanning multiple targets in a single run

---

## Why I Built This

Understanding what ports are open on a target is one of the first steps in any penetration test. This tool was built as part of my ethical hacking practice to understand how network reconnaissance works at the socket level, rather than just running existing tools without knowing what happens underneath.

---

## How It Works

The scanner uses Python's built-in `socket` library to attempt TCP connections on each port in the specified range. If a connection succeeds, the port is open. It then:

1. Looks up the service name using `socket.getservbyport()`
2. Attempts to receive a banner response from the service using `socket.recv(1024)`
3. Decodes and cleans the banner to extract the first line of the response
4. Prints the result in a formatted, colour-coded output

---

## Technologies Used

- Python 3
- `socket` — for TCP connection attempts and banner grabbing
- `termcolor` — for colour-coded terminal output
- `datetime` — for scan timestamps

---

## Installation

Clone the repository:

```bash
git clone https://github.com/SirArlex/ethical-hacking-labs
cd ethical-hacking-labs
```

Install the required dependency:

```bash
pip install termcolor
```

---

## Usage

```bash
python3 portscanner.py
```

You will be prompted to enter:

- Target IP address (or multiple IPs separated by commas)
- Number of ports to scan (e.g. 1000 scans ports 1 to 1000)

### Single target example:

```
[*] Enter target(s) to scan: 192.168.1.10
[*] Enter number of ports to scan: 1000
```

### Multiple targets example:

```
[*] Enter target(s) to scan: 192.168.1.10, 192.168.1.11
[*] Enter number of ports to scan: 500
```

---

## Sample Output

```
============================================================
         SCYFIX PORT SCANNER v2.0
============================================================

[*] Starting scan for 192.168.1.10
[*] Scanning ports 1 - 1000
[*] Scan started at 14:23:01

[+] Port 22     OPEN | Service: ssh          | Banner: SSH-2.0-OpenSSH_8.9
[+] Port 80     OPEN | Service: http         | Banner: no banner
[+] Port 21     OPEN | Service: ftp          | Banner: 220 FTP server ready

[*] Scan completed at 14:24:47
```

---

## Skills Demonstrated

- TCP socket programming in Python
- Network port enumeration techniques
- Service banner grabbing for version detection
- Multi-target scanning logic
- Penetration testing reconnaissance methodology

---

## Legal Disclaimer

This tool is intended for educational purposes and authorised penetration testing only. Only use this scanner on systems you own or have explicit written permission to test. Unauthorised scanning of networks is illegal.

---

## Author

**Chinedu Alex Chukwuma**
Cybersecurity Practitioner | Penetration Tester
[GitHub](https://github.com/SirArlex) | [TryHackMe](https://tryhackme.com/p/BigChicks) | [LinkedIn](https://www.linkedin.com/in/chinaedu-chukwuma)
