# backend/app/env_detect.py
from importlib import metadata
import json, os

def detect_python_packages():
    pkgs = []
    for dist in metadata.distributions():
        try:
            name = dist.metadata['Name'] or dist.metadata['Summary']
        except Exception:
            name = dist.metadata.get('Name', dist.metadata.get('Summary', 'unknown'))
        version = dist.version
        if name:
            pkgs.append({"name": name.lower(), "version": version})
    # de-dup by name
    seen, uniq = set(), []
    for p in pkgs:
        if p["name"] not in seen:
            seen.add(p["name"])
            uniq.append(p)
    return uniq

def detect_node_packages(project_root):
    pkg = os.path.join(project_root, "package.json")
    if not os.path.exists(pkg):
        return []
    data = json.load(open(pkg, "r", encoding="utf-8"))
    versions = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
    return [{"name": k, "version": v.lstrip("^~")} for k, v in versions.items()]

