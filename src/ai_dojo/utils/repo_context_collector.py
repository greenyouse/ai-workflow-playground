from pathlib import Path


class RepoContextCollector:
	def __init__(self, max_file_chars: int = 20000, max_repo_context_chars: int = 120000):
		self.max_file_chars = max_file_chars
		self.max_repo_context_chars = max_repo_context_chars

	def resolve_code_path(self, raw_code_path: str) -> Path:
		if not raw_code_path:
			raise ValueError(
				"TDDFlow requires a code_path input pointing to a file or directory."
			)

		resolved_path = Path(raw_code_path).expanduser().resolve()
		if not resolved_path.exists():
			raise FileNotFoundError(f"code_path does not exist: {resolved_path}")
		if not (resolved_path.is_file() or resolved_path.is_dir()):
			raise ValueError(f"code_path must be a file or directory: {resolved_path}")
		return resolved_path

	def collect_repo_context(self, resolved_path: Path) -> tuple[str, str]:
		if resolved_path.is_file():
			file_paths = [resolved_path]
			path_type = "file"
		else:
			file_paths = sorted(
				path for path in resolved_path.rglob("*")
				if path.is_file() and not self._should_skip_file(resolved_path, path)
			)
			path_type = "directory"

		collected_files = "\n".join(str(path) for path in file_paths)
		context_sections = [
			f"Resolved code path: {resolved_path}",
			f"Path type: {path_type}",
			f"Collected files count: {len(file_paths)}",
			"Collected files:",
			collected_files or "<none>",
		]

		current_size = sum(len(section) for section in context_sections)
		truncated = False
		for file_path in file_paths:
			file_body = self._read_text_file(file_path)
			section = f"\n\n--- FILE: {file_path} ---\n{file_body}"
			if current_size + len(section) > self.max_repo_context_chars:
				truncated = True
				break
			context_sections.append(section)
			current_size += len(section)

		if truncated:
			context_sections.append(
				"\n\n--- CONTEXT TRUNCATED ---\n"
				"The full file manifest is included above, but file contents were truncated to keep the prompt bounded."
			)

		return collected_files, "\n".join(context_sections)

	def _read_text_file(self, file_path: Path) -> str:
		try:
			contents = file_path.read_text(encoding="utf-8")
		except UnicodeDecodeError:
			contents = file_path.read_text(encoding="utf-8", errors="replace")

		if len(contents) <= self.max_file_chars:
			return contents

		return (
			contents[: self.max_file_chars]
			+ "\n\n# ... truncated to keep repo context bounded ...\n"
		)

	def _should_skip_file(self, base_path: Path, file_path: Path) -> bool:
		relative_parts = file_path.relative_to(base_path).parts[:-1]
		return any("__" in part for part in relative_parts)
