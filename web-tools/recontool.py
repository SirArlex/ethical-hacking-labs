import requests
import requests.exceptions
import urllib.parse
from collections import deque
from bs4 import BeautifulSoup, Comment
import re
import json
import os
from datetime import datetime
from termcolor import colored

# ─── BANNER ───────────────────────────────────────────────────
def print_banner():
    print(colored("""
╔═══════════════════════════════════════════════════╗
║           SCYFIX RECON TOOL v1.0                  ║
║      Passive Web Reconnaissance Scanner           ║
╚═══════════════════════════════════════════════════╝
""", 'cyan'))

# ─── HEADER ANALYSIS ──────────────────────────────────────────
def analyse_headers(headers, results):
    print(colored("\n[RESPONSE HEADERS]", 'yellow'))

    interesting = {
        'Server': 'Web Server',
        'X-Powered-By': 'Backend Technology',
        'X-Generator': 'CMS/Generator',
        'X-Frame-Options': 'Clickjacking Protection',
        'Content-Security-Policy': 'CSP Header',
        'Strict-Transport-Security': 'HSTS',
        'X-Content-Type-Options': 'MIME Sniffing Protection',
        'Set-Cookie': 'Cookie/Session Info',
    }

    security_missing = []

    for header, label in interesting.items():
        if header in headers:
            value = headers[header]
            print(colored(f"  [+] {label}: {value}", 'green'))
            results['headers'][label] = value
        else:
            if header in ['X-Frame-Options', 'Content-Security-Policy', 
                         'Strict-Transport-Security', 'X-Content-Type-Options']:
                security_missing.append(header)

    if security_missing:
        print(colored("\n[MISSING SECURITY HEADERS]", 'red'))
        for h in security_missing:
            print(colored(f"  [-] {h} not set -- potential security weakness", 'red'))
            results['missing_security_headers'].append(h)

# ─── EMAIL EXTRACTION ─────────────────────────────────────────
def extract_emails(text, results):
    found = set(re.findall(
        r"[a-z0-9\.\-+_]+@[a-z0-9\.\-+_]+\.[a-z]+", text, re.I
    ))
    new_emails = found - results['emails']
    if new_emails:
        print(colored("\n[EMAILS FOUND]", 'green'))
        for email in new_emails:
            print(colored(f"  [+] {email}", 'green'))
        results['emails'].update(new_emails)

# ─── META TAG EXTRACTION ──────────────────────────────────────
def extract_meta(soup, results):
    meta_tags = soup.find_all('meta')
    found = []
    for tag in meta_tags:
        name = tag.get('name', tag.get('property', ''))
        content = tag.get('content', '')
        if name and content:
            found.append(f"{name}: {content}")

    if found:
        print(colored("\n[META TAGS]", 'yellow'))
        for m in found:
            print(colored(f"  [+] {m}", 'yellow'))
            results['meta_tags'].append(m)

# ─── HTML COMMENT EXTRACTION ──────────────────────────────────
def extract_comments(soup, results):
    comments = soup.find_all(string=lambda text: isinstance(text, Comment))
    clean = [c.strip() for c in comments if c.strip()]
    if clean:
        print(colored("\n[HTML COMMENTS]", 'red'))
        for c in clean:
            print(colored(f"  [!] {c}", 'red'))
            results['html_comments'].append(c)

# ─── FORM EXTRACTION ──────────────────────────────────────────
def extract_forms(soup, url, results):
    forms = soup.find_all('form')
    if forms:
        print(colored("\n[FORMS DETECTED]", 'yellow'))
        for form in forms:
            action = form.get('action', 'no action')
            method = form.get('method', 'GET').upper()
            inputs = [i.get('name', 'unnamed') for i in form.find_all('input')]
            form_info = f"Action: {action} | Method: {method} | Fields: {', '.join(inputs)}"
            print(colored(f"  [+] {form_info}", 'yellow'))
            results['forms'].append({'url': url, 'action': action, 
                                    'method': method, 'fields': inputs})

# ─── JS FILE EXTRACTION ───────────────────────────────────────
def extract_js(soup, base_url, results):
    scripts = soup.find_all('script', src=True)
    if scripts:
        print(colored("\n[JAVASCRIPT FILES]", 'cyan'))
        for script in scripts:
            src = script['src']
            if not src.startswith('http'):
                src = base_url + '/' + src.lstrip('/')
            if src not in results['js_files']:
                print(colored(f"  [+] {src}", 'cyan'))
                results['js_files'].append(src)

# ─── LINK DISCOVERY ───────────────────────────────────────────
def discover_links(soup, base_url, path, urls, scraped_urls):
    for anchor in soup.find_all('a'):
        link = anchor.attrs.get('href', '')
        if link.startswith('/'):
            link = base_url + link
        elif not link.startswith('http'):
            link = path + link
        if link not in urls and link not in scraped_urls:
            urls.append(link)

# ─── SAVE RESULTS ─────────────────────────────────────────────
def save_results(results, target_url):
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    domain = urllib.parse.urlsplit(target_url).netloc.replace('.', '_')
    filename = f"recon_{domain}_{timestamp}.json"

    results['emails'] = list(results['emails'])
    with open(filename, 'w') as f:
        json.dump(results, f, indent=4)
    print(colored(f"\n[*] Results saved to {filename}", 'cyan'))

# ─── MAIN ─────────────────────────────────────────────────────
def main():
    print_banner()

    target_url = input(colored("[*] Enter target URL to scan: ", 'cyan'))
    max_pages = input(colored("[*] Max pages to crawl (default 100): ", 'cyan'))
    max_pages = int(max_pages) if max_pages.strip() else 100
    save = input(colored("[*] Save results to file? (y/n): ", 'cyan')).lower()

    results = {
        'target': target_url,
        'scan_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'emails': set(),
        'headers': {},
        'missing_security_headers': [],
        'meta_tags': [],
        'html_comments': [],
        'forms': [],
        'js_files': [],
    }

    urls = deque([target_url])
    scraped_urls = set()
    count = 0

    print(colored(f"\n[*] Starting recon on {target_url}", 'cyan'))
    print(colored(f"[*] Max pages: {max_pages}\n", 'cyan'))
    print(colored("=" * 55, 'cyan'))

    try:
        while len(urls):
            count += 1
            if count > max_pages:
                break

            url = urls.popleft()
            scraped_urls.add(url)

            parts = urllib.parse.urlsplit(url)
            base_url = f"{parts.scheme}://{parts.netloc}"
            path = url[:url.rfind('/')+1] if '/' in parts.path else url

            print(colored(f"\n[{count}/{max_pages}] Scanning: {url}", 'cyan'))

            try:
                response = requests.get(url, timeout=5)
            except (requests.exceptions.MissingSchema,
                    requests.exceptions.ConnectionError,
                    requests.exceptions.Timeout):
                print(colored(f"  [!] Could not connect to {url}", 'red'))
                continue

            # Run all extractions
            if count == 1:
                analyse_headers(dict(response.headers), results)

            soup = BeautifulSoup(response.text, 'lxml')
            extract_emails(response.text, results)
            extract_meta(soup, results)
            extract_comments(soup, results)
            extract_forms(soup, url, results)
            extract_js(soup, base_url, results)
            discover_links(soup, base_url, path, urls, scraped_urls)

    except KeyboardInterrupt:
        print(colored("\n[!] Scan interrupted by user", 'red'))

    # Summary
    print(colored("\n" + "=" * 55, 'cyan'))
    print(colored("[*] SCAN COMPLETE -- SUMMARY", 'cyan'))
    print(colored("=" * 55, 'cyan'))
    print(colored(f"  Pages scanned:           {count}", 'white'))
    print(colored(f"  Emails found:            {len(results['emails'])}", 'green'))
    print(colored(f"  Missing security headers:{len(results['missing_security_headers'])}", 'red'))
    print(colored(f"  HTML comments found:     {len(results['html_comments'])}", 'red'))
    print(colored(f"  Forms detected:          {len(results['forms'])}", 'yellow'))
    print(colored(f"  JS files found:          {len(results['js_files'])}", 'cyan'))

    if save == 'y':
        save_results(results, target_url)

if __name__ == "__main__":
    main()