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
