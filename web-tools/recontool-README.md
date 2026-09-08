# Scyfix Recon Tool v1.0

A passive web reconnaissance scanner that extracts a comprehensive picture of a target's web presence in a single run. Goes beyond simple email harvesting to analyse headers, detect security weaknesses, find hidden information in HTML comments, map forms, and discover JavaScript files.

---

## What It Does

This tool crawls a target website and extracts everything useful for reconnaissance — emails, server technology, missing security headers, developer comments, forms, and JavaScript files. It produces colour coded, categorised output and optionally saves results to a JSON file for further analysis.

---

## Why I Built This

Passive reconnaissance is the first phase of any penetration test. Understanding what information a target inadvertently exposes — through headers, comments, meta tags, and JavaScript — gives an attacker significant intelligence before any active exploitation begins. I built this tool to understand recon methodology at a deep level and to practice extracting actionable findings from raw HTTP responses.

---

## How It Works

1. Starts at the target URL and fetches the page
2. Analyses response headers for technology fingerprinting and security gaps
3. Parses HTML for emails, meta tags, comments, forms, and JavaScript files
4. Discovers links on the page and adds them to the crawl queue
5. Repeats for each discovered page up to the configured limit
6. Prints colour coded findings in real time
7. Displays a summary and optionally saves to JSON

---

## What It Extracts

**Response Headers:**
- Web server and version (Apache, nginx, IIS etc.)
- Backend technology (PHP, ASP.NET etc.)
- CMS or generator information
- Session and cookie technology

**Missing Security Headers (flagged as weaknesses):**
- X-Frame-Options — clickjacking protection
- Content-Security-Policy — XSS mitigation
- Strict-Transport-Security — HTTPS enforcement
- X-Content-Type-Options — MIME sniffing protection

**From HTML:**
- Email addresses (regex pattern matching across all page content)
- Meta tags — author, description, generator, keywords
- HTML comments — developers frequently leave sensitive information here
- Forms — action, method, and all field names
- JavaScript files — can reveal API endpoints, internal URLs, and more

---

## Technologies Used

- Python 3
- `requests` — HTTP requests and crawling
- `beautifulsoup4` — HTML parsing
- `termcolor` — colour coded terminal output
- `re` — regex email extraction
- `json` — structured results saving
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
python3 recontool.py
```

You will be prompted for:

- Target URL
- Maximum pages to crawl (default 100)
- Whether to save results to JSON file

### Example:

```
[*] Enter target URL to scan: https://example.com
[*] Max pages to crawl (default 100): 20
[*] Save results to file? (y/n): y
```

---

## Sample Output

```
╔═══════════════════════════════════════════════════╗
║           SCYFIX RECON TOOL v1.0                  ║
║      Passive Web Reconnaissance Scanner           ║
╚═══════════════════════════════════════════════════╝

[1/20] Scanning: https://example.com

[RESPONSE HEADERS]
  [+] Web Server: Apache/2.4.41 (Ubuntu)
  [+] Backend Technology: PHP/7.4.3

[MISSING SECURITY HEADERS]
  [-] X-Frame-Options not set -- potential security weakness
  [-] Content-Security-Policy not set -- potential security weakness
  [-] X-Content-Type-Options not set -- potential security weakness

[EMAILS FOUND]
  [+] admin@example.com
  [+] support@example.com

[HTML COMMENTS]
  [!] TODO: remove test credentials before deployment
  [!] Database: mysql://internal-db.company.local

[FORMS DETECTED]
  [+] Action: /login | Method: POST | Fields: username, password, csrf_token

[JAVASCRIPT FILES]
  [+] https://example.com/assets/app.js
  [+] https://example.com/assets/api-client.js

[*] SCAN COMPLETE -- SUMMARY
  Pages scanned:            20
  Emails found:             2
  Missing security headers: 3
  HTML comments found:      2
  Forms detected:           1
  JS files found:           2

[*] Results saved to recon_example_com_20260908_143022.json
```

---

## Real Finding Example

Running this tool against a test environment revealed:
- 3 missing security headers (X-Frame-Options, CSP, X-Content-Type-Options)
- Server technology fingerprint via response headers
- Compiled JavaScript bundle exposing frontend architecture

These findings were documented as a real security assessment report.

---

## Known Limitations

- Cannot execute JavaScript — misses content rendered dynamically by React, Angular, or Vue
- Crawl depth is page count based, not directory depth based
- No proxy support
- May trigger rate limiting on production sites with many pages

---

## Skills Demonstrated

- Passive web reconnaissance methodology
- HTTP response header analysis and security assessment
- HTML parsing and information extraction
- Web crawling and link discovery
- Regex pattern matching for data extraction
- JSON structured output for findings documentation
- Real-world security assessment reporting

---

## Legal Disclaimer

This tool is intended for educational purposes and authorised penetration testing only. Only use against systems you own or have explicit written permission to test. Unauthorised scanning is illegal.

---

## Author

**Chinedu Alex Chukwuma**
Cybersecurity Practitioner | Penetration Tester
[GitHub](https://github.com/SirArlex) | [TryHackMe](https://tryhackme.com/p/BigChicks) | [LinkedIn](https://www.linkedin.com/in/chinaedu-chukwuma)
