# Scyfix Directory Scanner v2.0

A multi-threaded web directory and path discovery tool built for penetration testing reconnaissance. Identifies hidden directories, files, and paths on web servers using wordlist-based scanning with full HTTP status code awareness.

---

## What It Does

This tool takes a target URL and a wordlist of directory and file names, then attempts to access each path on the target server. Unlike basic scanners that treat any response as a hit, this tool correctly interprets HTTP status codes to give you meaningful, actionable results.

---

## Why I Built This

Directory discovery is a core part of web application penetration testing. Understanding what paths exist on a server — even ones that return 403 — gives an attacker valuable information about the target's structure. I built this tool to understand the mechanics of directory brute forcing at the HTTP level rather than just running existing tools like dirb or gobuster without knowing what happens underneath.

---

## How It Works

1. Reads a wordlist file line by line
2. Optionally appends file extensions to each word
3. Dispatches requests across multiple threads simultaneously
4. Evaluates each HTTP response code and categorises the result
5. Prints colour coded output in real time
6. Displays a full summary on completion

**Status code handling:**
- `200` — Path exists and is accessible (green)
- `301/302` — Path exists and redirects elsewhere (yellow)
- `403` — Path exists but access is forbidden (red)
- `500` — Path exists and causes a server error (red)
- `404` — Path does not exist (ignored)

---

## Technologies Used

- Python 3
- `requests` — HTTP requests
- `termcolor` — colour coded terminal output
- `threading` — multi-threaded scanning
- `queue` — thread-safe work distribution
- `datetime` — scan timestamps

---

## Installation

```bash
git clone https://github.com/SirArlex/ethical-hacking-labs
cd ethical-hacking-labs/web-tools
pip install requests termcolor
```

---

## Usage

```bash
python3 dirscanner.py
```

You will be prompted for:

- Target URL (http or https, with or without trailing slash)
- Path to wordlist file
- Number of threads (default 10)
- File extensions to append e.g. `php,html,txt` (optional)
- Whether to save results to file

### Example:

```
[*] Enter target URL: http://192.168.1.121
[*] Enter path to wordlist file: /usr/share/dirb/wordlists/common.txt
[*] Number of threads (default 10): 10
[*] File extensions to check: php,html
[*] Save results to file? (y/n): y
```

---

## Recommended Wordlists

Available on Kali Linux at:

- `/usr/share/dirb/wordlists/common.txt` — 4,613 entries, fast general scan
- `/usr/share/dirb/wordlists/big.txt` — 20,469 entries, more thorough
- `/usr/share/dirbuster/wordlists/directory-list-2.3-medium.txt` — 220,000 entries, comprehensive

---

## Sample Output

```
╔═══════════════════════════════════════════════════╗
║         SCYFIX DIRECTORY SCANNER v2.0             ║
║      Web Directory & Path Discovery Tool          ║
╚═══════════════════════════════════════════════════╝

[*] Target:    http://192.168.1.121
[*] Wordlist:  4613 entries
[*] Threads:   10
[*] Scan started at 10:55:55

  [!] [403] FORBIDDEN: http://192.168.1.121/.htaccess
  [+] [200] FOUND:     http://192.168.1.121/index.php
  [+] [200] FOUND:     http://192.168.1.121/phpinfo.php
  [~] [301] REDIRECT:  http://192.168.1.121/phpMyAdmin --> http://192.168.1.121/phpMyAdmin/
  [~] [301] REDIRECT:  http://192.168.1.121/dav --> http://192.168.1.121/dav/

[*] Scan completed at 10:58:21
[*] Total found: 22
```

---

## Skills Demonstrated

- Multi-threaded network programming in Python
- HTTP status code interpretation
- Web directory enumeration methodology
- Thread-safe output with locks
- Queue-based work distribution across threads
- Penetration testing reconnaissance techniques

---

## Legal Disclaimer

This tool is intended for educational purposes and authorised penetration testing only. Only use this scanner on systems you own or have explicit written permission to test. Unauthorised scanning of systems is illegal.

---

## Author

**Chinedu Alex Chukwuma**
Cybersecurity Practitioner | Penetration Tester
[GitHub](https://github.com/SirArlex) | [TryHackMe](https://tryhackme.com/p/BigChicks) | [LinkedIn](https://www.linkedin.com/in/chinaedu-chukwuma)
