# Scyfix Brute Forcer v2.0

A web login brute force tool with dynamic form detection, CSRF token support, and multiple attack modes. Built for authorised penetration testing of web application login forms.

---

## What It Does

This tool automates credential testing against web login forms. Unlike basic brute forcers that hardcode field names and HTTP methods, this tool intelligently analyses the target login page first — detecting form fields, HTTP method, action URL, and CSRF tokens automatically — then launches the selected attack mode.

---

## Why I Built This

Understanding how brute force attacks work is fundamental to understanding how to defend against them. I built this tool to learn the mechanics of web authentication testing at the HTTP level, including how CSRF token protection works and how to handle it properly during automated testing.

---

## How It Works

1. Fetches the target login page and parses the HTML form
2. Auto-detects username field, password field, HTTP method, and form action
3. Detects CSRF tokens and fetches a fresh one before every attempt
4. Launches selected attack mode
5. Sends each credential pair as a properly formed HTTP request
6. Checks the response for the fail string to determine success or failure

---

## Attack Modes

**Mode 1 — Wordlist Attack:**
Tries every password in a provided wordlist file. Works best with `rockyou.txt` (`/usr/share/wordlists/rockyou.txt` on Kali).

**Mode 2 — Pattern Attack:**
Tries common passwords and variations of the target username without needing a wordlist file. Includes patterns like `username123`, `Username!`, `password`, `admin`, `qwerty123` and more.

**Mode 3 — Character Brute Force:**
Generates and tries every possible combination of characters up to a specified length. Use with caution — exponentially slower as length and charset increase.

**Mode 4 — All Modes:**
Runs wordlist first, then pattern, then character brute force in sequence, stopping as soon as credentials are found.

---

## Technologies Used

- Python 3
- `requests` — HTTP session management and form submission
- `beautifulsoup4` — HTML form parsing and CSRF token extraction
- `termcolor` — colour coded terminal output
- `datetime` — scan timestamps

---

## Installation

```bash
git clone https://github.com/SirArlex/ethical-hacking-labs
cd ethical-hacking-labs/web-tools
pip install requests beautifulsoup4 termcolor lxml
```

---

## Usage

```bash
python3 bruteforcer.py
```

You will be prompted for:

- Target login page URL
- Username(s) to attack (comma separated for multiple)
- String that appears when login fails
- Delay between attempts in seconds
- Attack mode

### Example against DVWA:

```
[*] Enter target login URL: http://192.168.1.121/dvwa/login.php
[*] Enter username(s) to attack: admin
[*] Enter string that appears when login FAILS: Login failed
[*] Delay between attempts: 0.5
[*] Enter mode: 2
```

---

## Sample Output

```
╔═══════════════════════════════════════════════════╗
║         SCYFIX BRUTE FORCER v2.0                  ║
║      Web Login Brute Force & Wordlist Attack      ║
║         Now with CSRF Token Support               ║
╚═══════════════════════════════════════════════════╝

[*] Detecting login form...
  [+] Form method: POST
  [+] Form action: http://192.168.1.121/dvwa/login.php
  [+] Input fields: ['username', 'password']
  [+] No CSRF token detected
  [+] Username field: username
  [+] Password field: password

[*] Starting pattern attack...
[*] Pattern attack on username: admin
  [*] Trying (8/30): password

  [+] SUCCESS!
  [+] Username: admin
  [+] Password: password
```

---

## Known Limitations

- No CAPTCHA bypass
- No proxy rotation support
- Single-threaded — one attempt at a time
- No account lockout detection
- Does not support JavaScript-rendered login forms
- Fail string must be manually identified from the target page

---

## Skills Demonstrated

- HTTP session management and cookie handling
- Dynamic HTML form parsing with BeautifulSoup
- CSRF token detection and automated refresh
- Web authentication attack methodology
- Python requests library proficiency
- Penetration testing web application techniques

---

## Legal Disclaimer

This tool is intended for educational purposes and authorised penetration testing only. Only use against systems you own or have explicit written permission to test. Unauthorised use is illegal.

---

## Author

**Chinedu Alex Chukwuma**
Cybersecurity Practitioner | Penetration Tester
[GitHub](https://github.com/SirArlex) | [TryHackMe](https://tryhackme.com/p/BigChicks) | [LinkedIn](https://www.linkedin.com/in/chinaedu-chukwuma)
