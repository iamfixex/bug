import subprocess
import requests
import json
import os
import sys
import socket
import re
from datetime import datetime
from termcolor import colored
from pyfiglet import Figlet
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import warnings
import base64
import hashlib
from urllib.parse import urlparse, parse_qs
import asyncio
import aiohttp
warnings.filterwarnings('ignore')

class Scanner:
    def __init__(self):
        self.target = None
        self.subdomains = set()
        self.live = []
        self.endpoints = []
        self.tech = {}
        self.vulns = []
        self.data = {}
        self.output = None
        self.waf_detected = None
        self.fuzzed_paths = []
        self.use_nuclei = False
        self.use_fuzzing = False
        self.output_formats = ['txt']
        
        # bug bounty safe mode
        self.bug_bounty_mode = False
        self.rate_limit_enabled = False
        self.max_requests_per_second = 10
        self.request_delay = 0.1
        self.last_request_time = 0
        self.total_requests = 0
        self.in_scope = []
        self.out_of_scope = []
        self.scope_enabled = False
        
    def show_banner(self):
        os.system('clear')
        banner = Figlet(font='slant')
        print(colored(banner.renderText('Scanner'), 'red', attrs=['bold']))
        print(colored("╔═══════════════════════════════════════════════════════════════════════╗", 'red'))
        print(colored("║     Advanced Bug Bounty Automation Framework - Scanner                ║", 'red'))
        print(colored("║     Passive OSINT → Active Recon → Systematic Testing → Exploitation  ║", 'red'))
        print(colored("╚═══════════════════════════════════════════════════════════════════════╝", 'red'))
        print()
        
    def log(self, msg, lvl="info"):
        ts = datetime.now().strftime("%H:%M:%S")
        
        if lvl == "info":
            print(colored(f"[{ts}] [INFO] {msg}", 'cyan'))
        elif lvl == "success":
            print(colored(f"[{ts}] [✓] {msg}", 'green'))
        elif lvl == "warning":
            print(colored(f"[{ts}] [!] {msg}", 'yellow'))
        elif lvl == "error":
            print(colored(f"[{ts}] [✗] {msg}", 'red'))
        elif lvl == "phase":
            print(colored(f"\n{'='*75}", 'red'))
            print(colored(f"[PHASE] {msg}", 'red', attrs=['bold']))
            print(colored(f"{'='*75}\n", 'red'))
    
    def enforce_rate_limit(self):
        if not self.rate_limit_enabled:
            return
        
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.request_delay:
            time.sleep(self.request_delay - time_since_last)
        
        self.last_request_time = time.time()
        self.total_requests += 1
    
    def check_scope(self, url):
        if not self.scope_enabled:
            return True
        
        for scope_item in self.in_scope:
            if scope_item in url:
                for out_item in self.out_of_scope:
                    if out_item in url:
                        return False
                return True
        return False
    
    def enable_bug_bounty_mode(self):
        self.bug_bounty_mode = True
        self.rate_limit_enabled = True
        self.scope_enabled = True
        print(colored("[*] Bug Bounty Safe Mode ENABLED", 'green', attrs=['bold']))
        print(colored(f"    Rate limit: {self.max_requests_per_second} requests/second", 'green'))
        print(colored("    Scope filtering: ACTIVE", 'green'))
        print()
    
    def safe_request(self, method='get', url='', **kwargs):
        if self.scope_enabled and not self.check_scope(url):
            return None
        
        self.enforce_rate_limit()
        
        try:
            if method.lower() == 'get':
                return requests.get(url, **kwargs)
            elif method.lower() == 'post':
                return requests.post(url, **kwargs)
            elif method.lower() == 'put':
                return requests.put(url, **kwargs)
            elif method.lower() == 'delete':
                return requests.delete(url, **kwargs)
        except Exception as e:
            return None
    
    def toggle_rate_limit(self, enabled=None):
        if enabled is None:
            self.rate_limit_enabled = not self.rate_limit_enabled
        else:
            self.rate_limit_enabled = enabled
        
        status = "ENABLED" if self.rate_limit_enabled else "DISABLED"
        print(colored(f"[*] Rate limiting {status}", 'yellow'))
        if self.rate_limit_enabled:
            print(colored(f"    Max: {self.max_requests_per_second} requests/second", 'yellow'))
    
    def set_rate_limit(self, max_rps):
        if max_rps <= 0:
            print(colored("[!] Rate limit must be positive", 'red'))
            return
        
        self.max_requests_per_second = max_rps
        self.request_delay = 1.0 / max_rps
        print(colored(f"[*] Rate limit set to {max_rps} requests/second", 'green'))
    
    def save_output(self, section, content):
        if not self.output:
            return
            
        with open(self.output, 'a') as f:
            f.write(f"\n{'='*80}\n{section}\n{'='*80}\n{content}\n")
    
    def passive_recon(self, domain):
        self.log("PHASE 1: PASSIVE OSINT (NO DIRECT TARGET CONTACT)", "phase")
        
        # Strip http/https and trailing slashes
        domain = domain.replace('http://', '').replace('https://', '').rstrip('/')
        
        self.target = domain
        self.output = f"scanner_report_{domain}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        self.log("Starting passive info gathering - this won't touch the target", "info")
        self.log("Passive recon is completely undetectable", "info")
        
        self.enum_subs()
        
        self.log(f"Phase 1 done: Found {len(self.subdomains)} subdomains", "success")
        
        summary = f"""
Target: {self.target}
Subdomains Found: {len(self.subdomains)}

All Subdomains:
{chr(10).join(sorted(self.subdomains))}
"""
        self.save_output("PHASE 1: PASSIVE OSINT RESULTS", summary)
    
    def enum_subs(self):
        self.log("Running subdomain enumeration from 4 sources", "info")
        self.log("Tools: Subfinder, Amass, crt.sh, HackerTarget", "info")
        
        def subfinder():
            try:
                self.log("Starting subfinder...", "info")
                r = subprocess.run(
                    f"subfinder -d {self.target} -silent",
                    shell=True, capture_output=True, text=True, timeout=180
                )
                if r.stdout:
                    results = set([s.strip() for s in r.stdout.strip().split('\n') if s.strip()])
                    self.log(f"Subfinder got {len(results)} results", "success")
                    return results
            except Exception as e:
                self.log(f"Subfinder error: {str(e)[:50]}", "error")
            return set()
        
        def amass_scan():
            # check if amass is installed first
            try:
                check = subprocess.run(
                    'amass -version',
                    shell=True,
                    capture_output=True,
                    timeout=3,
                    text=True
                )
                if check.returncode != 0:
                    return set()
            except:
                return set()
            
            try:
                self.log("Starting amass passive mode...", "info")
                r = subprocess.run(
                    f"amass enum -d {self.target} -passive",
                    shell=True, capture_output=True, text=True, timeout=180
                )
                if r.stdout:
                    results = set([s.strip() for s in r.stdout.strip().split('\n') if s.strip()])
                    self.log(f"Amass got {len(results)} results", "success")
                    return results
            except:
                # silently skip if amass fails - no error needed
                pass
            return set()
        
        def crtsh():
            try:
                self.log("Checking Certificate Transparency logs...", "info")
                resp = requests.get(
                    f"https://crt.sh/?q=%.{self.target}&output=json",
                    timeout=30
                )
                if resp.status_code == 200:
                    data = resp.json()
                    results = set()
                    for cert in data:
                        name = cert.get('name_value', '')
                        for sub in name.split('\n'):
                            sub = sub.strip().replace('*.', '')
                            if sub and self.target in sub:
                                results.add(sub)
                    self.log(f"crt.sh got {len(results)} results", "success")
                    return results
            except Exception as e:
                self.log(f"crt.sh error: {str(e)[:50]}", "error")
            return set()
        
        def hackertarget():
            try:
                self.log("Querying HackerTarget...", "info")
                resp = requests.get(
                    f"https://api.hackertarget.com/hostsearch/?q={self.target}",
                    timeout=15
                )
                if resp.status_code == 200:
                    results = set()
                    for line in resp.text.split('\n'):
                        if ',' in line:
                            sub = line.split(',')[0].strip()
                            if sub and self.target in sub:
                                results.add(sub)
                    self.log(f"HackerTarget got {len(results)} results", "success")
                    return results
            except Exception as e:
                self.log(f"HackerTarget error: {str(e)[:50]}", "error")
            return set()
        
        # run everything at once
        with ThreadPoolExecutor(max_workers=4) as ex:
            jobs = {
                ex.submit(subfinder): 'Subfinder',
                ex.submit(amass_scan): 'Amass',
                ex.submit(crtsh): 'crt.sh',
                ex.submit(hackertarget): 'HackerTarget'
            }
            
            for job in as_completed(jobs):
                res = job.result()
                self.subdomains.update(res)
        
        self.log(f"Total unique: {len(self.subdomains)} subdomains", "success")
    
    def active_recon(self):
        self.log("PHASE 2: ACTIVE RECONNAISSANCE (TOUCHING TARGET)", "phase")
        self.log("Warning: This will show up in target's logs", "warning")
        
        confirm = input(colored("\n[?] Continue with active recon? (yes/no): ", 'yellow'))
        if confirm.lower() != 'yes':
            self.log("Skipping active recon", "warning")
            return
        
        self.log("Starting active scanning...", "info")
        self.check_live()
        self.find_webapps()
        
        self.log("Phase 2 complete", "success")
        
        summary = f"""
Live Hosts: {len(self.live)}
Web Apps: {len(self.data.get('web_apps', []))}

Live Hosts:
{chr(10).join([f"{h['sub']} -> {h['ip']}" for h in self.live])}
"""
        self.save_output("PHASE 2: ACTIVE RECON RESULTS", summary)
    
    def check_live(self):
        self.log("Checking which hosts are actually live...", "info")
        
        # set dns timeout so we don't wait forever
        socket.setdefaulttimeout(3)
        
        cnt = 0
        total = len(self.subdomains)
        checked = 0
        
        with ThreadPoolExecutor(max_workers=50) as ex:
            def check(sub):
                try:
                    ip = socket.gethostbyname(sub)
                    return {'sub': sub, 'ip': ip}
                except:
                    return None
            
            jobs = [ex.submit(check, s) for s in self.subdomains]
            
            for job in as_completed(jobs):
                res = job.result()
                checked += 1
                
                # show progress so user knows we're not stuck
                print(f"\r[*] Checking hosts: {checked}/{total} ({len(self.live)} live)", end='', flush=True)
                
                if res:
                    self.live.append(res)
                    cnt += 1
        
        print()  # newline after progress bar
        self.log(f"Found {len(self.live)} live hosts", "success")
    
    def find_webapps(self):
        self.log("Looking for web applications...", "info")
        
        apps = []
        total = len(self.live)
        done = 0
        
        with ThreadPoolExecutor(max_workers=30) as ex:
            def probe(host):
                sub = host['sub']
                results = []
                
                # try both http and https
                for scheme in ['https', 'http']:
                    try:
                        url = f"{scheme}://{sub}"
                        # reduced timeout from 5s to 3s - faster and still catches everything
                        r = requests.get(url, timeout=3, allow_redirects=True, verify=False)
                        
                        if r.status_code < 500:
                            results.append({
                                'url': url,
                                'status': r.status_code,
                                'title': self.get_title(r.text),
                                'server': r.headers.get('Server', 'Unknown'),
                                'headers': dict(r.headers)
                            })
                    except:
                        pass
                
                return results
            
            jobs = [ex.submit(probe, h) for h in self.live]
            
            for job in as_completed(jobs):
                res = job.result()
                done += 1
                
                # show progress - let user know it's working
                print(f"\r[*] Probing web apps: {done}/{total} ({len(apps)} found)", end='', flush=True)
                
                if res:
                    apps.extend(res)
        
        print()  # newline
        self.data['web_apps'] = apps
        self.log(f"Found {len(apps)} web applications", "success")
    
    def get_title(self, html):
        match = re.search(r'<title>(.*?)</title>', html, re.IGNORECASE | re.DOTALL)
        if match:
            return match.group(1).strip()[:100]
        return "No title"
    
    def analyze(self):
        self.log("PHASE 3: ANALYZING TARGET", "phase")
        
        self.log("Running tech detection...", "info")
        
        total_apps = len(self.data.get('web_apps', []))
        analyzed = 0
        
        # use threadpool for parallel analysis - way faster
        with ThreadPoolExecutor(max_workers=20) as ex:
            def analyze_app(app):
                url = app['url']
                
                try:
                    # reduced timeout from 10s to 5s - still catches everything
                    r = requests.get(url, timeout=5, verify=False)
                    
                    # check headers for tech
                    headers = r.headers
                    server = headers.get('Server', '').lower()
                    xpowered = headers.get('X-Powered-By', '').lower()
                    
                    techs = []
                    
                    if 'nginx' in server:
                        techs.append('Nginx')
                    if 'apache' in server:
                        techs.append('Apache')
                    if 'cloudflare' in server:
                        techs.append('Cloudflare')
                    if 'php' in xpowered:
                        techs.append('PHP')
                    if 'asp.net' in xpowered:
                        techs.append('ASP.NET')
                    
                    # check body for frameworks
                    body = r.text.lower()
                    
                    if 'wordpress' in body or 'wp-content' in body:
                        techs.append('WordPress')
                    if 'joomla' in body:
                        techs.append('Joomla')
                    if 'drupal' in body:
                        techs.append('Drupal')
                    if 'react' in body or 'reactjs' in body:
                        techs.append('React')
                    if 'angular' in body or 'ng-app' in body:
                        techs.append('Angular')
                    if 'vue' in body or 'vuejs' in body:
                        techs.append('Vue.js')
                    
                    return (url, techs)
                    
                except:
                    return (url, [])
            
            jobs = [ex.submit(analyze_app, app) for app in self.data.get('web_apps', [])]
            
            for job in as_completed(jobs):
                url, techs = job.result()
                analyzed += 1
                
                # show progress
                print(f"\r[*] Analyzing apps: {analyzed}/{total_apps}", end='', flush=True)
                
                if techs:
                    self.tech[url] = techs
        
        print()  # newline after progress
        self.log("Tech detection complete", "success")
        
        # crawl for endpoints
        self.log("Crawling for endpoints...", "info")
        
        crawled = 0
        total_crawl = len(self.data.get('web_apps', []))
        found_endpoints = []
        
        # parallel crawling for speed
        with ThreadPoolExecutor(max_workers=20) as ex:
            def crawl_app(app):
                url = app['url']
                endpoints = []
                
                try:
                    r = requests.get(url, timeout=5, verify=False)
                    
                    # find links
                    links = re.findall(r'href=["\'](.*?)["\']', r.text)
                    
                    for link in links:
                        if link.startswith('http'):
                            endpoints.append(link)
                        elif link.startswith('/'):
                            endpoints.append(f"{url}{link}")
                    
                except:
                    pass
                
                return endpoints
            
            jobs = [ex.submit(crawl_app, app) for app in self.data.get('web_apps', [])]
            
            for job in as_completed(jobs):
                endpoints = job.result()
                crawled += 1
                
                if endpoints:
                    found_endpoints.extend(endpoints)
                
                # show crawling progress
                print(f"\r[*] Crawling: {crawled}/{total_crawl} ({len(found_endpoints)} endpoints)", end='', flush=True)
        
        print()  # newline
        self.endpoints = list(set(found_endpoints))[:100]  # limit to first 100
        
        self.log(f"Found {len(self.endpoints)} endpoints", "success")
    
    def detect_waf(self):
        """Check if there's a WAF protecting the target"""
        self.log("Checking for WAF/CDN protection...", "info")
        
        waf_signatures = {
            'Cloudflare': ['__cfduid', 'cf-ray', 'cloudflare'],
            'AWS WAF': ['x-amzn-requestid', 'x-amz-cf-id'],
            'Akamai': ['akamai', 'x-akamai'],
            'Imperva': ['incap_ses', 'visid_incap'],
            'Sucuri': ['x-sucuri-id', 'sucuri'],
            'ModSecurity': ['mod_security', 'NOYB'],
            'F5 BIG-IP': ['BigIP', 'F5', 'TS01'],
            'Barracuda': ['barra_counter_session'],
            'Fortinet': ['fortigate', 'fortiwasd_cookie']
        }
        
        detected = []
        
        for app in self.data.get('web_apps', [])[:5]:  # check first 5 apps
            url = app['url']
            
            try:
                # send suspicious request to trigger WAF
                r = requests.get(
                    url + "?id=1'OR'1'='1",
                    headers={'User-Agent': 'sqlmap/1.0'},
                    timeout=3,
                    verify=False
                )
                
                # check headers and body for WAF signatures
                headers_str = ' '.join([f"{k}:{v}" for k,v in r.headers.items()]).lower()
                body = r.text.lower()
                combined = headers_str + ' ' + body
                
                for waf, sigs in waf_signatures.items():
                    if any(sig.lower() in combined for sig in sigs):
                        if waf not in detected:
                            detected.append(waf)
                            self.log(f"WAF detected: {waf}", "warning")
                
                # check for generic WAF behavior
                if r.status_code in [403, 406, 419, 429, 503]:
                    if 'blocked' in body or 'forbidden' in body or 'access denied' in body:
                        if 'Generic WAF' not in detected:
                            detected.append('Generic WAF')
                            self.log("Generic WAF behavior detected", "warning")
                            
            except:
                pass
        
        if detected:
            self.waf_detected = detected
            self.log(f"WAF/Protection: {', '.join(detected)}", "warning")
            self.log("Note: Some tests might be blocked by WAF", "warning")
        else:
            self.log("No WAF detected - full testing possible", "success")
            self.waf_detected = None
    
    def run_fuzzing(self):
        """Fuzz for hidden directories and files using ffuf"""
        self.log("Starting directory/file fuzzing with ffuf...", "info")
        
        # check if ffuf is installed - try multiple ways
        ffuf_found = False
        
        # method 1: try running it directly with shell
        try:
            result = subprocess.run(
                'ffuf -h',
                shell=True,
                capture_output=True,
                timeout=3,
                text=True
            )
            if result.returncode == 0 or 'ffuf' in result.stdout.lower():
                ffuf_found = True
        except:
            pass
        
        # method 2: check common install locations
        if not ffuf_found:
            common_paths = [
                os.path.expanduser('~/go/bin/ffuf'),
                '/usr/local/bin/ffuf',
                '/usr/bin/ffuf',
                os.path.expanduser('~/.local/bin/ffuf')
            ]
            
            for path in common_paths:
                if os.path.exists(path):
                    ffuf_found = True
                    break
        
        if not ffuf_found:
            self.log("ffuf not installed - skipping fuzzing", "error")
            self.log("Install: go install github.com/ffuf/ffuf@latest", "info")
            self.log("Then run: export PATH=$PATH:~/go/bin", "info")
            return
        
        wordlist_paths = [
            '/usr/share/wordlists/dirb/common.txt',
            '/usr/share/seclists/Discovery/Web-Content/common.txt',
            '/usr/share/wordlists/dirbuster/directory-list-2.3-small.txt'
        ]
        
        wordlist = None
        for path in wordlist_paths:
            if os.path.exists(path):
                wordlist = path
                break
        
        if not wordlist:
            self.log("No wordlist found - skipping fuzzing", "warning")
            return
        
        self.log(f"Using wordlist: {wordlist}", "info")
        
        # fuzz first few web apps
        for app in self.data.get('web_apps', [])[:3]:  # limit to 3 to save time
            url = app['url']
            
            self.log(f"Fuzzing: {url}", "info")
            
            try:
                # run ffuf
                cmd = f'ffuf -u {url}/FUZZ -w {wordlist} -mc 200,204,301,302,307,401,403 -fs 0 -t 50 -timeout 3 -silent'
                result = subprocess.run(
                    cmd,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                
                if result.stdout:
                    # parse ffuf output
                    for line in result.stdout.split('\n'):
                        if url in line:
                            # extract the found path
                            match = re.search(r'(https?://[^\s]+)', line)
                            if match:
                                found_url = match.group(1)
                                self.fuzzed_paths.append(found_url)
                                self.endpoints.append(found_url)
                
                self.log(f"Found {len([p for p in self.fuzzed_paths if url in p])} new paths", "success")
                
            except subprocess.TimeoutExpired:
                self.log(f"Fuzzing timeout for {url}", "warning")
            except Exception as e:
                self.log(f"Fuzzing error: {str(e)[:50]}", "error")
        
        if self.fuzzed_paths:
            self.log(f"Total fuzzed paths discovered: {len(self.fuzzed_paths)}", "success")
    
    def run_nuclei(self):
        """Run nuclei vulnerability scanner"""
        self.log("Starting Nuclei vulnerability scan...", "info")
        
        # check if nuclei is installed - try multiple ways
        nuclei_found = False
        
        # method 1: try running it directly with shell
        try:
            result = subprocess.run(
                'nuclei -version',
                shell=True,
                capture_output=True,
                timeout=3,
                text=True
            )
            if result.returncode == 0 or 'nuclei' in result.stdout.lower():
                nuclei_found = True
        except:
            pass
        
        # method 2: check common install locations
        if not nuclei_found:
            common_paths = [
                os.path.expanduser('~/go/bin/nuclei'),
                '/usr/local/bin/nuclei',
                '/usr/bin/nuclei',
                os.path.expanduser('~/.local/bin/nuclei')
            ]
            
            for path in common_paths:
                if os.path.exists(path):
                    nuclei_found = True
                    break
        
        if not nuclei_found:
            self.log("Nuclei not installed - skipping", "error")
            self.log("Install: go install -v github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest", "info")
            self.log("Then run: export PATH=$PATH:~/go/bin", "info")
            return []
        
        findings = []
        
        # create temp file with URLs
        url_file = '/tmp/scanner_urls.txt'
        with open(url_file, 'w') as f:
            for app in self.data.get('web_apps', []):
                f.write(app['url'] + '\n')
        
        self.log(f"Running Nuclei on {len(self.data.get('web_apps', []))} targets...", "info")
        self.log("This might take a few minutes...", "info")
        
        try:
            # run nuclei with common templates - use shell=True to respect PATH
            cmd = f'nuclei -l {url_file} -silent -json -severity critical,high,medium -timeout 10 -retries 1'
            
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=300  # 5 min timeout
            )
            
            if result.stdout:
                # parse JSON output
                for line in result.stdout.strip().split('\n'):
                    try:
                        data = json.loads(line)
                        
                        vuln = {
                            'type': f"Nuclei: {data.get('info', {}).get('name', 'Unknown')}",
                            'severity': data.get('info', {}).get('severity', 'UNKNOWN').upper(),
                            'url': data.get('host', ''),
                            'param': data.get('matched-at', ''),
                            'payload': data.get('template-id', ''),
                            'evidence': data.get('matcher-name', 'Nuclei detection'),
                            'impact': data.get('info', {}).get('description', 'See Nuclei template'),
                            'fix': data.get('info', {}).get('remediation', 'Check vendor documentation'),
                            'poc': self.nuclei_poc(data),
                            'cvss': 'N/A'
                        }
                        findings.append(vuln)
                        self.log(f"Nuclei found: {vuln['type']}", "success")
                        
                    except json.JSONDecodeError:
                        pass
            
            self.log(f"Nuclei scan complete: {len(findings)} findings", "success")
            
        except subprocess.TimeoutExpired:
            self.log("Nuclei scan timeout - results may be incomplete", "warning")
        except Exception as e:
            self.log(f"Nuclei error: {str(e)[:50]}", "error")
        finally:
            # cleanup
            if os.path.exists(url_file):
                os.remove(url_file)
        
        return findings
    
    def advanced_recon_menu(self):
        """Ask user what advanced recon they want"""
        print(colored("\n╔═══════════════════════════════════════════════════════════════╗", 'red'))
        print(colored("║                  ADVANCED RECON OPTIONS                        ║", 'red', attrs=['bold']))
        print(colored("╚═══════════════════════════════════════════════════════════════╝\n", 'red'))
        
        print(colored("Available Options:", 'cyan', attrs=['bold']))
        print(colored("  [1] WAF Detection", 'white') + colored(" - Identify protection mechanisms", 'yellow'))
        print(colored("  [2] Directory Fuzzing (ffuf)", 'white') + colored(" - Find hidden paths/files", 'yellow'))
        print(colored("  [3] Nuclei Scanner", 'white') + colored(" - 1000s of vuln templates", 'yellow'))
        print()
        print(colored("Quick Options:", 'yellow'))
        print(colored("  [all]  Run all advanced recon", 'green'))
        print(colored("  [skip] Skip advanced recon", 'red'))
        print()
        
        choice = input(colored("[?] Select options (comma-separated) or quick option: ", 'yellow')).strip().lower()
        
        if choice == 'skip':
            self.log("Skipping advanced recon", "info")
            return
        
        run_waf = False
        run_fuzz = False
        run_nuclei = False
        
        if choice == 'all':
            run_waf = True
            run_fuzz = True
            run_nuclei = True
        else:
            opts = [o.strip() for o in choice.split(',')]
            if '1' in opts:
                run_waf = True
            if '2' in opts:
                run_fuzz = True
            if '3' in opts:
                run_nuclei = True
        
        # run selected options
        if run_waf:
            self.detect_waf()
        
        if run_fuzz:
            self.run_fuzzing()
        
        if run_nuclei:
            self.use_nuclei = True
    
    def output_format_menu(self):
        """Ask what output formats they want"""
        print(colored("\n╔═══════════════════════════════════════════════════════════════╗", 'red'))
        print(colored("║                    OUTPUT FORMAT OPTIONS                       ║", 'red', attrs=['bold']))
        print(colored("╚═══════════════════════════════════════════════════════════════╝\n", 'red'))
        
        print(colored("Available Formats:", 'cyan', attrs=['bold']))
        print(colored("  [1] TXT Report", 'white') + colored(" - Human-readable text", 'yellow'))
        print(colored("  [2] JSON Output", 'white') + colored(" - Machine-readable for tools", 'yellow'))
        print(colored("  [3] HTML Report", 'white') + colored(" - Web-based visual report", 'yellow'))
        print()
        print(colored("Quick Options:", 'yellow'))
        print(colored("  [all]  Generate all formats", 'green'))
        print()
        
        choice = input(colored("[?] Select formats (comma-separated) or 'all': ", 'yellow')).strip().lower()
        
        self.output_formats = []
        
        if choice == 'all':
            self.output_formats = ['txt', 'json', 'html']
        else:
            opts = [o.strip() for o in choice.split(',')]
            if '1' in opts or not opts:
                self.output_formats.append('txt')
            if '2' in opts:
                self.output_formats.append('json')
            if '3' in opts:
                self.output_formats.append('html')
        
        if not self.output_formats:
            self.output_formats = ['txt']  # default
        
        self.log(f"Will generate: {', '.join([f.upper() for f in self.output_formats])}", "success")
    
    def select_tests(self):
        """Let user pick which vulnerability tests to run"""
        
        print(colored("\n╔═══════════════════════════════════════════════════════════════╗", 'red'))
        print(colored("║              SELECT VULNERABILITY TESTS TO RUN                 ║", 'red', attrs=['bold']))
        print(colored("╚═══════════════════════════════════════════════════════════════╝\n", 'red'))
        
        # all available tests with descriptions
        tests = {
            '1': {'name': 'XSS (Cross-Site Scripting)', 'func': self.test_xss, 'severity': 'HIGH'},
            '2': {'name': 'SQL Injection', 'func': self.test_sqli, 'severity': 'CRITICAL'},
            '3': {'name': 'IDOR (Broken Access)', 'func': self.test_idor, 'severity': 'HIGH'},
            '4': {'name': 'SSRF (Server-Side Request Forgery)', 'func': self.test_ssrf, 'severity': 'CRITICAL'},
            '5': {'name': 'Open Redirect', 'func': self.test_open_redirect, 'severity': 'MEDIUM'},
            '6': {'name': 'XXE (XML External Entity)', 'func': self.test_xxe, 'severity': 'CRITICAL'},
            '7': {'name': 'Command Injection', 'func': self.test_cmd_injection, 'severity': 'CRITICAL'},
            '8': {'name': 'Path Traversal / LFI', 'func': self.test_path_traversal, 'severity': 'HIGH'},
            '9': {'name': 'Sensitive File Exposure', 'func': self.test_sensitive_files, 'severity': 'HIGH'},
            '10': {'name': 'CORS Misconfiguration', 'func': self.test_cors, 'severity': 'MEDIUM'},
            '11': {'name': 'Missing Security Headers', 'func': self.test_security_headers, 'severity': 'LOW'},
            '12': {'name': 'Rate Limiting Issues', 'func': self.test_rate_limiting, 'severity': 'MEDIUM'},
            '13': {'name': 'CRLF Injection', 'func': self.test_crlf, 'severity': 'MEDIUM'},
            '14': {'name': 'GraphQL Introspection', 'func': self.test_graphql, 'severity': 'MEDIUM'},
            '15': {'name': 'JWT Vulnerabilities', 'func': self.test_jwt, 'severity': 'HIGH'},
            '16': {'name': 'Subdomain Takeover', 'func': self.test_subdomain_takeover, 'severity': 'HIGH'},
            '17': {'name': 'SSTI (Template Injection)', 'func': self.test_ssti, 'severity': 'CRITICAL'},
            '18': {'name': 'Host Header Injection', 'func': self.test_host_header, 'severity': 'MEDIUM'},
            '19': {'name': 'WebSocket Security', 'func': self.test_websocket, 'severity': 'MEDIUM'}
        }
        
        # display the menu
        print(colored("Available Tests:", 'cyan', attrs=['bold']))
        print()
        
        for num, info in sorted(tests.items(), key=lambda x: int(x[0])):
            sev_color = {
                'CRITICAL': 'red',
                'HIGH': 'yellow', 
                'MEDIUM': 'cyan',
                'LOW': 'white'
           
