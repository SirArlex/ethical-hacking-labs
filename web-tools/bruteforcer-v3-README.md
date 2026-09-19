# Scyfix Brute Forcer v3.0

A multi-protocol authentication testing tool supporting web login forms, SSH, and FTP. Built from scratch with dynamic form detection, CSRF token handling, and intelligent attack modes. Tested against DVWA, Metasploitable 2, and real-world web applications.

---

## What It Does

This tool automates credential testing across multiple protocols. For web targets it intelligently analyses the login form before attacking — detecting field names, HTTP method, form action, and CSRF tokens automatically. For SSH and FTP targets it handles protocol-level authentication directly. An auto-detect mode identifies the protocol from the target's banner and launches the appropriate attack.

---

## Why I Built This

Understanding how brute force attacks work at a protocol level is fundamental to understanding how to defend against them. I built this tool progressively — starting with basic web form attacks, adding CSRF token support when basic approaches failed against protected forms, then extending to SSH and FTP to cover network service authentication. Each version was built to solve a specific problem encountered during real penetration testing practice.

---

## Attack Modes

**Web Modes (1-4):**

| Mode | Description |
|------|-------------|
| 1 | Wordlist attack — tries every password in a file |
| 2 | Pattern attack — username variations + common passwords, no wordlist needed |
| 3 | Character brute force — generates all combinations up to a specified length |
| 4 | All web modes in sequence — wordlist first, then pattern, then brute force |

**Network Modes (5-7):**

| Mode | Description |
|------|-------------|
| 5 | SSH brute force — tests credentials against SSH service |
| 6 | FTP brute force — tests credentials against FTP service |
| 7 | Auto-detect — reads service banner, identifies SSH or FTP, launches appropriate attack |

---

## Key Features

**Web attack features:**
- Auto-detects login form fields, method, and action by scraping the target page
- Identifies username and password fields automatically from common field names
- Falls back to manual field entry if auto-detection fails
- Detects CSRF tokens and fetches a fresh one before every attempt
- Handles session cookies properly for targets like DVWA
- Three attack strategies covering most real-world scenarios
- Configurable delay between attempts to avoid rate limiting and detection
- Progress counter showing current attempt vs total
- Supports multiple usernames in a single run

**Network attack features:**
- SSH support via paramiko — handles host key policies automatically
- FTP support via Python's built-in ftplib
- Protocol auto-detection by reading service banner on connection
- Configurable port for non-standard service deployments
- Graceful error handling for connection timeouts and refused connections

---

## Technologies Used

- Python 3
- `requests` — HTTP session management and form submission
- `beautifulsoup4` — HTML form parsing and CSRF token extraction
- `paramiko` — SSH authentication
- `ftplib` — FTP authentication (Python standard library)
- `termcolor` — colour coded terminal output
- `socket` — protocol banner detection
- `datetime` — attack timestamps

---

## Installation

Install the full Scyfix toolkit (includes all tools as global commands):

```bash
git clone https://github.com/SirArlex/ethical-hacking-labs.git
cd ethical-hacking-labs
pip install paramiko --break-system-packages
pip install -e . --break-system-packages
```

Or install dependencies manually for standalone use:

```bash
pip install requests beautifulsoup4 termcolor lxml paramiko --break-system-packages
```

---

## Usage

**As a global command (after package install):**
```bash
scyfix-brute
```

**Standalone:**
```bash
python3 bruteforcer.py
```

---

## Example Sessions

**Web attack against DVWA:**
```
[*] Select attack mode: 2
[*] Enter target login URL: http://192.168.1.121/dvwa/login.php
[*] Enter username(s): admin
[*] Enter string that appears when login FAILS: Login failed
[*] Delay between attempts: 0.5

[*] Detecting login form...
  [+] Form method: POST
  [+] Form action: http://192.168.1.121/dvwa/login.php
  [+] Input fields: ['username', 'password']
  [+] No CSRF token detected
  [+] Username field: username
  [+] Password field: password

[*] Pattern attack on username: admin
  [*] Trying (8/30): password

  [+] SUCCESS!
  [+] Username: admin
  [+] Password: password
```

**SSH attack against Metasploitable:**
```
[*] Select attack mode: 5
[*] Enter target host/IP: 192.168.1.121
[*] Enter port (default 22): 22
[*] Enter username(s): msfadmin
[*] Delay between attempts: 0.5
[*] Enter path to password file: /usr/share/wordlists/rockyou.txt

[*] Starting SSH attack on 192.168.1.121:22
[*] Loaded 14344392 passwords

[*] Attacking SSH user: msfadmin
  [*] Trying (847/14344392): msfadmin

  [+] SUCCESS!
  [+] Username: msfadmin
  [+] Password: msfadmin
```

**Auto-detect mode:**
```
[*] Select attack mode: 7
[*] Enter target host/IP: 192.168.1.121
[*] Enter target port: 21
  [+] Detected protocol: ftp

[*] Starting FTP attack on 192.168.1.121:21
```

---

## How CSRF Token Support Works

Many login forms include a hidden CSRF token that changes with every page load. A basic brute forcer sends the same token repeatedly — the server rejects all attempts because the token is stale.

This tool solves it by fetching a fresh copy of the login page before every single attempt, extracting the current token value using BeautifulSoup, and including it in the POST request. This makes the attack indistinguishable from a real user logging in normally.

**Important Burp Suite note:** When fuzzing file extensions or login forms in Burp Intruder, always disable URL encoding in the Payload Encoding section. By default Burp encodes dots as `%2E` — turning `.phtml` into `%2Ephtml` — which breaks extension-based attacks.

---

## Known Limitations

- No CAPTCHA bypass
- No proxy rotation support
- Web modes are single-threaded — one attempt at a time
- No account lockout detection or auto-pause
- Does not support JavaScript-rendered login forms (React, Angular, Vue)
- SSH mode requires paramiko — install separately if missing

---

## Version History

| Version | Changes |
|---------|---------|
| v1.0 | Basic web form brute forcer with hardcoded field names |
| v2.0 | Dynamic form detection, CSRF support, multiple attack modes, pattern attack |
| v3.0 | SSH brute force, FTP brute force, protocol auto-detection, installable as global command |

---

## Skills Demonstrated

- HTTP session management and cookie handling
- Dynamic HTML form parsing with BeautifulSoup
- CSRF token detection and automated per-attempt refresh
- SSH protocol authentication with paramiko
- FTP protocol authentication with ftplib
- Network service banner detection and protocol identification
- Multi-mode attack architecture in Python
- Penetration testing web and network authentication methodology

---

## Legal Disclaimer

This tool is intended for educational purposes and authorised penetration testing only. Only use against systems you own or have explicit written permission to test. Unauthorised use is illegal.

---

## Author

**Chinedu Alex Chukwuma**
Cybersecurity Practitioner | Penetration Tester
[GitHub](https://github.com/SirArlex) | [TryHackMe](https://tryhackme.com/p/BigChicks) | [LinkedIn](https://www.linkedin.com/in/chinaedu-chukwuma)
