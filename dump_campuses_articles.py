#!/usr/bin/env python
"""Dump campuses and articles app data to a single JSON file (UTF-8). Fixes Windows encoding errors."""
import os
import sys

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")

import django
django.setup()

from django.core.management import call_command

if __name__ == "__main__":
    out_path = os.path.join(os.path.dirname(__file__), "campuses_and_articles_dump.json")
    with open(out_path, "w", encoding="utf-8") as f:
        call_command("dumpdata", "campuses", "articles", "--indent", "2", stdout=f)
    print(f"Dumped to {out_path}")
