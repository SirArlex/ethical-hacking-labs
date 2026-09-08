# Scyfix Ethical Hacking Labs

A collection of Python-based penetration testing and reconnaissance tools built for educational purposes and authorised security assessments. These tools were developed as part of hands-on ethical hacking practice — each one tested against real vulnerable environments including DVWA and Metasploitable 2.

---

## Tools Included

### Port Scanner
A fast, multi-feature TCP port scanner with service detection and banner grabbing. Supports single and multiple targets simultaneously.

### Web Tools
A suite of three web-focused security tools:

**Brute Forcer** — Web login brute force tool with dynamic form detection, CSRF token support, wordlist attack, pattern attack, and character brute force modes.

**Directory Scanner** — Multi-threaded web directory and path discovery tool with status code awareness, extension scanning, and colour coded output.

**Recon Tool** — Passive web reconnaissance scanner that extracts emails, analyses response headers, detects missing security headers, finds HTML comments, maps forms, and discovers JavaScript files.

---

## Lab Environment

All tools were developed and tested in an isolated VirtualBox lab environment:

- **Attack Machine:** Kali Linux
- **Target Machine:** Metasploitable 2
- **Network:** Host-Only Adapter (isolated, no internet exposure)
- **Additional Target:** DVWA (Damn Vulnerable Web Application)

---

## Requirements

Install all dependencies with:

```bash
pip install requests beautifulsoup4 termcolor lxml
```

---

## Legal Disclaimer

These tools are intended for educational purposes and authorised penetration testing only. Only use these tools on systems you own or have explicit written permission to test. Unauthorised scanning or attacking of systems is illegal and unethical. The author takes no responsibility for misuse of these tools.

---

## Skills Demonstrated

- TCP socket programming and network reconnaissance
- HTTP request handling and session management
- Dynamic HTML form parsing and CSRF token handling
- Multi-threaded network scanning
- Web application security testing methodology
- Python security tooling and scripting
- Penetration testing lab setup and operation

---

## Author

**Chinedu Alex Chukwuma**
Cybersecurity Practitioner | Penetration Tester
[GitHub](https://github.com/SirArlex) | [TryHackMe](https://tryhackme.com/p/BigChicks) | [LinkedIn](https://www.linkedin.com/in/chinaedu-chukwuma)
