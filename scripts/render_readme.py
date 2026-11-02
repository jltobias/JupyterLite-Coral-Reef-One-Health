"""Generate the public README without requiring any build dependencies."""

import argparse
import json
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]


def settings():
    return json.loads((ROOT / "site.json").read_text(encoding="utf-8"))


def publication_url(config):
    return config.get(
        "pages_url",
        f"https://{config['owner']}.github.io/{config['repository']}",
    ).rstrip("/")


def render():
    config = settings()
    base = publication_url(config)
    replacements = {
        "__SITE_URL__": base + "/",
        "__BOOK_URL__": base + "/book/",
        "__LAB_URL__": base + "/lite/lab/index.html",
        "__NOTEBOOK_URL__": base + "/lite/lab/index.html?path=" + quote("01-reef-mapping.ipynb"),
        "__REPO_URL__": f"https://github.com/{config['owner']}/{config['repository']}",
    }
    result = (ROOT / "templates/README.md").read_text(encoding="utf-8")
    for key, value in replacements.items():
        result = result.replace(key, value)
    return result.rstrip() + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Fail if README.md needs regeneration")
    args = parser.parse_args()
    target = ROOT / "README.md"
    result = render()
    if args.check:
        if not target.exists() or target.read_text(encoding="utf-8") != result:
            raise SystemExit("README.md is stale; run python scripts/render_readme.py")
        print("README.md is current")
    else:
        target.write_text(result, encoding="utf-8", newline="\n")
        print("Generated README.md")


if __name__ == "__main__":
    main()
