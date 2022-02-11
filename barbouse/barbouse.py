import json
import os
from pathlib import Path
from tempfile import gettempdir, mkstemp

import argparse

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
        with open(filename, "r", encoding="utf-8") as f:
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

    def execute(self, silent=False):
        if not silent:
            print(f"{self.method} {self.url}")
        return r.request(self.method, self.url, headers=self.headers, data=self.payload)


def main():
    parser = argparse.ArgumentParser(description="Send HTTP requests")
    parser.add_argument(
        "-H",
        "--headers",
        action="store_true",
        default=False,
        help="Only print the request headers",
    )
    parser.add_argument(
        "-b",
        "--body",
        action="store_true",
        default=False,
        help="Only output the response body",
    )
    parser.add_argument(
        "-f", "--filter", type=str, default=False, help="JQ filter override"
    )
    parser.add_argument(
        "-r",
        "--raw",
        default=False,
        help="Print raw response body (no JSON formatting)",
        action="store_true",
    )
    parser.add_argument("filename", type=str, nargs="+")

    args = parser.parse_args()

    for filename in args.filename:
        req = ReqFile.load(filename)
        resp = req.execute(silent=args.body)

        if args.headers:
            print(f"{resp.status_code} {resp.reason}")
            for hdr, val in resp.headers.items():
                print(f"{hdr}: {val}")

            print(" ")

        dispo = resp.headers.get("content-disposition")
        if dispo and "attachment" in dispo:
            if ";" in dispo:
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
            if req.filtr or args.filter:
                filtr = req.filtr
                if args.filter:
                    filtr = jq.compile(req._populate(args.filter.strip()))
                result = filtr.input(result).all()

            if args.raw:
                print(json.dumps(result, indent=4, sort_keys=True))
            else:
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
