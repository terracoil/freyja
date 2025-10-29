# 📦 Git Submodules in Freyja

## 📍 Navigation
**You are here**: Development > Git Submodules

**Parents**:
- [🏠 Main README](../../README.md) - Project overview and quick start
- [📚 Documentation Hub](../README.md) - Complete documentation index
- [🔧 Development](README.md) - Development guides

**Related**:
- [🛡️ Features > Guards](../features/guards.md) - Guard clause usage and API
- [🤝 Contributing](contributing.md) - Contribution guidelines

---

## 📑 Table of Contents
- [🔍 Overview](#-overview)
- [🏁 Initial Setup](#-initial-setup)
- [✅ Verifying Submodule Status](#-verifying-submodule-status)
- [⚙️ Common Operations](#️-common-operations)
- [🔧 Troubleshooting](#-troubleshooting)
- [🤖 CI/CD Integration](#-cicd-integration)
- [💼 Development Workflow](#-development-workflow)
- [🔒 Namespace Isolation](#-namespace-isolation)
- [🤔 Why Git Submodules?](#-why-git-submodules)
- [📖 References](#-references)
- [📝 Quick Reference](#-quick-reference)

---

## 🔍 Overview

> **📦 Standalone modgud v2.1.1**: While Freyja includes modgud v2.1.1 as a git submodule, you can also use modgud independently in your own projects. Install from PyPI: `pip install modgud`. Visit [modgud on PyPI](https://pypi.org/project/modgud/) for more information.

The `modgud` library (v2.1.1) is included as a git submodule at:
```
freyja/utils/modgud/
```

This allows Freyja to:
- Maintain zero pip dependencies
- Control the exact version of modgud used
- Prevent conflicts with user's standalone modgud installations
- Update modgud independently of Freyja releases

## 🏁 Initial Setup

When cloning Freyja for the first time, you **must** initialize the submodules:

```bash
# Clone the repository
git clone https://github.com/terracoil/freyja.git
cd freyja

# Initialize and fetch submodules
git submodule update --init --recursive
```

**Alternative:** Clone with submodules in one step:
```bash
git clone --recurse-submodules https://github.com/terracoil/freyja.git
```

## ✅ Verifying Submodule Status

Check if submodules are properly initialized:

```bash
# Show submodule status
git submodule status

# Expected output:
# <commit-hash> freyja/utils/modgud (v2.1.1)
```

If the line starts with `-` (dash), the submodule is not initialized:
```bash
# Not initialized (bad):
-<commit-hash> freyja/utils/modgud

# Initialized (good):
 <commit-hash> freyja/utils/modgud (v2.1.1)
```

## ⚙️ Common Operations

### Update Submodule to Latest Version

Use the `bin/update-modgud` script to update the submodule and clean development files:

```bash
# Update to latest version on master branch and clean
bin/update-modgud

# Update to specific tag
bin/update-modgud --tag v2.1.1

# Update to specific branch
bin/update-modgud --branch develop

# Preview what would happen without making changes
bin/update-modgud --dry-run

# Update without cleaning (keep development files)
bin/update-modgud --no-clean
```

**What it does:**
1. Fetches latest changes from the modgud repository
2. Checks out the specified branch or tag (default: master)
3. Updates the parent repository's submodule reference
4. Removes development files (tests, docs, build configs, etc.) unless `--no-clean` is specified

**Manual alternative:**

```bash
# Navigate to submodule directory
cd freyja/utils/modgud

# Fetch latest changes
git fetch

# Checkout desired version (e.g., v2.1.1 tag)
git checkout v2.1.1

# Return to Freyja root
cd ../../..

# Update parent repo reference and commit
git add freyja/utils/modgud
git commit -m "Update modgud to v2.1.1"

# Clean development cruft (IMPORTANT for publishing)
bin/update-modgud --no-clean  # Skip update, just clean
```

### Development Files Cleaned

The update script automatically removes development files that aren't needed for runtime:

**Removed:**
- Development directories: tests, docs, bin, tmp, dist, build
- Configuration files: *.toml, *.md, .gitignore, etc.
- Cache directories: .venv, .pytest_cache, .mypy_cache, __pycache__

**Preserved:**
- The `modgud/` package directory (essential)
- LICENSE file
- Git submodule metadata (.git)

**When to clean:** After every `git checkout` or `git pull` in the submodule. The `bin/update-modgud` script does this automatically.

### Update All Submodules

```bash
# Update all submodules to their latest commits
git submodule update --remote --merge
```

### Reset Submodule to Tracked Version

If your submodule is out of sync:

```bash
# Reset submodule to the commit tracked by Freyja
git submodule update --init --recursive
```

## 🔧 Troubleshooting

### Empty Submodule Directory

**Problem:** `freyja/utils/modgud/` directory exists but is empty.

**Solution:**
```bash
git submodule update --init --recursive
```

### Import Errors

**Problem:** `ImportError: cannot import name 'guarded' from 'freyja.utils.guards'`

**Cause:** Submodule not initialized.

**Solution:**
```bash
# Initialize submodules
git submodule update --init --recursive

# Verify modgud is present
ls -la freyja/utils/modgud/modgud/
```

### Detached HEAD in Submodule

**Problem:** Submodule is in "detached HEAD" state.

**Explanation:** This is normal! Submodules point to specific commits, not branches.

**To check current version:**
```bash
cd freyja/utils/modgud
git describe --tags
```

### Updating After Pull

After pulling Freyja changes that update the submodule:

```bash
# Pull latest Freyja changes
git pull

# Update submodules to match
git submodule update --init --recursive
```

## 🤖 CI/CD Integration

### GitHub Actions

```yaml
- name: Checkout code
  uses: actions/checkout@v3
  with:
    submodules: recursive  # Automatically fetch submodules

- name: Set up Python
  uses: actions/setup-python@v4
  with:
    python-version: '3.13'

- name: Install dependencies
  run: |
    pip install poetry
    poetry install
```

### Manual CI Setup

```bash
#!/bin/bash
# ci-setup.sh

# Clone with submodules
git clone --recurse-submodules https://github.com/terracoil/freyja.git

# Or if already cloned:
cd freyja
git submodule update --init --recursive

# Install dependencies
poetry install
```

## 💼 Development Workflow

### Making Changes to Modgud

**NOT RECOMMENDED** - Modgud changes should be made in the upstream modgud repository.

If you need to test modgud changes:

```bash
# 1. Make changes in separate modgud clone
cd /path/to/separate/modgud
# ... make changes ...
git commit -m "Fix: ..."
git push

# 2. Update Freyja's submodule reference
cd /path/to/freyja
cd freyja/utils/modgud
git pull origin main
cd ../../..
git add freyja/utils/modgud
git commit -m "Update modgud with latest fixes"
```

### Reviewing Submodule Changes

```bash
# See what version of modgud is currently used
git submodule status

# See if submodule has uncommitted changes
cd freyja/utils/modgud
git status

# View submodule commit history
git log --oneline
```

## 🔒 Namespace Isolation

Freyja's import wrapper (`freyja/utils/guards.py`) provides namespace isolation:

```python
# In freyja/utils/guards.py
from freyja.utils.modgud.modgud import guarded_expression, not_none, ...

# Alias for Freyja usage
guarded = guarded_expression

# Re-export
__all__ = ['guarded', 'not_none', ...]
```

**Benefits:**
- Users always import from `freyja.utils.guards`
- No conflicts if user has standalone `modgud` installed
- Freyja controls exactly which modgud version is used

## 🤔 Why Git Submodules?

**Alternatives Considered:**

1. **Pip Dependency** ❌
   - Breaks zero-dependency goal
   - Version conflicts with user's modgud
   - Harder to control exact version

2. **Copy Source Files** ❌
   - Hard to track updates
   - No version history
   - Difficult to upstream fixes

3. **Git Submodule** ✅
   - Maintains zero pip dependencies
   - Full version control
   - Easy to update
   - Tracks exact commit/version
   - Upstream contributions possible

## 📖 References

- [Git Submodules Documentation](https://git-scm.com/book/en/v2/Git-Tools-Submodules)
- [modgud Repository](https://github.com/user/modgud)
- [Freyja Guards Documentation](../features/guards.md)

## 📝 Quick Reference

```bash
# Initialize submodules (first time)
git submodule update --init --recursive

# Update submodules after pull
git submodule update --init --recursive

# Check submodule status
git submodule status

# Update modgud to latest and clean
bin/update-modgud

# Update to specific version
bin/update-modgud --tag v2.1.1

# Preview changes without applying
bin/update-modgud --dry-run

# Update without cleaning
bin/update-modgud --no-clean
```
