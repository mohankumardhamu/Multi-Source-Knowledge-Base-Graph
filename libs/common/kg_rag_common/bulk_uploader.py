from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

import requests


@dataclass
class UploadResult:
    path: Path
    ok: bool
    status_code: int
    response: Any
    error: Optional[str] = None


class BulkDocumentUploader:
    """Lightweight client for bulk uploading documents to the API.

    Keeps functionality isolated so the rest of the system remains untouched.
    """

    def __init__(self, base_url: str, timeout: float = 60.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._session = requests.Session()

    def upload_file(self, file_path: Path, title: Optional[str] = None, domain: Optional[str] = None, extra_metadata: Optional[Dict[str, Any]] = None) -> UploadResult:
        url = f"{self.base_url}/v1/docs"
        title = title or file_path.stem
        data = {"title": title}
        if domain:
            data["domain"] = domain
        if extra_metadata:
            # flatten simple metadata keys if needed (server currently expects title/domain only)
            for k, v in extra_metadata.items():
                if k not in data and isinstance(v, (str, int, float)):
                    data[k] = str(v)

        try:
            with file_path.open("rb") as f:
                files = {"file": (file_path.name, f, "application/pdf")}
                resp = self._session.post(url, data=data, files=files, timeout=self.timeout)
            ok = 200 <= resp.status_code < 300
            payload: Any
            try:
                payload = resp.json()
            except Exception:
                payload = resp.text
            return UploadResult(path=file_path, ok=ok, status_code=resp.status_code, response=payload, error=None if ok else str(payload))
        except Exception as e:
            return UploadResult(path=file_path, ok=False, status_code=0, response=None, error=str(e))

    def upload_folder(self, folder: str | Path, pattern: str = "*.pdf", recursive: bool = True, domain: Optional[str] = None) -> List[UploadResult]:
        """Upload all files matching pattern under folder.

        - folder: base directory to search
        - pattern: glob-style pattern (e.g., "*.pdf")
        - recursive: search subdirectories when True
        - domain: optional domain to attach to each upload
        """
        base = Path(folder)
        if not base.exists() or not base.is_dir():
            return [UploadResult(path=base, ok=False, status_code=0, response=None, error="Folder not found or not a directory")]  # type: ignore[arg-type]

        paths: Iterable[Path]
        if recursive:
            paths = base.rglob(pattern)
        else:
            paths = base.glob(pattern)

        results: List[UploadResult] = []
        for p in paths:
            if not p.is_file():
                continue
            results.append(self.upload_file(p, title=p.stem, domain=domain))
        return results

