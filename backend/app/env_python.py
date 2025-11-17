from __future__ import annotations
from pathlib import Path
from typing import List, Dict, Optional
import json, subprocess, sys, os

# ----- run a small metadata script in a chosen interpreter -----
_METADATA_SCRIPT = r"""
import json
try:
    from importlib import metadata
except Exception:  # py<3.8
    import importlib_metadata as metadata  # type: ignore
out = []
seen = set()
for dist in metadata.distributions():
    name = (dist.metadata.get('Name') or '').lower()
    version = getattr(dist, 'version', None)
    if name and version and name not in seen:
        seen.add(name)
        out.append({'name': name, 'version': version})
print(json.dumps(out))
"""

def get_installed_with_interpreter(python_path: str, timeout: int = 10) -> List[Dict[str, str]]:
    try:
        proc = subprocess.run(
            [python_path, "-c", _METADATA_SCRIPT],
            capture_output=True, text=True, timeout=timeout
        )
        if proc.returncode == 0 and proc.stdout.strip():
            return json.loads(proc.stdout)
    except Exception:
        pass
    return []

# ----- try to guess an interpreter under a folder (.venv, venv) -----
def guess_python_interpreters(workdir: Path) -> List[str]:
    candidates = []
    # windows vs posix
    names = [
        workdir / ".venv" / "Scripts" / "python.exe",
        workdir / "venv" / "Scripts" / "python.exe",
        workdir / ".venv" / "bin" / "python",
        workdir / "venv" / "bin" / "python",
    ]
    for p in names:
        if p.exists():
            candidates.append(str(p))
    return candidates

def env_python_packages(workdir: Optional[str] = None, python_path: Optional[str] = None) -> Dict:
    """
    Returns {'interpreter': <path>, 'packages': [...]}
    Priority:
      1) explicit python_path
      2) guessed .venv/venv under workdir
      3) current process interpreter
    """
    # 1) explicit
    if python_path:
        pkgs = get_installed_with_interpreter(python_path)
        if pkgs:
            return {"interpreter": python_path, "packages": pkgs}

    # 2) guess under workdir
    if workdir:
        for cand in guess_python_interpreters(Path(workdir)):
            pkgs = get_installed_with_interpreter(cand)
            if pkgs:
                return {"interpreter": cand, "packages": pkgs}

    # 3) fallback: backend’s own interpreter
    pkgs = get_installed_with_interpreter(sys.executable)
    return {"interpreter": sys.executable, "packages": pkgs}
