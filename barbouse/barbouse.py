import json
from pygments import highlight
from pygments.lexers import JsonLexer
from pygments.formatters import TerminalFormatter
import sys
import os
import requests as r
import jq
import logging

log = logging.getLogger("barbouse")

class Command:
    def __init__(self, cmd):
        command = cmd.split("#")
        self.method = command[0]
        self.url = command[1]
        for varname in os.environ:
            placeholder = "{%s}" % (varname,)
            self.url = self.url.replace(placeholder, os.environ.get(varname))

        print(self.url)
        self.filtr = None
        if len(command) > 2:
            self.filtr = command[2]

def main():
    filename = sys.argv[1]
    with open(filename, 'r') as f:
        cmd = Command(f.readline())
        payload = f.read()

    resp = r.request(cmd.method, cmd.url)
    result = resp.json()
    if cmd.filtr:
        result = jq.compile(cmd.filtr).input(resp.json()).all()

    print(highlight(json.dumps(result, indent=4, sort_keys=True), JsonLexer(), TerminalFormatter()))
    
    

if __name__ == "__main__":
    main()
