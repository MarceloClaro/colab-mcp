from __future__ import annotations

import hashlib
import json
from pathlib import Path

from pydantic import BaseModel, Field


class QCAFNotebookMaterializeRequest(BaseModel):
    notebook_json: str = Field(min_length=2)
    filename: str = Field(default="qcaf_experiment.ipynb", min_length=1)
    output_dir: str = "."
    overwrite: bool = False


class QCAFNotebookMaterializeResult(BaseModel):
    path: str
    sha256: str
    size_bytes: int
    nbformat: int
    cell_count: int


def _validate_filename(filename: str) -> str:
    candidate = Path(filename)
    if candidate.name != filename:
        raise ValueError("filename must be a basename, not a path")
    if candidate.suffix.lower() != ".ipynb":
        raise ValueError("filename must end with .ipynb")
    return filename


def materialize_qcaf_notebook(
    request: QCAFNotebookMaterializeRequest,
) -> QCAFNotebookMaterializeResult:
    """Validate and persist a generated QCAF/Jupyter notebook."""

    filename = _validate_filename(request.filename)

    try:
        notebook = json.loads(request.notebook_json)
    except json.JSONDecodeError as exc:
        raise ValueError(f"notebook_json is not valid JSON: {exc}") from exc

    if not isinstance(notebook, dict):
        raise ValueError("notebook_json must contain a JSON object")
    if notebook.get("nbformat") != 4:
        raise ValueError("only Jupyter nbformat 4 notebooks are supported")
    cells = notebook.get("cells")
    if not isinstance(cells, list):
        raise ValueError("notebook_json must contain a cells list")

    output_dir = Path(request.output_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / filename

    if output_path.exists() and not request.overwrite:
        raise FileExistsError(
            f"{output_path} already exists; set overwrite=true to replace it"
        )

    canonical = json.dumps(
        notebook,
        indent=2,
        ensure_ascii=False,
        sort_keys=False,
    ) + "\n"
    payload = canonical.encode("utf-8")
    output_path.write_bytes(payload)

    return QCAFNotebookMaterializeResult(
        path=str(output_path),
        sha256=hashlib.sha256(payload).hexdigest(),
        size_bytes=len(payload),
        nbformat=4,
        cell_count=len(cells),
    )
