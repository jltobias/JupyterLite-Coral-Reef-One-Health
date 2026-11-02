"""Build a Jupyter Book and JupyterLite into one GitHub Pages artifact."""

import argparse
from html import escape
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from urllib.parse import urlsplit

from render_readme import publication_url, settings

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "_site"


def run(*args, env=None):
    subprocess.run(args, cwd=ROOT, env=env, check=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--local", action="store_true", help="Build for http://localhost:8000/")
    parser.add_argument("--base-path", help="Override the deployment prefix, e.g. /my-repository")
    args = parser.parse_args()
    config = settings()
    if args.local and args.base_path is not None:
        parser.error("Choose --local or --base-path")
    repository = os.environ.get("GITHUB_REPOSITORY")
    default_path = urlsplit(publication_url(config)).path
    if repository and "pages_url" not in config:
        name = repository.split("/", 1)[1]
        default_path = "" if name.endswith(".github.io") else f"/{name}"
    base_path = "" if args.local else (args.base_path if args.base_path is not None else default_path)
    base_path = "/" + base_path.strip("/") if base_path.strip("/") else ""
    env = dict(os.environ, BASE_URL=base_path + "/book")

    run(sys.executable, "scripts/render_readme.py", "--check")
    # This is the only directory this script removes; resolve and check it first.
    if OUTPUT.resolve() != ROOT / "_site" or OUTPUT.is_symlink():
        raise SystemExit("Refusing to replace an unexpected output directory")
    if OUTPUT.exists():
        shutil.rmtree(OUTPUT)
    OUTPUT.mkdir()
    run(sys.executable, "-m", "jupyter", "book", "build", "--html", "--strict", env=env)
    shutil.copytree(ROOT / "_build/html", OUTPUT / "book")
    # Reset all task records before unpacking a fresh output tree. The CLI's
    # --force flag does not reset records early enough in JupyterLite 0.8.7.
    run(sys.executable, "-m", "jupyter", "lite", "doit", "--", "forget", "--all")
    run(sys.executable, "-m", "jupyter", "lite", "build", "--contents", "content", "--output-dir", str(OUTPUT / "lite"))
    shutil.copytree(ROOT / "assets", OUTPUT / "assets")
    portal = (ROOT / "templates/index.html").read_text(encoding="utf-8")
    portal = portal.replace("__TITLE__", escape(config["title"]))
    portal = portal.replace("__DESCRIPTION__", escape(config["description"]))
    portal = portal.replace("__REPO_URL__", f"https://github.com/{config['owner']}/{config['repository']}")
    (OUTPUT / "index.html").write_text(portal, encoding="utf-8", newline="\n")
    (OUTPUT / ".nojekyll").touch()
    manifest = {"base_path": base_path, "book": "book/index.html", "lab": "lite/lab/index.html"}
    (OUTPUT / "build-info.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    run(sys.executable, "scripts/check_site.py")
    print(f"Built Book, Lab, and portal in {OUTPUT}")


if __name__ == "__main__":
    main()
