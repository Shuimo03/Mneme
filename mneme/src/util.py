import datetime
from pathlib import Path

def _get_date_path(self, date: datetime | None = None) -> Path:
    """生成日期路径，如 /data/2025-01-18/"""
    d = date or datetime.now()
    return self.base_dir / d.strftime(self.date_format)


def get_source_path(self, source: str, date_path: Path) -> Path:
    """生成来源路径，如 /data/2025-01-18/meta/"""
    return date_path / source