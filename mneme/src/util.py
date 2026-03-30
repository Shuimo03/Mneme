from datetime import datetime
from pathlib import Path


def get_date_path(base_dir: Path, date_format: str, date: datetime | None = None) -> Path:
    """生成日期路径，如 /data/2025-01-18/。"""
    selected_date = date or datetime.now()
    return base_dir / selected_date.strftime(date_format)


def get_source_path(source: str, date_path: Path) -> Path:
    """生成来源路径，如 /data/2025-01-18/meta/。"""
    return date_path / source
