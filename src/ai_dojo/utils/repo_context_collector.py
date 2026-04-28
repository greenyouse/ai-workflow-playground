from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

# Define common binary/hidden directories and extensions to skip
SKIP_DIRS = {
    '.git', '.svn', '.hg', '.idea', '.vscode', 'node_modules', '__pycache__',
    'dist', 'build', 'venv', '.venv', 'env', '.env', 'target', '.pytest_cache'
}

SKIP_EXTENSIONS = {
    '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.ico', '.webp',
    '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
    '.zip', '.tar', '.gz', '.rar', '.7z',
    '.dll', '.so', '.dylib', '.exe', '.bin',
    '.class', '.pyc', '.pyo',
    '.lock', '.orig', '.bak'
}

STOP_WORDS = {
    'a', 'an', 'and', 'are', 'at', 'be', 'by', 'for', 'from', 'how', 'in',
    'into', 'is', 'it', 'of', 'on', 'or', 'that', 'the', 'this', 'to', 'use',
    'with', 'when', 'why'
}

ALLOWED_SHORT_KEYWORDS = {'ai', 'ui', 'ux'}


# This ranks files based on the path proximity and semantic matching on the text
# against the idea passed in. It's a rough pass for now. Replace with RAG later.
@dataclass
class RankedFile:
    path: str
    content: str
    score: float
    match_reasons: list[str] = field(default_factory=list)


@dataclass
class RepoContext:
    file_list: str
    content: str
    is_truncated: bool
    file_count: int
    total_chars: int
    ranked_files: list[RankedFile] = field(default_factory=list)
    issue_keywords: list[str] = field(default_factory=list)
    selected_file_count: int = 0


class RepoContextCollector:
    def __init__(self, max_file_chars: int = 20000, max_repo_context_chars: int = 50000):
        self.max_file_chars = max_file_chars
        self.max_repo_context_chars = max_repo_context_chars

    def collect(self, code_path: str, issue: str = "") -> RepoContext:
        """Scan the repository and build a ranked deterministic context packet."""
        resolved_path = self.resolve_code_path(code_path)
        file_paths = self._get_filtered_files(resolved_path)
        issue_keywords = self._extract_issue_keywords(issue, resolved_path)
        ranked_files = self._rank_files(file_paths, resolved_path, issue_keywords)
        selected_files, is_truncated = self._select_ranked_files(ranked_files)
        content = self._render_context_content(selected_files, is_truncated)

        # TODO: omit some of the metadata like match_reasons, score, etc
        return RepoContext(
            file_list="\n".join(ranked_file.path for ranked_file in selected_files),
            content=content,
            is_truncated=is_truncated,
            file_count=len(file_paths),
            total_chars=len(content),
            ranked_files=selected_files,
            issue_keywords=issue_keywords,
            selected_file_count=len(selected_files),
        )

    def collect_repo_context(self, code_path: str, issue: str = "") -> tuple[str, str]:
        """Compatibility wrapper for older tuple-based consumers."""
        resolved_path = self.resolve_code_path(code_path)
        repo_context = self.collect(code_path, issue=issue)

        sections = [
            f"Resolved code path: {resolved_path}",
            f"Path type: {'file' if resolved_path.is_file() else 'directory'}",
        ]

        if repo_context.issue_keywords:
            sections.append(f"Issue keywords: {', '.join(repo_context.issue_keywords)}")

        for ranked_file in repo_context.ranked_files:
            sections.append(f"--- FILE: {ranked_file.path} ---\n{ranked_file.content}")

        if repo_context.is_truncated:
            sections.append("--- CONTEXT TRUNCATED ---")

        return repo_context.file_list, "\n\n".join(sections)

    def resolve_code_path(self, raw_code_path: str) -> Path:
        if not raw_code_path:
            raise ValueError("code_path input is required.")

        resolved = Path(raw_code_path).expanduser().resolve()
        if not resolved.exists():
            raise FileNotFoundError(f"code_path does not exist: {resolved}")
        if not (resolved.is_file() or resolved.is_dir()):
            raise ValueError(f"Path is not a file or directory: {resolved}")
        return resolved

    def _resolve_path(self, raw_code_path: str) -> Path:
        return self.resolve_code_path(raw_code_path)

    def _get_filtered_files(self, base_path: Path) -> list[Path]:
        """Recursively find files, skipping hidden and binary content."""
        files: list[Path] = []

        def _walk(current: Path):
            try:
                items = list(current.iterdir())
                for item in items:
                    if item.is_dir():
                        if item.name in SKIP_DIRS:
                            continue
                        _walk(item)
                    elif self._is_text_file(item):
                        files.append(item)
            except PermissionError:
                pass
            except Exception:
                pass

        if base_path.is_file():
            if self._is_text_file(base_path):
                return [base_path]
            return []

        _walk(base_path)
        return sorted(files)

    def _extract_issue_keywords(self, issue: str, resolved_path: Path) -> list[str]:
        raw_tokens = re.findall(r"[a-z0-9_]+", f"{issue} {resolved_path.name}".lower())
        keywords: list[str] = []
        seen: set[str] = set()

        for token in raw_tokens:
            normalized = token.strip('_')
            if not normalized or normalized in STOP_WORDS:
                continue
            if len(normalized) < 3 and normalized not in ALLOWED_SHORT_KEYWORDS:
                continue
            if normalized in seen:
                continue
            seen.add(normalized)
            keywords.append(normalized)

        return keywords

    def _rank_files(
        self,
        file_paths: list[Path],
        resolved_path: Path,
        issue_keywords: list[str],
    ) -> list[RankedFile]:
        ranked_files: list[RankedFile] = []

        for file_path in file_paths:
            content = self._read_text_file_safely(file_path)
            score, reasons = self._score_file(file_path, content, resolved_path, issue_keywords)
            ranked_files.append(
                RankedFile(
                    path=str(file_path),
                    content=content,
                    score=score,
                    match_reasons=reasons,
                )
            )

        return sorted(ranked_files, key=lambda ranked_file: (-ranked_file.score, ranked_file.path))

    def _score_file(
        self,
        file_path: Path,
        content: str,
        resolved_path: Path,
        issue_keywords: list[str],
    ) -> tuple[float, list[str]]:
        reasons: list[str] = []
        path_text = str(file_path).lower()

        path_keyword_score, path_hits = self._path_keyword_score(file_path, issue_keywords)
        if path_hits:
            reasons.append(f"path_keyword:{','.join(path_hits)}")

        content_keyword_score, content_hits = self._content_keyword_score(content, issue_keywords)
        if content_hits:
            reasons.append(f"content_keyword:{','.join(content_hits)}")

        filename_keyword_score, filename_hits = self._filename_keyword_score(file_path, issue_keywords)
        if filename_hits:
            reasons.append(f"filename_keyword:{','.join(filename_hits)}")

        keyword_score = max(
            path_keyword_score,
            min(1.0, (0.75 * content_keyword_score) + (0.25 * filename_keyword_score)),
        )
        combined_keyword_hits = sorted({*path_hits, *content_hits, *filename_hits})
        if combined_keyword_hits:
            reasons.append(f"keyword:{','.join(combined_keyword_hits)}")

        symbol_score = self._content_symbol_score(content, issue_keywords)
        if symbol_score:
            reasons.append(f"symbol:{symbol_score:.2f}")

        proximity_score = self._proximity_score(file_path, resolved_path)
        if proximity_score:
            reasons.append(f"proximity:{proximity_score:.2f}")

        role_score, role_reason = self._role_score(file_path)
        if role_reason:
            reasons.append(role_reason)

        issue_boost = self._issue_signal_boost(file_path, issue_keywords)
        if issue_boost:
            reasons.append(f"issue_boost:{issue_boost:.2f}")

        size_penalty = self._size_penalty(file_path)
        if size_penalty < 1.0:
            reasons.append(f"size_penalty:{size_penalty:.2f}")

        score = (
            (0.45 * keyword_score)
            + (0.20 * symbol_score)
            + (0.15 * proximity_score)
            + (0.15 * role_score)
            + issue_boost
        ) * size_penalty
        return round(score, 6), reasons

    def _path_keyword_score(self, file_path: Path, issue_keywords: list[str]) -> tuple[float, list[str]]:
        path_text = str(file_path).lower()
        path_tokens = set(re.findall(r"[a-z0-9_]+", path_text))
        keyword_hits = [keyword for keyword in issue_keywords if keyword in path_tokens or keyword in path_text]
        score = len(keyword_hits) / max(len(issue_keywords), 1) if issue_keywords else 0.0
        return score, keyword_hits

    def _filename_keyword_score(self, file_path: Path, issue_keywords: list[str]) -> tuple[float, list[str]]:
        file_name = file_path.stem.lower()
        keyword_hits = [keyword for keyword in issue_keywords if keyword in file_name]
        score = len(keyword_hits) / max(len(issue_keywords), 1) if issue_keywords else 0.0
        return score, keyword_hits

    def _content_keyword_score(self, content: str, issue_keywords: list[str]) -> tuple[float, list[str]]:
        if not issue_keywords:
            return 0.0, []

        content_text = content.lower()
        content_tokens = set(re.findall(r"[a-z0-9_]+", content_text))
        keyword_hits = [
            keyword
            for keyword in issue_keywords
            if keyword in content_tokens or re.search(rf"\b{re.escape(keyword)}\b", content_text)
        ]
        score = len(keyword_hits) / len(issue_keywords)
        return score, keyword_hits

    def _content_symbol_score(self, content: str, issue_keywords: list[str]) -> float:
        if not issue_keywords:
            return 0.0

        symbol_candidates = re.findall(
            r"(?:def|class|async\s+def|function|const|let|var|task|flow)\s+([A-Za-z_][A-Za-z0-9_]*)",
            content,
            flags=re.IGNORECASE,
        )
        if not symbol_candidates:
            return 0.0

        normalized_symbols = [symbol.lower() for symbol in symbol_candidates]
        hits = 0
        for keyword in issue_keywords:
            if any(keyword in symbol for symbol in normalized_symbols):
                hits += 1

        return hits / len(issue_keywords)

    def _proximity_score(self, file_path: Path, resolved_path: Path) -> float:
        if resolved_path.is_file():
            if file_path == resolved_path:
                return 1.0
            if file_path.parent == resolved_path.parent:
                return 0.8
            return self._shared_parent_score(file_path, resolved_path.parent)

        if resolved_path in file_path.parents:
            depth = len(file_path.relative_to(resolved_path).parts)
            return max(0.35, 0.9 - (depth * 0.1))

        return self._shared_parent_score(file_path, resolved_path)

    def _shared_parent_score(self, file_path: Path, anchor_path: Path) -> float:
        anchor_parts = anchor_path.parts
        file_parts = file_path.parts
        shared_parts = 0

        for left, right in zip(anchor_parts, file_parts):
            if left != right:
                break
            shared_parts += 1

        if not anchor_parts:
            return 0.0
        return min(0.6, shared_parts / len(anchor_parts))

    def _role_score(self, file_path: Path) -> tuple[float, str | None]:
        path_text = str(file_path).lower()

        if '/config/' in path_text and file_path.suffix in {'.yaml', '.yml'}:
            return 0.95, 'role:config'
        if '/flows/' in path_text:
            return 0.85, 'role:flow'
        if '/crews/' in path_text:
            return 0.80, 'role:crew'
        if '/tests/' in path_text or file_path.name.startswith('test_'):
            return 0.70, 'role:test'
        if '/utils/' in path_text:
            return 0.65, 'role:utility'
        if file_path.name == 'main.py':
            return 0.60, 'role:entrypoint'
        if file_path.suffix == '.md':
            return 0.25, 'role:docs'
        return 0.40, None

    def _issue_signal_boost(self, file_path: Path, issue_keywords: list[str]) -> float:
        path_text = str(file_path).lower()
        boost = 0.0

        if any(keyword.startswith('test') for keyword in issue_keywords):
            if '/tests/' in path_text or file_path.name.startswith('test_'):
                boost += 0.12
        if 'flow' in issue_keywords and '/flows/' in path_text:
            boost += 0.08
        if 'crew' in issue_keywords and '/crews/' in path_text:
            boost += 0.08
        if any(keyword in {'config', 'yaml', 'yml'} for keyword in issue_keywords) and '/config/' in path_text:
            boost += 0.06

        return boost

    def _size_penalty(self, file_path: Path) -> float:
        try:
            size = file_path.stat().st_size
        except OSError:
            return 0.5

        if size <= 2_000:
            return 1.0
        if size <= 10_000:
            return 0.85
        if size <= 50_000:
            return 0.55
        return 0.25

    def _select_ranked_files(self, ranked_files: list[RankedFile]) -> tuple[list[RankedFile], bool]:
        selected_files: list[RankedFile] = []
        current_size = 0
        truncated = False

        for ranked_file in ranked_files:
            section = self._render_ranked_file(ranked_file)
            if current_size + len(section) > self.max_repo_context_chars:
                truncated = True
                if not selected_files:
                    selected_files.append(ranked_file)
                continue
            selected_files.append(ranked_file)
            current_size += len(section)

        return selected_files, truncated

    def _render_context_content(self, ranked_files: list[RankedFile], is_truncated: bool) -> str:
        context_parts = [self._render_ranked_file(ranked_file) for ranked_file in ranked_files]

        if is_truncated:
            context_parts.append("\n\n--- CONTEXT TRUNCATED ---\nFile contents stopped to respect size limits.")

        return "\n".join(context_parts)

    def _render_ranked_file(self, ranked_file: RankedFile) -> str:
        reasons = ', '.join(ranked_file.match_reasons) if ranked_file.match_reasons else 'none'
        return (
            f"### File: {ranked_file.path}\n"
            f"score: {ranked_file.score:.4f}\n"
            f"match_reasons: {reasons}\n"
            f"{ranked_file.content}"
        )

    def _is_text_file(self, path: Path) -> bool:
        """Heuristic to determine if a file is text."""
        if path.suffix.lower() in SKIP_EXTENSIONS:
            return False

        try:
            with path.open('rb') as handle:
                chunk = handle.read(1024)

            if b'\x00' in chunk:
                return False

            chunk.decode('utf-8')
            return True
        except (UnicodeDecodeError, IOError):
            return False

    def _read_text_file_safely(self, file_path: Path) -> str:
        try:
            content = file_path.read_text(encoding='utf-8')
            if len(content) > self.max_file_chars:
                return content[:self.max_file_chars] + "\n\n# ... [File Truncated for Size] ..."
            return content
        except Exception:
            return f"[Error reading file: {file_path}]"