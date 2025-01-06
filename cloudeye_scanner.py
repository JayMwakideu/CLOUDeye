#!/usr/bin/env python3
import requests
import sys
import argparse
from termcolor import colored
import time
import re
import json
import csv
from datetime import datetime
import pyfiglet

# Generate a banner
banner = pyfiglet.figlet_format("CLOUDeye")
print(banner)

# Default paths to scan for sensitive files
DEFAULT_PATHS = [
    "config.yml",
    "secrets.json",
    "backup.tar.gz",
    "env.bak",
    "db_dump.sql",
    "private_keys/",
    "admin_panel/",
    "settings.ini"
]

# Patterns to detect sensitive data
SENSITIVE_PATTERNS = {
    "API Key": r"(?:api[_-]?key|apikey)[\s=:\"']+([a-zA-Z0-9_\-]{10,})",
    "Access Token": r"(?:token|bearer)[\s=:\"']+([a-zA-Z0-9.\-_]{10,})",
    "Password": r"(?:password|pwd)[\s=:\"']+([^\s\"']{5,})",
    "JWT": r"eyJ[a-zA-Z0-9\-_]+\.[a-zA-Z0-9\-_]+\.[a-zA-Z0-9\-_]+",
    "Private Key": r"-----BEGIN (?:RSA|EC|DSA|OPENSSH) PRIVATE KEY-----",
    "AWS Access Key": r"AKIA[0-9A-Z]{16}",
    "Email Address": r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+",
    "IP Address": r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b",
}

# App banner with graphics
def print_banner():
    banner = """
    ###################################################
    #                                                 #
    #                  CLOUDeye Scanner               #
    #       By: Japhet Mwakideu                      #
    #       GitHub: https://github.com/JayMwakideu   #
    #                                                 #
    ###################################################

    DISCLAIMER: Use responsibly and ethically.
    Unauthorized or malicious use is prohibited.
    ###################################################
    """
    print(colored(banner, "cyan", attrs=["bold"]))

# Parse command-line arguments
def parse_arguments():
    parser = argparse.ArgumentParser(description="CLOUDeye Scanner: Identify sensitive configurations and files.")
    parser.add_argument("-u", "--url", type=str, required=True, help="Target URL or domain to scan.")
    parser.add_argument("-m", "--mode", type=str, choices=["basic", "full"], default="basic",
                        help="Scan mode: 'basic' (quick) or 'full' (deep). Default: 'basic'.")
    parser.add_argument("--proxy", type=str, help="Optional proxy server (e.g., http://127.0.0.1:8080).")
    parser.add_argument("-o", "--output", type=str, default="cloudeye_results", help="Base name for output files.")
    parser.add_argument("--custom-list", type=str, help="Path to a custom file list for scanning.")
    return parser.parse_args()

# Load custom file paths
def load_custom_paths(filepath):
    try:
        with open(filepath, "r") as file:
            return [line.strip() for line in file if line.strip()]
    except FileNotFoundError:
        print(colored(f"[!] Custom file not found: {filepath}", "red"))
        sys.exit(1)

# Scan for sensitive files on the target
def scan_paths(base_url, paths, proxy=None):
    print(colored("[*] Starting scan for sensitive files...", "cyan"))
    headers = {
        "User-Agent": "CLOUDeye/1.0 (Scanner)",
        "Accept": "*/*",
    }
    found_files = []
    errors = []
    results = []

    for path in paths:
        full_url = f"{base_url.rstrip('/')}/{path}"
        try:
            response = requests.get(full_url, headers=headers, proxies={"http": proxy, "https": proxy} if proxy else None, timeout=5)
            time.sleep(1)
            if response.status_code == 200:
                print(colored(f"[+] Found: {full_url} (200 OK)", "green"))
                sensitive_data = analyze_content(response.text, full_url)
                if sensitive_data:
                    results.append({"url": full_url, "sensitive_data": sensitive_data})
                found_files.append(full_url)
            elif response.status_code == 404:
                print(colored(f"[-] Not Found: {full_url}", "yellow"))
            else:
                print(colored(f"[!] Unexpected response: {response.status_code} for {full_url}", "yellow"))
        except requests.RequestException as e:
            print(colored(f"[!] Error accessing {full_url}: {e}", "red"))
            errors.append(full_url)

    print(colored("[*] Scan completed.", "cyan"))
    return found_files, errors, results

# Analyze content for sensitive data
def analyze_content(content, url):
    print(colored(f"[*] Analyzing content from {url}...", "cyan"))
    sensitive_data = {}
    for label, pattern in SENSITIVE_PATTERNS.items():
        matches = re.findall(pattern, content, re.IGNORECASE)
        if matches:
            sensitive_data[label] = list(set(matches))  # Deduplicate matches
            print(colored(f"[!] Found {label} in {url}: {matches}", "red"))
    return sensitive_data

# Save results to JSON and CSV

def save_results(output_base, results):
    json_file = f"{output_base}.json"
    csv_file = f"{output_base}.csv"

    # Save as JSON
    with open(json_file, "w") as jf:
        json.dump(results, jf, indent=4)
    print(colored(f"[+] Results saved to {json_file}", "green"))

    # Save as CSV
    with open(csv_file, "w", newline="") as cf:
        writer = csv.writer(cf)
        writer.writerow(["URL", "Sensitive Data"])
        for result in results:
            writer.writerow([result["url"], json.dumps(result["sensitive_data"])] if result["sensitive_data"] else "No Sensitive Data")

    print(colored(f"[+] Results saved to {csv_file}", "green"))

# Main function
def main():
    print_banner()
    args = parse_arguments()
    start_time = datetime.now()

    paths = DEFAULT_PATHS
    if args.custom_list:
        paths = load_custom_paths(args.custom_list)

    found_files, errors, results = scan_paths(args.url, paths, args.proxy)

    save_results(args.output, results)

    print(colored("\n[Summary]", "cyan"))
    print(f"  Found files: {len(found_files)}")
    print(f"  Errors: {len(errors)}")
    print(f"  Time Elapsed: {datetime.now() - start_time}")

if __name__ == "__main__":
    main()
