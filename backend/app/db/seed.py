"""
Idempotent database seeding.

Run AFTER `alembic upgrade head` (the migration creates the tables; this
inserts the default admin user, categories and cases). Safe to run repeatedly –
existing rows are left untouched.

Usage:
    python -m app.db.seed

The default admin password can be overridden with the DEFAULT_ADMIN_PASSWORD
environment variable (defaults to "admin123").
"""
from __future__ import annotations

import csv
import os
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models import Case, Category, User

SEED_DIR = Path(__file__).resolve().parent / "seed_data"
DEFAULT_ADMIN_USERNAME = "admin"


def _seed_admin(db: Session) -> bool:
    """Create the default admin user if it does not already exist."""
    if db.query(User).filter(User.username == DEFAULT_ADMIN_USERNAME).first():
        return False
    password = os.getenv("DEFAULT_ADMIN_PASSWORD", "admin123")
    db.add(
        User(
            username=DEFAULT_ADMIN_USERNAME,
            password_hash=hash_password(password),
            role="admin",
            is_active=True,
        )
    )
    return True


def _seed_categories(db: Session) -> int:
    """Upsert categories from seed_data/categories.csv (keyed by name)."""
    created = 0
    with (SEED_DIR / "categories.csv").open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            name = row["name"].strip()
            if db.query(Category).filter(Category.name == name).first():
                continue
            db.add(
                Category(
                    name=name,
                    description=(row.get("description") or "").strip() or None,
                    sort_order=int(row.get("sort_order") or 0),
                )
            )
            created += 1
    db.flush()  # ensure category ids are available for case FK lookups
    return created


def _seed_cases(db: Session) -> int:
    """Upsert cases from seed_data/cases.csv (keyed by name + category)."""
    created = 0
    categories = {c.name: c.id for c in db.query(Category).all()}
    with (SEED_DIR / "cases.csv").open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            cat_name = row["category_name"].strip()
            category_id = categories.get(cat_name)
            if category_id is None:
                print(f"  [skip] case '{row['name']}': unknown category '{cat_name}'")
                continue
            name = row["name"].strip()
            exists = (
                db.query(Case)
                .filter(Case.name == name, Case.category_id == category_id)
                .first()
            )
            if exists:
                continue
            is_enabled = (row.get("is_enabled") or "t").strip().lower() in ("t", "true", "1")
            db.add(
                Case(
                    name=name,
                    category_id=category_id,
                    risk_level=(row.get("risk_level") or "medium").strip(),
                    description=(row.get("description") or "").strip() or None,
                    fix_suggestion=(row.get("fix_suggestion") or "").strip() or None,
                    script_path=(row.get("script_path") or "").strip(),
                    is_enabled=is_enabled,
                )
            )
            created += 1
    return created


def seed() -> None:
    db = SessionLocal()
    try:
        admin_created = _seed_admin(db)
        cats = _seed_categories(db)
        cases = _seed_cases(db)
        db.commit()
        print(
            "Seed complete: "
            f"admin {'created' if admin_created else 'exists'}, "
            f"+{cats} categories, +{cases} cases."
        )
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
