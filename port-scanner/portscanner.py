import socket
import termcolor
from datetime import datetime

def get_service(port):
    try:
        service = socket.getservbyport(port)
    except:
        service = "unknown"
    return service

def get_banner(sock):
    try:
        banner = sock.recv(1024).decode().strip()
        # Clean up banner - take only first line
        banner = banner.split('\n')[0]
    except:
        banner = "no banner"
    return banner

def scan_port(ipaddress, port):
    try:
        sock = socket.socket()
        sock.settimeout(1)
        sock.connect((ipaddress, port))
        service = get_service(port)
        banner = get_banner(sock)
        print(termcolor.colored(
            f"[+] Port {port:<6} OPEN | Service: {service:<12} | Banner: {banner}", 
            'green'
        ))
        sock.close()
    except:
        pass

def scan(target, ports):
    print(termcolor.colored(f"\n[*] Starting scan for {target}", 'yellow'))
    print(termcolor.colored(f"[*] Scanning ports 1 - {ports}", 'yellow'))
    print(termcolor.colored(f"[*] Scan started at {datetime.now().strftime('%H:%M:%S')}\n", 'yellow'))
    
    open_ports = []
    for port in range(1, ports + 1):
        result = scan_port(target, port)
        
    print(termcolor.colored(f"\n[*] Scan completed at {datetime.now().strftime('%H:%M:%S')}", 'yellow'))

def main():
    print(termcolor.colored("=" * 60, 'blue'))
    print(termcolor.colored("         SCYFIX PORT SCANNER v2.0", 'blue'))
    print(termcolor.colored("=" * 60, 'blue'))
    
    targets = input("\n[*] Enter target(s) to scan (split by comma): ")
    ports = int(input("[*] Enter number of ports to scan: "))
    
    if ',' in targets:
        print(termcolor.colored("\n[*] Scanning multiple targets...", 'cyan'))
        for ip_addr in targets.split(','):
            scan(ip_addr.strip(), ports)
    else:
        scan(targets, ports)

if __name__ == "__main__":
    main()