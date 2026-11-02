"""Check publication entry points and local HTML links in the finished artifact."""

from html.parser import HTMLParser
import json
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1] / "_site"


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.urls = []

    def handle_starttag(self, tag, attrs):
        for name, value in attrs:
            if value and ((name == "href" and tag in {"a", "link"}) or (name == "src" and tag in {"img", "script", "iframe", "source"})):
                self.urls.append(value)


def main():
    info = json.loads((ROOT / "build-info.json").read_text(encoding="utf-8"))
    for path in ["index.html", info["book"], info["lab"], "assets/reef-splash.png", ".nojekyll"]:
        if not (ROOT / path).is_file():
            raise SystemExit(f"Missing publication file: {path}")
    lite_config = json.loads((ROOT / "lite/jupyter-lite.json").read_text(encoding="utf-8"))["jupyter-config-data"]
    source_config = json.loads((ROOT.parent / "jupyter-lite.json").read_text(encoding="utf-8"))["jupyter-config-data"]
    if lite_config.get("appName") != source_config["appName"]:
        raise SystemExit("Lab configuration was not applied; reset the JupyterLite task database before rebuilding")
    if not any(extension["name"] == "@jupyterlite/pyodide-kernel-extension" for extension in lite_config.get("federated_extensions", [])):
        raise SystemExit("Lab is missing its Python kernel extension")
    for source in (ROOT.parent / "content").rglob("*"):
        if source.is_file() and ".ipynb_checkpoints" not in source.parts:
            target = ROOT / "lite/files" / source.relative_to(ROOT.parent / "content")
            if not target.is_file():
                raise SystemExit(f"Missing Lab content: {target}")

    errors = []
    count = 0
    prefix = info["base_path"]
    for page in ROOT.rglob("*.html"):
        parser = Links()
        parser.feed(page.read_text(encoding="utf-8"))
        for url in parser.urls:
            parsed = urlsplit(url)
            if parsed.scheme or parsed.netloc or not parsed.path:
                continue
            path = unquote(parsed.path)
            if path.startswith("/"):
                if prefix and not (path == prefix or path.startswith(prefix + "/")):
                    errors.append(f"{page.relative_to(ROOT)}: URL misses deployment prefix: {url}")
                    continue
                path = path[len(prefix):] if prefix else path
                target = ROOT / path.lstrip("/")
            else:
                target = page.parent / path
            target = target.resolve()
            count += 1
            if not target.is_relative_to(ROOT.resolve()):
                errors.append(f"{page.relative_to(ROOT)}: link escapes artifact: {url}")
            elif not target.is_file() and not (target / "index.html").is_file():
                errors.append(f"{page.relative_to(ROOT)}: missing link target: {url}")
    if errors:
        raise SystemExit("\n".join(errors))
    print(f"Verified publication entry points, bundled Lab content, and {count} local HTML links")


if __name__ == "__main__":
    main()
