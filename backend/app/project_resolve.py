from __future__ import annotations
from typing import Dict, Any, List
from pathlib import Path

from app.project_detect import detect_multi
from app.env_python import env_python_packages

def resolve_all(root: Path, folder_python_paths: Dict[str, str] | None = None) -> Dict[str, Any]:
    """
    root: repo root
    folder_python_paths: optional map { folder_path: python_interpreter_path }
    """
    det = detect_multi(root, scan_depth=1)
    enriched = []
    for r in det.roots:
        ecos_out = []
        for e in r.ecosystems:
            block = {
                "name": e.name,
                "score": e.score,
                "files": e.files,
                "packages": e.packages  # node: declared, python: will be replaced below
            }
            if e.name == "python":
                # pick interpreter: explicit > guessed > backend
                py_path = None
                if folder_python_paths and r.path in folder_python_paths:
                    py_path = folder_python_paths[r.path]
                env_info = env_python_packages(workdir=r.path, python_path=py_path)
                block["interpreter"] = env_info["interpreter"]
                block["packages"] = env_info["packages"]  # installed for that interpreter
            ecos_out.append(block)
        enriched.append({"path": r.path, "ecosystems": ecos_out})
    return {"roots": enriched}
