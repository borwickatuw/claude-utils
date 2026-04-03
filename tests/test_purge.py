"""Tests for purge logic."""

import uuid

import pytest

from claude_utils.purge import (
    _collect_targets,
    _dir_size,
    _execute_purge,
    _file_size,
    _format_size,
    _is_empty_dir,
    _scan_project_transcripts,
    _would_be_empty_after_purge,
    run_purge,
)


@pytest.fixture()
def claude_dir(tmp_path):
    """Create a minimal .claude directory structure for testing."""
    d = tmp_path / ".claude"
    d.mkdir()
    return d


@pytest.fixture()
def populated_claude_dir(claude_dir):
    """Create a .claude directory with purgeable content."""
    # Purgeable directories with content
    for dirname in ["sessions", "telemetry", "debug"]:
        dirpath = claude_dir / dirname
        dirpath.mkdir()
        (dirpath / "data.json").write_text('{"test": true}')

    # Purgeable file
    (claude_dir / "history.jsonl").write_text('{"line": 1}\n')

    # Project with transcript
    project = claude_dir / "projects" / "-test-project"
    project.mkdir(parents=True)
    transcript_id = str(uuid.uuid4())
    transcript_dir = project / transcript_id
    transcript_dir.mkdir()
    (transcript_dir / "conversation.json").write_text('{"messages": []}')

    # Project memory (should be preserved)
    memory_dir = project / "memory"
    memory_dir.mkdir()
    (memory_dir / "MEMORY.md").write_text("# Memory\n")

    return claude_dir


class TestFormatSize:
    """Tests for _format_size."""

    def test_bytes(self):
        assert _format_size(500) == "500 B"

    def test_kilobytes(self):
        assert _format_size(2048) == "2.0 KB"

    def test_megabytes(self):
        assert _format_size(5_242_880) == "5.0 MB"

    def test_gigabytes(self):
        assert _format_size(1_073_741_824) == "1.0 GB"

    def test_zero(self):
        assert _format_size(0) == "0 B"


class TestDirSize:
    """Tests for _dir_size."""

    def test_empty_dir(self, tmp_path):
        d = tmp_path / "empty"
        d.mkdir()
        assert _dir_size(d) == 0

    def test_dir_with_files(self, tmp_path):
        d = tmp_path / "files"
        d.mkdir()
        (d / "a.txt").write_text("hello")
        (d / "b.txt").write_text("world!")
        assert _dir_size(d) == 11

    def test_nested_dirs(self, tmp_path):
        d = tmp_path / "nested"
        d.mkdir()
        sub = d / "sub"
        sub.mkdir()
        (sub / "file.txt").write_text("data")
        assert _dir_size(d) == 4


class TestFileSize:
    """Tests for _file_size."""

    def test_existing_file(self, tmp_path):
        f = tmp_path / "test.txt"
        f.write_text("hello")
        assert _file_size(f) == 5

    def test_missing_file(self, tmp_path):
        f = tmp_path / "nonexistent.txt"
        assert _file_size(f) == 0


class TestIsEmptyDir:
    """Tests for _is_empty_dir."""

    def test_empty_dir(self, tmp_path):
        d = tmp_path / "empty"
        d.mkdir()
        assert _is_empty_dir(d) is True

    def test_dir_with_file(self, tmp_path):
        d = tmp_path / "notempty"
        d.mkdir()
        (d / "file.txt").write_text("content")
        assert _is_empty_dir(d) is False

    def test_nested_empty_dirs(self, tmp_path):
        d = tmp_path / "nested"
        d.mkdir()
        (d / "sub1").mkdir()
        (d / "sub1" / "sub2").mkdir()
        assert _is_empty_dir(d) is True

    def test_nested_with_file(self, tmp_path):
        d = tmp_path / "nested"
        d.mkdir()
        sub = d / "sub"
        sub.mkdir()
        (sub / "file.txt").write_text("x")
        assert _is_empty_dir(d) is False


class TestScanProjectTranscripts:
    """Tests for _scan_project_transcripts."""

    def test_finds_uuid_dirs(self, tmp_path):
        project = tmp_path / "project"
        project.mkdir()
        uid = str(uuid.uuid4())
        (project / uid).mkdir()
        targets = _scan_project_transcripts(project)
        assert len(targets) == 1
        assert targets[0].name == uid

    def test_preserves_memory(self, tmp_path):
        project = tmp_path / "project"
        project.mkdir()
        (project / "memory").mkdir()
        targets = _scan_project_transcripts(project)
        assert len(targets) == 0

    def test_preserves_claude_md(self, tmp_path):
        project = tmp_path / "project"
        project.mkdir()
        (project / "CLAUDE.md").write_text("# Claude")
        targets = _scan_project_transcripts(project)
        assert len(targets) == 0

    def test_finds_sessions_index(self, tmp_path):
        project = tmp_path / "project"
        project.mkdir()
        (project / "sessions-index.json").write_text("{}")
        targets = _scan_project_transcripts(project)
        assert len(targets) == 1
        assert targets[0].name == "sessions-index.json"


class TestWouldBeEmptyAfterPurge:
    """Tests for _would_be_empty_after_purge."""

    def test_empty_after_purge(self, tmp_path):
        project = tmp_path / "project"
        project.mkdir()
        uid_dir = project / str(uuid.uuid4())
        uid_dir.mkdir()
        assert _would_be_empty_after_purge(project, {uid_dir}) is True

    def test_not_empty_with_memory(self, tmp_path):
        project = tmp_path / "project"
        project.mkdir()
        uid_dir = project / str(uuid.uuid4())
        uid_dir.mkdir()
        memory = project / "memory"
        memory.mkdir()
        (memory / "MEMORY.md").write_text("content")
        assert _would_be_empty_after_purge(project, {uid_dir}) is False


class TestCollectTargets:
    """Tests for _collect_targets."""

    def test_empty_claude_dir(self, claude_dir):
        targets, total_bytes, empty_count = _collect_targets(claude_dir)
        assert targets == []
        assert total_bytes == 0
        assert empty_count == 0

    def test_finds_purgeable_dirs(self, populated_claude_dir):
        targets, total_bytes, _ = _collect_targets(populated_claude_dir)
        assert total_bytes > 0
        target_names = {t.name for t in targets}
        assert "sessions" in target_names
        assert "telemetry" in target_names

    def test_finds_purgeable_files(self, populated_claude_dir):
        targets, _, _ = _collect_targets(populated_claude_dir)
        target_names = {t.name for t in targets}
        assert "history.jsonl" in target_names


class TestExecutePurge:
    """Tests for _execute_purge."""

    def test_removes_files(self, populated_claude_dir):
        targets, _, _ = _collect_targets(populated_claude_dir)
        result = _execute_purge(targets, populated_claude_dir)
        assert result.bytes_freed > 0
        assert not (populated_claude_dir / "history.jsonl").exists()

    def test_clears_top_level_dirs(self, populated_claude_dir):
        targets, _, _ = _collect_targets(populated_claude_dir)
        _execute_purge(targets, populated_claude_dir)
        # Dir itself should still exist but be empty
        sessions_dir = populated_claude_dir / "sessions"
        assert sessions_dir.is_dir()
        assert list(sessions_dir.iterdir()) == []

    def test_preserves_memory(self, populated_claude_dir):
        targets, _, _ = _collect_targets(populated_claude_dir)
        _execute_purge(targets, populated_claude_dir)
        # Find the project dir
        projects = populated_claude_dir / "projects"
        for project in projects.iterdir():
            memory = project / "memory"
            if memory.exists():
                assert (memory / "MEMORY.md").exists()


class TestRunPurge:
    """Tests for run_purge."""

    def test_nonexistent_dir(self, tmp_path):
        result = run_purge(str(tmp_path / "nonexistent"))
        assert result == 1

    def test_nothing_to_purge(self, claude_dir):
        result = run_purge(str(claude_dir))
        assert result == 0

    def test_dry_run(self, populated_claude_dir, capsys):
        result = run_purge(str(populated_claude_dir), dry_run=True)
        assert result == 0
        assert "dry run" in capsys.readouterr().out.lower()
        # Files should still exist
        assert (populated_claude_dir / "history.jsonl").exists()

    def test_yes_flag(self, populated_claude_dir):
        result = run_purge(str(populated_claude_dir), yes=True)
        assert result == 0
        assert not (populated_claude_dir / "history.jsonl").exists()

    def test_abort_on_no(self, populated_claude_dir, monkeypatch):
        monkeypatch.setattr("builtins.input", lambda _: "n")
        result = run_purge(str(populated_claude_dir))
        assert result == 0
        # Files should still exist
        assert (populated_claude_dir / "history.jsonl").exists()

    def test_abort_on_eof(self, populated_claude_dir, monkeypatch):
        def raise_eof(_):
            raise EOFError

        monkeypatch.setattr("builtins.input", raise_eof)
        result = run_purge(str(populated_claude_dir))
        assert result == 1
