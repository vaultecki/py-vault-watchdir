import time

import pytest

from watch_directory_change import Handler, VaultWatch


def wait_until(predicate, timeout=3.0, interval=0.05):
    """Poll predicate() until it returns truthy or timeout elapses."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(interval)
    return predicate()


class TestVaultWatchInit:
    def test_raises_for_missing_directory(self, tmp_path):
        missing = tmp_path / "does_not_exist"
        with pytest.raises(ValueError):
            VaultWatch(str(missing))

    def test_raises_when_path_is_a_file(self, tmp_path):
        file_path = tmp_path / "somefile.txt"
        file_path.write_text("hello")
        with pytest.raises(ValueError):
            VaultWatch(str(file_path))

    def test_accepts_existing_directory(self, tmp_path):
        watch = VaultWatch(str(tmp_path))
        assert watch.directory == tmp_path
        assert watch.recursive is True
        assert isinstance(watch.event_handler, Handler)

    def test_non_recursive_flag_stored(self, tmp_path):
        watch = VaultWatch(str(tmp_path), recursive=False)
        assert watch.recursive is False


class TestVaultWatchLifecycle:
    def test_start_stop_toggles_running_state(self, tmp_path):
        watch = VaultWatch(str(tmp_path))
        assert watch.is_running() is False

        watch.start()
        try:
            assert watch.is_running() is True
        finally:
            watch.stop()

        assert watch.is_running() is False

    def test_double_start_is_a_no_op(self, tmp_path):
        watch = VaultWatch(str(tmp_path))
        watch.start()
        try:
            first_observer = watch.observer
            watch.start()
            assert watch.observer is first_observer
            assert watch.is_running() is True
        finally:
            watch.stop()

    def test_stop_without_start_does_not_raise(self, tmp_path):
        watch = VaultWatch(str(tmp_path))
        watch.stop()
        assert watch.is_running() is False

    def test_context_manager_starts_and_stops(self, tmp_path):
        with VaultWatch(str(tmp_path)) as watch:
            assert watch.is_running() is True
        assert watch.is_running() is False


class TestHandlerSignals:
    def test_file_create_signal(self, tmp_path):
        received = []
        with VaultWatch(str(tmp_path)) as watch:
            # NOTE: PySignal only keeps a strong reference to lambdas/partials;
            # a bound method like `received.append` would be wrapped in a
            # weakref that dies before it can ever fire. Use a lambda.
            watch.event_handler.create_signal.connect(lambda p: received.append(p))

            (tmp_path / "new_file.txt").write_text("content")

            assert wait_until(lambda: len(received) > 0)
        assert received[0].endswith("new_file.txt")

    def test_file_change_signal(self, tmp_path):
        target = tmp_path / "existing.txt"
        target.write_text("initial")

        received = []
        with VaultWatch(str(tmp_path)) as watch:
            watch.event_handler.change_signal.connect(lambda p: received.append(p))

            target.write_text("updated content")

            assert wait_until(lambda: len(received) > 0)
        assert received[0].endswith("existing.txt")

    def test_file_delete_signal(self, tmp_path):
        target = tmp_path / "to_delete.txt"
        target.write_text("bye")

        received = []
        with VaultWatch(str(tmp_path)) as watch:
            watch.event_handler.delete_signal.connect(lambda p: received.append(p))

            target.unlink()

            assert wait_until(lambda: len(received) > 0)
        assert received[0].endswith("to_delete.txt")

    def test_file_move_signal_emits_src_and_dest(self, tmp_path):
        source = tmp_path / "source.txt"
        source.write_text("move me")
        dest = tmp_path / "dest.txt"

        received = []
        with VaultWatch(str(tmp_path)) as watch:
            watch.event_handler.move_signal.connect(lambda p: received.append(p))

            source.rename(dest)

            assert wait_until(lambda: len(received) > 0)
        src_path, dest_path = received[0]
        assert src_path.endswith("source.txt")
        assert dest_path.endswith("dest.txt")

    def test_directory_create_signal(self, tmp_path):
        received = []
        with VaultWatch(str(tmp_path)) as watch:
            watch.event_handler.dir_create_signal.connect(lambda p: received.append(p))

            (tmp_path / "subdir").mkdir()

            assert wait_until(lambda: len(received) > 0)
        assert received[0].endswith("subdir")

    def test_directory_delete_signal(self, tmp_path):
        subdir = tmp_path / "subdir_to_delete"
        subdir.mkdir()

        received = []
        with VaultWatch(str(tmp_path)) as watch:
            watch.event_handler.dir_delete_signal.connect(lambda p: received.append(p))

            subdir.rmdir()

            assert wait_until(lambda: len(received) > 0)
        assert received[0].endswith("subdir_to_delete")

    def test_handler_instances_have_independent_signals(self, tmp_path):
        handler_a = Handler()
        handler_b = Handler()

        received_a = []
        handler_a.create_signal.connect(received_a.append)

        handler_b.create_signal.emit("/some/path")

        assert received_a == []
