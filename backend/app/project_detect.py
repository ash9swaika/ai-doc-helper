from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import json

# --------- Sentinels we look for ----------
PY_SENTINELS = [
    "pyproject.toml", "poetry.lock", "requirements.txt", "Pipfile", "Pipfile.lock",
    "environment.yml", "setup.py", "setup.cfg"
]
NODE_SENTINELS = [
    "package.json", "yarn.lock", "pnpm-lock.yaml", "package-lock.json", "tsconfig.json"
]

# --------- Utility: score presence of sentinel files ----------
def score_sentinels(root: Path, sentinels: List[str]) -> Tuple[float, List[str]]:
    hits = []
    score = 0.0
    for f in sentinels:
        p = root / f
        if p.exists():
            hits.append(f)
            # weight canonical manifests slightly higher for *detection* confidence
            if f in ("pyproject.toml", "package.json"):
                score += 2.0
            else:
                score += 1.0
    return score, hits

# --------- Package lists ----------
def detect_python_packages_installed() -> List[Dict[str, str]]:
    # Reads the interpreter's environment where the backend runs
    try:
        from importlib import metadata
    except Exception:
        return []
    pkgs = []
    seen = set()
    for dist in metadata.distributions():
        name = (dist.metadata.get('Name') or '').lower()
        version = getattr(dist, "version", None)
        if name and version and name not in seen:
            seen.add(name)
            pkgs.append({"name": name, "version": version})
    return pkgs

def read_node_deps_declared(root: Path) -> List[Dict[str, str]]:
    pkg = root / "package.json"
    if not pkg.exists():
        return []
    try:
        data = json.loads(pkg.read_text(encoding="utf-8"))
        versions = {}
        for k, v in (data.get("dependencies") or {}).items():
            versions[k] = v
        for k, v in (data.get("devDependencies") or {}).items():
            versions[k] = v
        out = []
        for k, v in versions.items():
            vv = str(v).lstrip("^~")
            out.append({"name": k, "version": vv})
        return out
    except Exception:
        return []

# --------- Data shapes ----------
@dataclass
class EcosystemBlock:
    name: str                       # "python" or "node"
    score: float                    # detection confidence
    files: List[str]                # sentinel files found
    packages: List[Dict[str, str]]  # python: installed, node: declared

@dataclass
class FolderDetection:
    path: str
    ecosystems: List[EcosystemBlock]   # zero, one, or many

@dataclass
class MultiDetection:
    roots: List[FolderDetection]       # each scanned folder

# --------- Main detection ----------
def detect_multi(root: Path, scan_depth: int = 1) -> MultiDetection:
    """
    Scan the repo root and its first-level subfolders (depth=1) by default.
    No ecosystem preference; return all that are present in each folder.
    """
    folders = [root]
    if scan_depth >= 1:
        # add first-level subfolders (skip dot/venv/node_modules, etc.)
        for p in root.iterdir():
            if p.is_dir() and p.name not in {".git", ".venv", "node_modules", "__pycache__", ".vscode"}:
                folders.append(p)

    results: List[FolderDetection] = []
    # we compute python installed list *once* for the environment
    py_installed = detect_python_packages_installed()

    for f in folders:
        ecos: List[EcosystemBlock] = []

        py_score, py_hits = score_sentinels(f, PY_SENTINELS)
        if py_score > 0:
            # attach the global installed list (best we can do without executing in that folder's venv)
            ecos.append(EcosystemBlock(name="python", score=py_score, files=py_hits, packages=py_installed))

        node_score, node_hits = score_sentinels(f, NODE_SENTINELS)
        if node_score > 0:
            ecos.append(EcosystemBlock(name="node", score=node_score, files=node_hits, packages=read_node_deps_declared(f)))

        results.append(FolderDetection(path=str(f), ecosystems=ecos))

    return MultiDetection(roots=results)
