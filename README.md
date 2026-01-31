# clone it
git clone https://github.com/iamfixex/bug
cd bug

# install python stuff
pip install requests termcolor pyfiglet aiohttp

# optional but recommended - for advanced features
go install github.com/ffuf/ffuf@latest
go install -v github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest
go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest
go install -v github.com/owasp-amass/amass/v4/...@master

# update nuclei templates
nuclei -update-templates

# get wordlists for fuzzing
sudo apt install seclists
# or just grab dirb's common.txt


vulnerability test reference

Test #  | Name                    | Severity
--------|-------------------------|----------
1       | XSS                     | HIGH
2       | SQL Injection           | CRITICAL
3       | IDOR                    | HIGH
4       | SSRF                    | CRITICAL
5       | Open Redirect           | MEDIUM
6       | XXE                     | CRITICAL
7       | Command Injection       | CRITICAL
8       | Path Traversal          | HIGH
9       | Sensitive Files         | HIGH
10      | CORS Misconfiguration   | MEDIUM
11      | Security Headers        | LOW
12      | Rate Limiting           | MEDIUM
13      | CRLF Injection          | MEDIUM
14      | GraphQL Introspection   | MEDIUM
15      | JWT Vulnerabilities     | HIGH
16      | Subdomain Takeover      | HIGH
17      | SSTI                    | CRITICAL
18      | Host Header Injection   | MEDIUM
19      | WebSocket Security      | MEDIUM
