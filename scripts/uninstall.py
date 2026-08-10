#!/usr/bin/env python3
"""Safely remove manifest-owned cmize-skills files without removing skill directories."""

from __future__ import annotations

try:
    from .install import uninstall_main
except ImportError:  # Running directly as: python3 scripts/uninstall.py
    from install import uninstall_main


if __name__ == "__main__":
    raise SystemExit(uninstall_main())
