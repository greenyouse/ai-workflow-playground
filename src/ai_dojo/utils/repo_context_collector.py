from pathlib import Path
from dataclasses import dataclass

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

@dataclass
class RepoContext:
    file_list: str
    content: str
    is_truncated: bool
    file_count: int
    total_chars: int

class RepoContextCollector:
    def __init__(self, max_file_chars: int = 20000, max_repo_context_chars: int = 50000):
        self.max_file_chars = max_file_chars
        self.max_repo_context_chars = max_repo_context_chars

    def collect(self, code_path: str) -> RepoContext:
        """
        Scans the repository at code_path and returns a RepoContext object.
        """
        resolved_path = self._resolve_path(code_path)
        file_paths = self._get_filtered_files(resolved_path)
        
        context_parts = []
        current_size = 0
        truncated = False

        for file_path in file_paths:
            # Check if adding this file would exceed total repo context limit
            # We estimate file size by reading it safely. 
            # To be safe, we read the content first.
            content = self._read_text_file_safely(file_path)
            
            # If content is empty or error message, we might still want to include it 
            # or skip it. Here we include error messages for debugging.
            
            section = f"### File: {file_path}\n{content}"
            
            if current_size + len(section) > self.max_repo_context_chars:
                truncated = True
                break
            
            context_parts.append(section)
            current_size += len(section)

        if truncated:
            context_parts.append("\n\n--- CONTEXT TRUNCATED ---\nFile contents stopped to respect size limits.")

        full_content = "\n".join(context_parts)
        
        return RepoContext(
            file_list="\n".join(str(p) for p in file_paths),
            content=full_content,
            is_truncated=truncated,
            file_count=len(file_paths),
            total_chars=len(full_content)
        )

    def _resolve_path(self, raw_code_path: str) -> Path:
        if not raw_code_path:
            raise ValueError("code_path input is required.")
        
        resolved = Path(raw_code_path).expanduser().resolve()
        if not resolved.exists():
            raise FileNotFoundError(f"Path does not exist: {resolved}")
        if not (resolved.is_file() or resolved.is_dir()):
            raise ValueError(f"Path is not a file or directory: {resolved}")
        return resolved

    def _get_filtered_files(self, base_path: Path) -> list[Path]:
        """Recursively find files, skipping hidden/binary dirs."""
        files = []
        
        def _walk(current: Path):
            try:
                # List directory contents, handling permission errors
                items = list(current.iterdir())
                for item in items:
                    if item.is_dir():
                        # Check if directory name is in skip list
                        if item.name in SKIP_DIRS:
                            continue
                        _walk(item)
                    else:
                        if self._is_text_file(item):
                            files.append(item)
            except PermissionError:
                pass # Skip unreadable dirs
            except Exception:
                pass # Skip other unexpected IO errors

        if base_path.is_file():
            if self._is_text_file(base_path):
                return [base_path]
            return []
        
        _walk(base_path)
        return sorted(files)

    def _is_text_file(self, path: Path) -> bool:
        """Heuristic to determine if a file is text."""
        # Check extension first for known binary types
        if path.suffix.lower() in SKIP_EXTENSIONS:
            return False
        
        try:
            # Read first 1024 bytes to check for binary content
            with open(path, 'rb') as f:
                chunk = f.read(1024)
            
            # Check for null bytes which indicate binary
            if b'\x00' in chunk:
                return False
            
            # Try decoding
            chunk.decode('utf-8')
            return True
        except (UnicodeDecodeError, IOError):
            return False

    def _read_text_file_safely(self, file_path: Path) -> str:
        try:
            content = file_path.read_text(encoding="utf-8")
            if len(content) > self.max_file_chars:
                # Truncate but try to keep logical blocks intact if possible
                # Simple approach: hard cut + note
                return content[:self.max_file_chars] + "\n\n# ... [File Truncated for Size] ..."
            return content
        except Exception:
            return f"[Error reading file: {file_path}]"