"""Repository cloning and scanning utilities."""
from __future__ import annotations

import os
import shutil
import stat
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional, Set
from urllib.parse import quote, urlparse

from git import GitCommandError, Repo

from .utils import build_snippet, get_clone_root, get_github_token

_SUPPORTED_EXTENSIONS = {".py", ".js", ".jsx", ".ts", ".tsx", ".java"}


@dataclass(slots=True)
class ScannedFile:
    """Lightweight representation of a scanned code file."""

    path: str
    language: str
    snippet: str


def clone_repository(repo_url: str, branch: str | None = None) -> Path:
    """Clone the repository into a temporary directory and return its path.

    Supports optional branch checkout, injects PAT credentials when available, and
    falls back to unauthenticated cloning if the token fails. Temporary directories
    are cleaned up to avoid Windows permission issues with Git pack files.
    """
    # Feature 2 story — Resilient cloning with PAT injection and branch support.
    if shutil.which("git") is None:
        raise RuntimeError("Git executable not found on PATH. Install Git to enable repository cloning.")

    clone_root = get_clone_root()
    repo_slug = _build_repo_slug(repo_url, branch)
    target_path = clone_root / repo_slug

    _safe_rmtree(target_path)

    auth_url = _maybe_inject_token(repo_url)
    kwargs = {}
    if branch:
        kwargs["branch"] = branch

    try:
        Repo.clone_from(auth_url, target_path, **kwargs)
    except GitCommandError as exc:
        if auth_url != repo_url:
            _safe_rmtree(target_path)
            try:
                Repo.clone_from(repo_url, target_path, **kwargs)
            except GitCommandError as fallback_exc:
                raise RuntimeError(f"Failed to clone repository: {fallback_exc}") from fallback_exc
        else:
            raise RuntimeError(f"Failed to clone repository: {exc}") from exc

    return target_path


def scan_repository(repo_path: Path, branches: Optional[Iterable[str]] = None) -> List[ScannedFile]:
    """Scan repository branches for supported source files and return snippet metadata."""
    repo = Repo(repo_path)
    try:
        repo.remotes.origin.fetch()
    except Exception:
        # Fetch failures should not block reading already-cloned data.
        pass

    original_ref = _get_current_branch(repo)

    target_branches = _normalise_branches(repo, branches)

    results: List[ScannedFile] = []
    seen: Set[str] = set()

    for branch_name in target_branches:
        _checkout_branch(repo, branch_name)
        for file_path in _iter_code_files(repo_path):
            try:
                content = file_path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue

            snippet = build_snippet(content)
            language = _guess_language(file_path)
            relative_path = file_path.relative_to(repo_path)
            keyed_path = f"{branch_name}:{relative_path}" if branch_name else str(relative_path)
            if keyed_path in seen:
                continue
            seen.add(keyed_path)
            results.append(ScannedFile(path=keyed_path, language=language, snippet=snippet))

    if original_ref:
        _checkout_branch(repo, original_ref)

    return results


def _iter_code_files(repo_path: Path) -> Iterable[Path]:
    for extension in _SUPPORTED_EXTENSIONS:
        yield from repo_path.rglob(f"*{extension}")


def _guess_language(file_path: Path) -> str:
    suffix = file_path.suffix.lower()
    mapping = {
        ".py": "python",
        ".js": "javascript",
        ".jsx": "javascript",
        ".ts": "typescript",
        ".tsx": "typescript",
        ".java": "java",
    }
    return mapping.get(suffix, "unknown")


def _build_repo_slug(repo_url: str, branch: str | None) -> str:
    parsed = urlparse(repo_url)
    slug = parsed.path.strip("/").replace(".git", "")
    slug = slug.replace("/", "_") or "repository"
    if branch:
        slug = f"{slug}_{branch}"
    return slug


def _maybe_inject_token(repo_url: str) -> str:
    token = get_github_token()
    if not token:
        return repo_url

    parsed = urlparse(repo_url)
    if parsed.scheme not in {"http", "https"}:
        return repo_url

    netloc = parsed.netloc
    if "@" in netloc:
        return repo_url

    safe_token = quote(token, safe="")
    safe_netloc = f"{safe_token}:x-oauth-basic@{netloc}"
    return parsed._replace(netloc=safe_netloc).geturl()


def _safe_rmtree(path: Path) -> None:
    # Feature 2 story — Clean temp folders even when Windows leaves pack files read-only.
    if not path.exists():
        return

    def _onerror(func, value, exc_info):
        try:
            os.chmod(value, stat.S_IWRITE)
        except OSError:
            pass
        func(value)

    shutil.rmtree(path, onerror=_onerror)


def _get_current_branch(repo: Repo) -> Optional[str]:
    try:
        if repo.head.is_detached:
            return None
        return repo.active_branch.name
    except (TypeError, ValueError):
        return None


def _normalise_branches(repo: Repo, branches: Optional[Iterable[str]]) -> List[str]:
    if branches is not None:
        return [branch for branch in branches]

    remote_refs = repo.remotes.origin.refs if repo.remotes else []
    branch_names = []
    for ref in remote_refs:
        if ref.name.endswith("/HEAD"):
            continue
        branch_names.append(ref.remote_head)

    if not branch_names and repo.heads:
        branch_names = [head.name for head in repo.heads]

    if not branch_names:
        current = _get_current_branch(repo)
        return [current] if current else []

    return sorted(set(branch_names))


def _checkout_branch(repo: Repo, branch: Optional[str]) -> None:
    if branch is None:
        return

    if branch in repo.heads:
        repo.git.checkout(branch)
        return

    origin_ref = f"origin/{branch}"
    if origin_ref in repo.refs:
        repo.git.checkout("-B", branch, origin_ref)
        return

    raise RuntimeError(f"Branch '{branch}' not found in repository")
