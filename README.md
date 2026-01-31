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
