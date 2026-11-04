"""The news banner on the home page, from CHANGELOG.md.

    python news.py ../CHANGELOG.md 5.7.1-3-gabc1234 > data/news.json

For version x.y.z (the latest tag, as `git describe --tags` gives it) it takes the highlights of
x.y.0: the quote (lines starting with "> ") right below its heading in the changelog,

    ## 5.7.0 (2026-11-05)

    > Trees: a tree that the server fills and drives, ...

and writes {"version": "5.7", "text": "Trees: ..."} for layouts/index.html. So the banner
announces the latest x.y release, and stays during its x.y.z bug-fix releases.

A tag x.y.0 without highlights fails the build: every x.y release gets a banner. Anything else
(no tag, an older release without highlights) gives {}: no banner.
"""

import json
import re
import sys


def highlights(changelog, version):
    """The highlight text of release x.y.0 of this version, or None."""
    m = re.match(r"v?(\d+)\.(\d+)\.(\d+)", version)
    if not m:
        return None
    heading = re.compile(rf"^## v?{m[1]}\.{m[2]}\.0\b")
    lines = changelog.splitlines()
    for i, line in enumerate(lines):
        if heading.match(line):
            quote = []
            for each in lines[i + 1 :]:
                if each.startswith(">"):
                    quote.append(each[1:].strip())
                elif each.strip() or quote:
                    break
            return " ".join(quote) or None
    return None


def news(changelog, version):
    m = re.match(r"v?(\d+)\.(\d+)\.(\d+)(.*)", version)
    if not m:
        return {}
    text = highlights(changelog, version)
    if text is None:
        if m[3] == "0" and not m[4]:
            raise SystemExit(
                f"CHANGELOG.md: release {version} has no highlights; put them in a quote"
                f" ('> ...') right below its heading, for the banner on the website"
            )
        return {}
    return {"version": f"{m[1]}.{m[2]}", "text": text}


if __name__ == "__main__":
    path, version = sys.argv[1:3]
    with open(path, encoding="utf-8") as f:
        print(json.dumps(news(f.read(), version), ensure_ascii=False))
