#!/usr/bin/env python3
"""Idempotently replace the celeb.platformengineer.io site block in the Caddyfile.
Removes any existing (brace-balanced) block for the site, then appends the new one."""
import sys

CADDYFILE = "/etc/caddy/Caddyfile"
SITE = "celeb.platformengineer.io"
NEW_BLOCK = open(sys.argv[1]).read().strip() + "\n"

src = open(CADDYFILE).read()


def remove_block(text, site):
    while True:
        idx = text.find(site)
        if idx == -1:
            return text
        b = text.find("{", idx)
        if b == -1:
            return text
        depth = 0
        i = b
        while i < len(text):
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
                if depth == 0:
                    text = text[:idx] + text[i + 1:]
                    break
            i += 1
        else:
            return text  # unbalanced; bail without corrupting


src = remove_block(src, SITE)
src = src.rstrip() + "\n\n" + NEW_BLOCK
open(CADDYFILE, "w").write(src)
print("Caddyfile updated for", SITE)
