# Copyright [2025] [ecki]
# SPDX-License-Identifier: Apache-2.0

"""
Improved Directory Watcher with better error handling and resource management
"""
import logging
import time
from pathlib import Path
from threading import Event
from typing import Optional

import watchdog.events
import watchdog.observers
from psygnal import Signal
from watchdog.observers.api import BaseObserver

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


class Handler(watchdog.events.FileSystemEventHandler):
    """
    FileSystemEventHandler that emits psygnal signals for different event types
    """
    # Per-instance signals for different event types
    create_signal = Signal(str)
    dir_create_signal = Signal(str)
    change_signal = Signal(str)
    dir_change_signal = Signal(str)
    delete_signal = Signal(str)
    dir_delete_signal = Signal(str)
    move_signal = Signal(tuple)
    dir_move_signal = Signal(tuple)

    def on_any_event(self, event):
        """Handle all filesystem events and emit appropriate signals"""
        try:
            if event.is_directory:
                self._handle_directory_event(event)
            else:
                self._handle_file_event(event)
        except Exception as e:
            logger.error(f"Error handling event {event}: {e}")

    def _handle_directory_event(self, event):
        """Handle directory-specific events"""
        if event.event_type == "created":
            logger.debug(f"Directory created: {event.src_path}")
            self.dir_create_signal.emit(event.src_path)
        elif event.event_type == 'modified':
            logger.debug(f"Directory modified: {event.src_path}")
            self.dir_change_signal.emit(event.src_path)
        elif event.event_type == 'deleted':
            logger.debug(f"Directory deleted: {event.src_path}")
            self.dir_delete_signal.emit(event.src_path)
        elif event.event_type == 'moved':
            logger.debug(f"Directory moved: {event.src_path} -> {event.dest_path}")
            self.dir_move_signal.emit((event.src_path, event.dest_path))

    def _handle_file_event(self, event):
        """Handle file-specific events"""
        if event.event_type == 'created':
            logger.debug(f"File created: {event.src_path}")
            self.create_signal.emit(event.src_path)
        elif event.event_type == 'modified':
            logger.debug(f"File modified: {event.src_path}")
            self.change_signal.emit(event.src_path)
        elif event.event_type == 'deleted':
            logger.debug(f"File deleted: {event.src_path}")
            self.delete_signal.emit(event.src_path)
        elif event.event_type == 'moved':
            logger.debug(f"File moved: {event.src_path} -> {event.dest_path}")
            self.move_signal.emit((event.src_path, event.dest_path))


class VaultWatch:
    """
    Directory watcher with signal-based notifications

    Example:
        watch = VaultWatch("/path/to/watch")
        watch.event_handler.create_signal.connect(my_callback)
        watch.start()
        # ... do work ...
        watch.stop()
    """

    def __init__(self, watch_directory: str, recursive: bool = True):
        """
        Initialize directory watcher

        :param watch_directory: Path to directory to watch
        :param recursive: Watch subdirectories recursively
        :raises ValueError: If directory doesn't exist
        """
        self.directory = Path(watch_directory)
        if not self.directory.exists():
            raise ValueError(f"Directory does not exist: {watch_directory}")
        if not self.directory.is_dir():
            raise ValueError(f"Path is not a directory: {watch_directory}")

        self.recursive = recursive
        self.observer: Optional[BaseObserver] = None
        self.event_handler = Handler()
        self._stop_event = Event()
        self._started = False

        logger.info(f"VaultWatch initialized for: {self.directory}")

    def start(self):
        """Start watching the directory"""
        if self._started:
            logger.warning("Watcher already started")
            return

        try:
            self.observer = watchdog.observers.Observer()
            self.observer.schedule(
                self.event_handler,
                str(self.directory),
                recursive=self.recursive
            )
            self.observer.start()
            self._started = True
            logger.info(f"Started watching: {self.directory}")
        except Exception as e:
            logger.error(f"Failed to start watcher: {e}")
            raise

    def stop(self, timeout: float = 5.0):
        """
        Stop watching the directory

        :param timeout: Maximum time to wait for observer to stop
        """
        if not self._started:
            logger.warning("Watcher not started")
            return

        logger.info("Stopping watcher...")
        self._stop_event.set()

        if self.observer:
            self.observer.stop()
            self.observer.join(timeout=timeout)
            if self.observer.is_alive():
                logger.warning("Observer thread did not stop gracefully")
            else:
                logger.info("Observer stopped successfully")

        self._started = False

    def is_running(self) -> bool:
        """Check if watcher is currently running"""
        return bool(self._started and self.observer and self.observer.is_alive())

    def __enter__(self):
        """Context manager support"""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager cleanup"""
        self.stop()
        return False


# Example callback functions
def on_file_created(path: str):
    """Example callback for file creation"""
    logger.info(f"File created callback: {path}")


def on_file_modified(path: str):
    """Example callback for file modification"""
    logger.info(f"File modified callback: {path}")


def on_file_deleted(path: str):
    """Example callback for file deletion"""
    logger.info(f"File deleted callback: {path}")


def on_file_moved(paths: tuple):
    """Example callback for file move"""
    src, dest = paths
    logger.info(f"File moved callback: {src} -> {dest}")


if __name__ == '__main__':
    # Example usage with context manager
    import tempfile

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Create a temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        logger.info(f"Using temporary directory: {temp_dir}")

        # Create watcher with context manager
        with VaultWatch(temp_dir) as watch:
            # Connect callbacks
            watch.event_handler.create_signal.connect(on_file_created)
            watch.event_handler.change_signal.connect(on_file_modified)
            watch.event_handler.delete_signal.connect(on_file_deleted)
            watch.event_handler.move_signal.connect(on_file_moved)

            logger.info("Watcher started. Creating test files...")

            # Create test file
            test_file = Path(temp_dir) / "test.txt"
            test_file.write_text("Hello World")
            time.sleep(0.5)

            # Modify test file
            test_file.write_text("Hello World Modified")
            time.sleep(0.5)

            # Move test file
            moved_file = Path(temp_dir) / "test_moved.txt"
            test_file.rename(moved_file)
            time.sleep(0.5)

            # Delete test file
            moved_file.unlink()
            time.sleep(0.5)

        logger.info("Watcher stopped. Demo complete.")
