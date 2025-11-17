from __future__ import annotations
from pathlib import Path
from typing import Dict, List, Tuple
from packaging.version import Version
from packaging.requirements import Requirement

# py311+: tomllib is stdlib. If on py310, use tomli.
try:
    import tomllib as toml  # type: ignore
except Exception:
    import tomli as toml  # type: ignore

# ---- parse declared requirements (requirements.txt / pyproject.toml) ----
def _parse_requirements_txt(path: Path) -> Dict[str, str]:  # name -> spec (PEP 440)
    reqs: Dict[str, str] = {}
    if not path.exists():
        return reqs
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        try:
            r = Requirement(line)
            name = r.name.lower()
            spec = str(r.specifier) if r.specifier else ""
            reqs[name] = spec
        except Exception:
            # ignore weird lines (editable URLs, etc.) for now
            pass
    return reqs

def _parse_pyproject(path: Path) -> Dict[str, str]:
    reqs: Dict[str, str] = {}
    if not path.exists():
        return reqs
    data = toml.loads(path.read_text(encoding="utf-8"))

    # PEP 621
    deps = (data.get("project") or {}).get("dependencies") or []
    for d in deps:
        try:
            r = Requirement(d)
            reqs[r.name.lower()] = str(r.specifier) if r.specifier else ""
        except Exception:
            pass

    # Optional Poetry section
    poetry = (data.get("tool") or {}).get("poetry") or {}
    pdeps = poetry.get("dependencies") or {}
    for name, spec in pdeps.items():
        if name.lower() == "python":
            continue
        try:
            # poetry allows dicts; normalize to string if needed
            s = spec.get("version") if isinstance(spec, dict) else str(spec)
            r = Requirement(f"{name}{'' if s in (None,'*') else s}")
            reqs[r.name.lower()] = str(r.specifier) if r.specifier else ""
        except Exception:
            pass
    return reqs

def discover_declared_requirements(workdir: Path) -> Dict[str, str]:
    reqs = {}
    reqs_txt = _parse_requirements_txt(workdir / "requirements.txt")
    pyproj = _parse_pyproject(workdir / "pyproject.toml")
    reqs.update(reqs_txt)
    reqs.update(pyproj)
    return reqs

# ---- compare declared vs installed ----
def diff_declared_installed(
    declared: Dict[str, str],
    installed: List[Dict[str, str]]
) -> Tuple[List[Dict], List[Dict]]:
    """
    Returns (missing, incompatible)
    missing = [{name, required}]
    incompatible = [{name, required, installed}]
    """
    inst_map = {p["name"].lower(): p["version"] for p in installed}
    missing: List[Dict] = []
    incompatible: List[Dict] = []

    for name, spec in declared.items():
        if name not in inst_map:
            missing.append({"name": name, "required": spec or "any"})
            continue
        if spec:
            try:
                r = Requirement(f"{name}{spec}")
                if not Version(inst_map[name]) in r.specifier:
                    incompatible.append({"name": name, "required": spec, "installed": inst_map[name]})
            except Exception:
                # if spec parse fails, skip strict check
                pass
    return missing, incompatible
