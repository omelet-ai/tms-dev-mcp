import json
from pathlib import Path

import pytest

from tms_mcp.pipeline.utils import (
    atomic_directory_replace,
    compare_json_files,
    escape_markdown_table_content,
    get_provider_from_path,
    load_markdown_with_front_matter,
    read_json_file,
    sanitize_path_for_filename,
    write_json_file,
    write_markdown_file,
)


class TestWriteJsonFile:
    def test_writes_json_with_newline(self, tmp_path: Path) -> None:
        file_path = tmp_path / "test.json"
        data = {"key": "value"}
        write_json_file(file_path, data)

        content = file_path.read_text()
        assert content.endswith("\n")
        assert json.loads(content) == data

    def test_creates_parent_directories(self, tmp_path: Path) -> None:
        file_path = tmp_path / "nested" / "dir" / "test.json"
        write_json_file(file_path, {"test": True})
        assert file_path.exists()


class TestReadJsonFile:
    def test_reads_valid_json(self, tmp_path: Path) -> None:
        file_path = tmp_path / "test.json"
        file_path.write_text('{"key": "value"}')
        result = read_json_file(file_path)
        assert result == {"key": "value"}

    def test_raises_on_invalid_json(self, tmp_path: Path) -> None:
        file_path = tmp_path / "test.json"
        file_path.write_text("not json")
        with pytest.raises(json.JSONDecodeError):
            read_json_file(file_path)


class TestWriteMarkdownFile:
    def test_writes_with_trailing_newline(self, tmp_path: Path) -> None:
        file_path = tmp_path / "test.md"
        write_markdown_file(file_path, "# Header")
        assert file_path.read_text().endswith("\n")

    def test_does_not_add_extra_newline(self, tmp_path: Path) -> None:
        file_path = tmp_path / "test.md"
        write_markdown_file(file_path, "# Header\n")
        assert file_path.read_text() == "# Header\n"


class TestLoadMarkdownWithFrontMatter:
    def test_parses_front_matter(self, tmp_path: Path) -> None:
        file_path = tmp_path / "test.md"
        file_path.write_text("---\ntitle: Test\ndescription: A test\n---\n# Content")

        metadata, body = load_markdown_with_front_matter(file_path)

        assert metadata["title"] == "Test"
        assert metadata["description"] == "A test"
        assert body.strip() == "# Content"

    def test_returns_empty_metadata_without_front_matter(self, tmp_path: Path) -> None:
        file_path = tmp_path / "test.md"
        file_path.write_text("# No front matter\nJust content")

        metadata, body = load_markdown_with_front_matter(file_path)

        assert metadata == {}
        assert "No front matter" in body


class TestEscapeMarkdownTableContent:
    def test_escapes_pipe_character(self) -> None:
        assert escape_markdown_table_content("a|b") == "a\\|b"

    def test_replaces_newlines(self) -> None:
        assert escape_markdown_table_content("line1\nline2") == "line1 line2"
        assert escape_markdown_table_content("line1\r\nline2") == "line1  line2"


class TestCompareJsonFiles:
    def test_returns_true_for_identical_files(self, tmp_path: Path) -> None:
        file1 = tmp_path / "file1.json"
        file2 = tmp_path / "file2.json"
        file1.write_text('{"key": "value"}')
        file2.write_text('{"key": "value"}')
        assert compare_json_files(file1, file2) is True

    def test_returns_false_for_different_files(self, tmp_path: Path) -> None:
        file1 = tmp_path / "file1.json"
        file2 = tmp_path / "file2.json"
        file1.write_text('{"key": "value1"}')
        file2.write_text('{"key": "value2"}')
        assert compare_json_files(file1, file2) is False

    def test_returns_false_for_missing_file(self, tmp_path: Path) -> None:
        file1 = tmp_path / "exists.json"
        file2 = tmp_path / "missing.json"
        file1.write_text('{"key": "value"}')
        assert compare_json_files(file1, file2) is False


class TestGetProviderFromPath:
    def test_detects_omelet_provider(self) -> None:
        assert get_provider_from_path("/api/vrp") == "omelet"
        assert get_provider_from_path("/api/cost-matrix") == "omelet"

    def test_detects_inavi_provider(self) -> None:
        assert get_provider_from_path("/maps/v3.0/appkeys/{appkey}/coordinates") == "inavi"

    def test_defaults_to_omelet(self) -> None:
        assert get_provider_from_path("/unknown/path") == "omelet"


class TestSanitizePathForFilename:
    def test_removes_omelet_prefix(self) -> None:
        result = sanitize_path_for_filename("omelet", "/api/cost-matrix")
        assert result == "cost-matrix"

    def test_replaces_slashes_with_underscores(self) -> None:
        result = sanitize_path_for_filename("omelet", "/api/nested/path")
        assert result == "nested_path"


class TestAtomicDirectoryReplace:
    def test_replaces_directory(self, tmp_path: Path) -> None:
        source = tmp_path / "source"
        target = tmp_path / "target"

        source.mkdir()
        (source / "file.txt").write_text("new content")

        target.mkdir()
        (target / "old.txt").write_text("old content")

        result = atomic_directory_replace(source, target)

        assert result is True
        assert (target / "file.txt").exists()
        assert (target / "file.txt").read_text() == "new content"
        assert not (target / "old.txt").exists()

    def test_creates_target_if_not_exists(self, tmp_path: Path) -> None:
        source = tmp_path / "source"
        target = tmp_path / "target"

        source.mkdir()
        (source / "file.txt").write_text("content")

        result = atomic_directory_replace(source, target)

        assert result is True
        assert target.exists()
        assert (target / "file.txt").read_text() == "content"

    def test_cleans_up_backup(self, tmp_path: Path) -> None:
        source = tmp_path / "source"
        target = tmp_path / "target"
        backup = tmp_path / "target.backup"

        source.mkdir()
        target.mkdir()
        (source / "file.txt").write_text("content")

        atomic_directory_replace(source, target)

        assert not backup.exists()

    def test_rollback_on_rename_failure(self, tmp_path: Path) -> None:
        from unittest.mock import patch

        source = tmp_path / "source"
        target = tmp_path / "target"

        source.mkdir()
        target.mkdir()
        (source / "new.txt").write_text("new content")
        (target / "old.txt").write_text("old content")

        original_rename = Path.rename
        call_count = 0

        def failing_rename(self: Path, target_path: Path) -> Path:
            nonlocal call_count
            call_count += 1
            if call_count == 2:
                raise OSError("Simulated rename failure")
            return original_rename(self, target_path)

        with patch.object(Path, "rename", failing_rename):
            result = atomic_directory_replace(source, target)

        assert result is False
        assert target.exists()
        assert (target / "old.txt").exists()
        assert (target / "old.txt").read_text() == "old content"

    def test_success_despite_backup_cleanup_failure(self, tmp_path: Path) -> None:
        import shutil
        from unittest.mock import patch

        source = tmp_path / "source"
        target = tmp_path / "target"

        source.mkdir()
        target.mkdir()
        (source / "new.txt").write_text("new content")
        (target / "old.txt").write_text("old content")

        original_rmtree = shutil.rmtree
        rmtree_call_count = 0

        def failing_rmtree(path: Path, ignore_errors: bool = False) -> None:
            nonlocal rmtree_call_count
            rmtree_call_count += 1
            if rmtree_call_count == 2:
                raise OSError("Simulated rmtree failure")
            original_rmtree(path, ignore_errors=ignore_errors)

        with patch("tms_mcp.pipeline.utils.shutil.rmtree", failing_rmtree):
            result = atomic_directory_replace(source, target)

        assert result is True
        assert target.exists()
        assert (target / "new.txt").exists()
        assert (target / "new.txt").read_text() == "new content"
