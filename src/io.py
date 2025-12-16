from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

import pandas as pd
import yaml

# Racine du projet (…/artist-compass/)
ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"


def _ensure_data_dir() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)


# ---------- YAML ----------
def load_yaml(filename: str, default: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    _ensure_data_dir()
    path = DATA_DIR / filename
    if not path.exists():
        return default or {}
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def save_yaml(filename: str, data: Dict[str, Any]) -> None:
    _ensure_data_dir()
    path = DATA_DIR / filename
    with path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, allow_unicode=True, sort_keys=False)


# ---------- JSON ----------
def load_json(filename: str, default: Optional[Any] = None) -> Any:
    _ensure_data_dir()
    path = DATA_DIR / filename
    if not path.exists():
        return default if default is not None else []
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_json(filename: str, data: Any) -> None:
    _ensure_data_dir()
    path = DATA_DIR / filename
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ---------- CSV (journal) ----------
def load_csv(filename: str, default_columns: Optional[list[str]] = None) -> pd.DataFrame:
    _ensure_data_dir()
    path = DATA_DIR / filename
    if not path.exists():
        return pd.DataFrame(columns=default_columns or [])
    return pd.read_csv(path)


def save_csv(filename: str, df: pd.DataFrame) -> None:
    _ensure_data_dir()
    path = DATA_DIR / filename
    df.to_csv(path, index=False)


def append_row_csv(filename: str, row: Dict[str, Any], default_columns: Optional[list[str]] = None) -> pd.DataFrame:
    """
    Ajoute une ligne dans un CSV et renvoie le DataFrame à jour.
    ⚠️ Sur Streamlit Cloud, l'écriture disque peut ne pas être persistante sur le long terme.
    """
    df = load_csv(filename, default_columns=default_columns)
    # Assure que toutes les colonnes existent
    for k in row.keys():
        if k not in df.columns:
            df[k] = None
    df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    save_csv(filename, df)
    return df
