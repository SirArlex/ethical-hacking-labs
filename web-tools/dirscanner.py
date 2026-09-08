import requests
import requests.exceptions
from termcolor import colored
from datetime import datetime
import sys
import threading
from queue import Queue

# ─── BANNER ───────────────────────────────────────────────────
def print_banner():
    print(colored("""
╔═══════════════════════════════════════════════════╗
║         SCYFIX DIRECTORY SCANNER v2.0             ║
║      Web Directory & Path Discovery Tool          ║
╚═══════════════════════════════════════════════════╝
""", 'cyan'))

# ─── GLOBALS ──────────────────────────────────────────────────
found_directories = []
lock = threading.Lock()
progress_count = 0
total_count = 0

# ─── NORMALIZE URL ────────────────────────────────────────────
def normalize_url(url):
    url = url.strip()
    if not url.startswith('http://') and not url.startswith('https://'):
        url = 'http://' + url
    return url.rstrip('/')

# ─── SCAN DIRECTORY ───────────────────────────────────────────
def scan_directory(target_url, directory, extensions, save):
    global progress_count

    paths = [directory]
    for ext in extensions:
        paths.append(directory + '.' + ext)

    for path in paths:
        full_url = target_url + '/' + path

        try:
            response = requests.get(full_url, timeout=5, allow_redirects=False)
            status = response.status_code

            with lock:
                progress_count += 1
                sys.stdout.write(colored(
                    f"\r  [*] Progress: {progress_count}/{total_count} | Trying: {path:<40}",
                    'cyan'
                ))
                sys.stdout.flush()

                if status == 200:
                    msg = f"[200] FOUND:     {full_url}"
                    print(colored(f"\n  [+] {msg}", 'green'))
                    found_directories.append(msg)
                elif status == 301 or status == 302:
                    location = response.headers.get('Location', 'unknown')
                    msg = f"[{status}] REDIRECT:  {full_url} --> {location}"
                    print(colored(f"\n  [~] {msg}", 'yellow'))
                    found_directories.append(msg)
                elif status == 403:
                    msg = f"[403] FORBIDDEN: {full_url}"
                    print(colored(f"\n  [!] {msg}", 'red'))
                    found_directories.append(msg)
                elif status == 500:
                    msg = f"[500] SERVER ERROR: {full_url}"
                    print(colored(f"\n  [!] {msg}", 'red'))
                    found_directories.append(msg)

        except requests.exceptions.ConnectionError:
            pass
        except requests.exceptions.Timeout:
            pass

# ─── WORKER THREAD ────────────────────────────────────────────
def worker(target_url, queue, extensions, save):
    while not queue.empty():
        directory = queue.get()
        scan_directory(target_url, directory, extensions, save)
        queue.task_done()

# ─── SAVE RESULTS ─────────────────────────────────────────────
def save_results(target_url):
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    domain = target_url.replace('http://', '').replace('https://', '').replace('/', '_')
    filename = f"dirscan_{domain}_{timestamp}.txt"
    with open(filename, 'w') as f:
        f.write(f"Scyfix Directory Scanner Results\n")
        f.write(f"Target: {target_url}\n")
        f.write(f"Scan Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 60 + "\n\n")
        for entry in found_directories:
            f.write(entry + "\n")
    print(colored(f"\n[*] Results saved to {filename}", 'cyan'))

# ─── MAIN ─────────────────────────────────────────────────────
def main():
    global total_count

    print_banner()

    target_url = input(colored("[*] Enter target URL: ", 'cyan'))
    wordlist = input(colored("[*] Enter path to wordlist file: ", 'cyan'))
    threads = input(colored("[*] Number of threads (default 10): ", 'cyan'))
    threads = int(threads) if threads.strip() else 10
    ext_input = input(colored("[*] File extensions to check e.g. php,html,txt (leave blank to skip): ", 'cyan'))
    extensions = [e.strip() for e in ext_input.split(',')] if ext_input.strip() else []
    save = input(colored("[*] Save results to file? (y/n): ", 'cyan')).lower()

    target_url = normalize_url(target_url)

    try:
        with open(wordlist, 'r', encoding='utf-8', errors='ignore') as f:
            directories = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print(colored(f"[-] Wordlist not found: {wordlist}", 'red'))
        return

    total_count = len(directories) * (1 + len(extensions))

    queue = Queue()
    for directory in directories:
        queue.put(directory)

    print(colored(f"\n[*] Target:    {target_url}", 'cyan'))
    print(colored(f"[*] Wordlist:  {len(directories)} entries", 'cyan'))
    print(colored(f"[*] Threads:   {threads}", 'cyan'))
    print(colored(f"[*] Extensions: {extensions if extensions else 'none'}", 'cyan'))
    print(colored(f"[*] Scan started at {datetime.now().strftime('%H:%M:%S')}", 'cyan'))
    print(colored("=" * 55, 'cyan'))

    thread_list = []
    for _ in range(threads):
        t = threading.Thread(
            target=worker,
            args=(target_url, queue, extensions, save)
        )
        t.daemon = True
        t.start()
        thread_list.append(t)

    for t in thread_list:
        t.join()

    print(colored(f"\n\n[*] Scan completed at {datetime.now().strftime('%H:%M:%S')}", 'cyan'))
    print(colored("=" * 55, 'cyan'))
    print(colored(f"[*] Total found: {len(found_directories)}", 'green'))

    if found_directories:
        print(colored("\n[*] Summary of findings:", 'cyan'))
        for entry in found_directories:
            if entry.startswith('[200]'):
                print(colored(f"  {entry}", 'green'))
            elif entry.startswith('[403]') or entry.startswith('[500]'):
                print(colored(f"  {entry}", 'red'))
            else:
                print(colored(f"  {entry}", 'yellow'))

    if save == 'y':
        save_results(target_url)

if __name__ == "__main__":
    main()