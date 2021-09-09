import json
import os
import sys
from pathlib import Path
from tempfile import gettempdir, mkstemp

import jq
import requests as r
from pygments import highlight
from pygments.formatters import TerminalFormatter
from pygments.lexers import JsonLexer


class ReqFile:
    def _populate(self, subject):
        for varname in os.environ:
            placeholder = "{%s}" % (varname,)
            subject = subject.replace(placeholder, os.environ.get(varname))
        return subject

    def __init__(self):
        self.method = "GET"
        self.url = None
        self.headers = {}
        self.filtr = None

    @classmethod
    def load(klass, filename):
        req = klass()
        with open(filename, "r") as f:
            line = f.readline()
            if line[0] != "#":
                raise ValueError()

            req.method, req.url = line[1:].split("^")
            req.url = req._populate(req.url.strip())

            # Headers and filter
            line = f.readline()
            while len(line) > 0 and line[0] == "#":
                if line[1] == "|":
                    req.filtr = jq.compile(req._populate(line[2:].strip()))
                elif ":" in line:
                    key, val = line[1:].split(":")
                    req.headers[key] = req._populate(val.strip())
                line = f.readline()
            req.payload = f.read()
            if req.payload.strip() == "":
                req.payload = None
        return req

    def execute(self):
        print(f"{self.method} {self.url}")
        return r.request(self.method, self.url, headers=self.headers, data=self.payload)


def main():
    for filename in sys.argv[1:]:
        if filename in ("--headers", "-f"):
            continue
        req = ReqFile.load(filename)
        resp = req.execute()

        if "--headers" in sys.argv:
            print(f"{resp.status_code} {resp.reason}")
            for hdr, val in resp.headers.items():
                print(f"{hdr}: {val}")

            print(" ")

        dispo = resp.headers.get("content-disposition")
        if dispo and "attachment" in dispo:
            if ";" in dispo:
                from pprint import pprint

                filename = dispo.split(";")[1].strip().split("=")[1].replace('"', "")
                filepath = Path(gettempdir()) / filename
            else:
                filepath = mkstemp()[1]

            with open(filepath, "wb") as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    f.write(chunk)
            return print(f"Response saved as {filepath}")

        try:
            result = resp.json()
            if req.filtr or "-f" in sys.argv:
                filtr = req.filtr
                if "-f" in sys.argv:
                    pattern = sys.argv[sys.argv.index("-f") + 1]
                    filtr = jq.compile(req._populate(pattern.strip()))
                result = filtr.input(result).all()

            print(
                highlight(
                    json.dumps(result, indent=4, sort_keys=True),
                    JsonLexer(),
                    TerminalFormatter(),
                )
            )
        except json.JSONDecodeError:
            print(resp.text)


if __name__ == "__main__":
    main()
