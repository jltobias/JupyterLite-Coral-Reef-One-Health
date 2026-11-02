"""Validate and execute the actual learning notebooks against their bundled data."""

from pathlib import Path

import nbformat
from nbclient import NotebookClient

ROOT = Path(__file__).resolve().parents[1]


def main():
    notebooks = sorted((ROOT / "content").glob("*.ipynb"))
    if not notebooks:
        raise SystemExit("No notebooks found")
    output = ROOT / "_build" / "executed"
    output.mkdir(parents=True, exist_ok=True)
    identifiers = set()
    for path in notebooks:
        notebook = nbformat.read(path, as_version=4)
        nbformat.validate(notebook)
        for cell in notebook.cells:
            if cell.id in identifiers:
                raise SystemExit(f"Duplicate Book cell identifier: {cell.id}")
            identifiers.add(cell.id)
        client = NotebookClient(
            notebook,
            timeout=90,
            kernel_name="python3",
            resources={"metadata": {"path": str(path.parent)}},
        )
        client.execute()
        # Preserve executed copies for inspection without dirtying source notebooks.
        nbformat.write(notebook, output / path.name)
        print(f"Executed {path.name}")


if __name__ == "__main__":
    main()
