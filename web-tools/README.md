# Scyfix Web Tools

A suite of three Python-based web security tools for reconnaissance, directory discovery, and login brute forcing. All tools were built from scratch and tested against DVWA and Metasploitable 2 in an isolated lab environment.

---

## Tools

### 1. Scyfix Brute Forcer v2.0

A web login brute force tool with dynamic form detection and CSRF token support.

**Features:**
- Auto-detects login form fields, method, and action by scraping the target page
- Identifies username and password fields automatically
- Detects and handles CSRF tokens — fetches a fresh token before every attempt
- Three attack modes: wordlist, pattern, and character brute force
- Mode 4 runs all three in sequence
- Configurable delay between attempts to avoid detection
- Session-based requests with realistic User-Agent header
- Supports multiple usernames in a single run
- Progress counter showing current attempt vs total

**Usage:**
```bash
python3 bruteforcer.py
```

**Tested against:** DVWA (Damn Vulnerable Web Application) on Metasploitable 2

**Known limitations:**
- No CAPTCHA bypass
- No proxy rotation support
- No multi-threading
- No handling for account lockouts
- Does not support JavaScript-rendered login forms

---

### 2. Scyfix Directory Scanner v2.0

A multi-threaded web directory and path discovery tool.

**Features:**
- Multi-threaded scanning — configurable thread count, default 10
- Status code awareness: 200, 301, 302, 403, 500 all handled and colour coded
- Optional file extension scanning — tries each word with extensions like .php, .html, .txt
- URL normalisation — handles http and https, adds protocol if missing
- Progress counter showing current position vs total entries
- Colour coded output: green for 200, yellow for redirects, red for 403 and 500
- Summary of all findings at the end
- Optional save to timestamped text file

**Usage:**
```bash
python3 dirscanner.py
```

**Recommended wordlists (available on Kali Linux):**
- `/usr/share/dirb/wordlists/common.txt` — 4,613 entries, fast general scan
- `/usr/share/dirbuster/wordlists/directory-list-2.3-medium.txt` — 220,000 entries, thorough scan

**Sample output on Metasploitable 2:**
```
[+] [200] FOUND:     http://192.168.1.121/phpinfo.php
[!] [403] FORBIDDEN: http://192.168.1.121/.htaccess
[~] [301] REDIRECT:  http://192.168.1.121/phpMyAdmin --> http://192.168.1.121/phpMyAdmin/
[~] [301] REDIRECT:  http://192.168.1.121/dav --> http://192.168.1.121/dav/
```

**Known limitations:**
- Duplicate results when wordlist already contains extensions
- No recursive scanning into discovered directories
- No proxy support

---

### 3. Scyfix Recon Tool v1.0

A passive web reconnaissance scanner that goes beyond email harvesting to extract a full picture of a target's web presence.

**Features:**
- Crawls up to a configurable number of pages (default 100)
- Email extraction using regex pattern matching
- Response header analysis — detects server technology and backend stack
- Missing security header detection (X-Frame-Options, CSP, HSTS, X-Content-Type-Options)
- Meta tag extraction — reveals CMS, generator, author information
- HTML comment extraction — developers often leave sensitive info in comments
- Form detection — maps all forms with method, action, and field names
- JavaScript file discovery — reveals API endpoints and frontend architecture
- Colour coded output by category
- Optional JSON save with timestamp

**Usage:**
```bash
python3 recontool.py
```

**Sample output:**
```
[RESPONSE HEADERS]
  [+] Web Server: Apache/2.4.41
  [+] Backend Technology: PHP/7.4.3

[MISSING SECURITY HEADERS]
  [-] X-Frame-Options not set -- potential security weakness
  [-] Content-Security-Policy not set -- potential security weakness

[EMAILS FOUND]
  [+] admin@example.com

[HTML COMMENTS]
  [!] TODO: remove debug credentials before deployment
```

**Known limitations:**
- Cannot execute JavaScript — misses dynamically rendered content
- Crawl depth limited to page count, not directory depth
- No proxy support

---

## Installation

```bash
git clone https://github.com/SirArlex/ethical-hacking-labs
cd ethical-hacking-labs/web-tools
pip install requests beautifulsoup4 termcolor lxml
```

---

## Legal Disclaimer

These tools are for educational purposes and authorised penetration testing only. Only use against systems you own or have explicit written permission to test. Unauthorised use is illegal.

---

## Author

**Chinedu Alex Chukwuma**
Cybersecurity Practitioner | Penetration Tester
[GitHub](https://github.com/SirArlex) | [TryHackMe](https://tryhackme.com/p/BigChicks) | [LinkedIn](https://www.linkedin.com/in/chinaedu-chukwuma)
