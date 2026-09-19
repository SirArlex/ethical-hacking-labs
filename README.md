# Scyfix Security Testing Toolkit

A collection of Python-based penetration testing tools, installable as global commands. Built for educational purposes and authorised security assessments, and tested against DVWA and Metasploitable 2.

---

## Tools

| Command | Tool | Description |
|---------|------|-------------|
| `scyfix-port` | Port Scanner | TCP port scanner with service detection and banner grabbing |
| `scyfix-brute` | Brute Forcer | Multi-protocol authentication tester — Web, SSH, FTP |
| `scyfix-scan` | Directory Scanner | Multi-threaded directory discovery with SPA false-positive detection |
| `scyfix-recon` | Recon Tool | Passive web reconnaissance — emails, headers, forms, JS files |

---

## Installation

Clone the repository and install as an editable package:

```bash
git clone https://github.com/SirArlex/ethical-hacking-labs.git
cd ethical-hacking-labs
pip install -e . --break-system-packages
```

Once installed, the four commands are available system-wide. Because it is installed in editable mode, any updates pulled from GitHub take effect immediately without reinstalling:

```bash
git pull
```

---

## Usage

After installation, run any tool from anywhere in your terminal:

```bash
scyfix-port      # Port scanner
scyfix-brute     # Brute forcer (Web / SSH / FTP)
scyfix-scan      # Directory scanner
scyfix-recon     # Recon tool
```

Each tool is interactive and will prompt for the required inputs.

---

## Brute Forcer Modes (v3.0)

The brute forcer now supports multiple protocols:

- **Mode 1-4** — Web login forms (wordlist, pattern, character brute force, or all)
- **Mode 5** — SSH brute force
- **Mode 6** — FTP brute force
- **Mode 7** — Auto-detect protocol (SSH or FTP) and attack

Web mode includes dynamic form detection, CSRF token handling, and multiple attack strategies.

---

## Dependencies

Installed automatically with the package:

- requests
- beautifulsoup4
- termcolor
- lxml
- paramiko (for SSH support)

---

## Legal Disclaimer

These tools are intended for educational purposes and authorised penetration testing only. Only use them on systems you own or have explicit written permission to test. Unauthorised use is illegal.

---

## Author

**Chinedu Alex Chukwuma**
Cybersecurity Practitioner | Penetration Tester
[GitHub](https://github.com/SirArlex) | [TryHackMe](https://tryhackme.com/p/BigChicks) | [LinkedIn](https://www.linkedin.com/in/chinaedu-chukwuma)
