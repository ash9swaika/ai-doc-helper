# Contributing Guide – AI Doc Helper

Welcome! 🎉  
This document outlines how development, branching, and releases are managed in this repository.

---

## 🧩 Branch Structure

| Branch | Purpose |
|---------|----------|
| **`main`** | Production-ready branch (stable releases only). |
| **`develop`** | Integration branch for tested features. |
| **`feature/*`** | Temporary branches for individual features or fixes. |

---

## 🧠 Workflow Summary

### 1️⃣ Create a new feature branch

Start from the latest `develop` branch:
```bash
git checkout develop
git pull origin develop
git checkout -b feature/<short-description>
```

### 2️⃣ Make changes

Implement your code in the feature branch.

Keep commits small and descriptive.

Prefix	Use for
feat:	New features
fix:	Bug fixes
chore:	Maintenance or config changes
docs:	Documentation updates
refactor:	Code refactoring
style:	Formatting / lint-only changes
test:	Unit or integration tests

Example:
```bash
git commit -m "feat: connect VS Code webview to FastAPI backend"
```

### 3️⃣ Push your feature branch

```bash
git push -u origin feature/<short-description>
```

This creates a remote branch for your feature.


### 4️⃣ Merge into develop

When your feature is tested and stable:

```bash
git checkout develop
git pull origin develop
git merge --no-ff feature/<short-description> -m "merge: integrate <feature-name>"
git push origin develop
```

Optionally delete the local and remote feature branch:
```bash
git branch -d feature/<short-description>
git push origin --delete feature/<short-description>
```

### 5️⃣ Release a new version

When develop reaches a stable milestone:

```bash
git checkout main
git pull origin main
git merge --no-ff develop -m "release: vX.Y.Z - <summary>"
git push origin main
git tag -a vX.Y.Z -m "Release vX.Y.Z"
git push origin vX.Y.Z
```

## 🔐 Branch Protection

Recommended GitHub settings:

main: Require PR + 1 review before merging.

develop: Require PRs, no direct pushes.

feature/*: Direct push allowed (development only).

## 🧰 Local Development (quick start)

### Clone repo
```bash
git clone https://github.com/<your-username>/ai-doc-helper.git
cd ai-doc-helper
```

### Enter extension folder
```bash
cd extension
```

### Install and build
```bash
npm install
npm run compile
```

### Run VS Code extension
### Press F5 inside VS Code → "AI: Lookup Docs"

## 🧾 Notes

Ensure your commits and PR titles follow the Conventional Commit format.

Keep the develop branch clean and working at all times.

All development should flow:
feature → develop → main → release tag

Happy coding! 💻✨
