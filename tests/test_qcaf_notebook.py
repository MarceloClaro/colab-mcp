import json

import pytest

from colab_mcp.qcaf_notebook import (
    QCAFNotebookMaterializeRequest,
    materialize_qcaf_notebook,
)


def notebook_json():
    return json.dumps(
        {
            "cells": [
                {
                    "cell_type": "markdown",
                    "metadata": {},
                    "source": ["# QCAF\n"],
                }
            ],
            "metadata": {"colab": {"name": "qcaf.ipynb"}},
            "nbformat": 4,
            "nbformat_minor": 5,
        }
    )


def test_materialize_notebook(tmp_path):
    result = materialize_qcaf_notebook(
        QCAFNotebookMaterializeRequest(
            notebook_json=notebook_json(),
            filename="qcaf.ipynb",
            output_dir=str(tmp_path),
        )
    )

    path = tmp_path / "qcaf.ipynb"
    assert path.exists()
    assert result.path == str(path.resolve())
    assert len(result.sha256) == 64
    assert result.cell_count == 1


def test_refuses_overwrite_by_default(tmp_path):
    path = tmp_path / "qcaf.ipynb"
    path.write_text("existing", encoding="utf-8")

    with pytest.raises(FileExistsError):
        materialize_qcaf_notebook(
            QCAFNotebookMaterializeRequest(
                notebook_json=notebook_json(),
                filename="qcaf.ipynb",
                output_dir=str(tmp_path),
            )
        )


def test_rejects_path_in_filename(tmp_path):
    with pytest.raises(ValueError, match="basename"):
        materialize_qcaf_notebook(
            QCAFNotebookMaterializeRequest(
                notebook_json=notebook_json(),
                filename="../qcaf.ipynb",
                output_dir=str(tmp_path),
            )
        )


def test_rejects_invalid_nbformat(tmp_path):
    bad = json.loads(notebook_json())
    bad["nbformat"] = 3

    with pytest.raises(ValueError, match="nbformat 4"):
        materialize_qcaf_notebook(
            QCAFNotebookMaterializeRequest(
                notebook_json=json.dumps(bad),
                filename="qcaf.ipynb",
                output_dir=str(tmp_path),
            )
        )
