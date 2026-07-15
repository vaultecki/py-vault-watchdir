# Directory Watcher with Signal-Based Notifications

A robust Python directory watcher that monitors filesystem changes and emits signals for different event types using psygnal and watchdog.

## Features

- **Signal-Based Architecture**: Uses psygnal for loose coupling between file events and handlers
- **Comprehensive Event Handling**: Monitors file/directory creation, modification, deletion, and moves
- **Resource Management**: Proper cleanup with context manager support
- **Thread-Safe**: Built on watchdog's Observer pattern
- **Error Handling**: Graceful error handling and logging
- **Type Hints**: Full type annotation for better IDE support
- **Recursive Watching**: Optional recursive directory monitoring

## Installation

### Prerequisites

- Python 3.7 or higher

### Install Dependencies

```bash
pip install .
```

For development (linting with ruff, running tests with pytest):

```bash
pip install -e ".[dev]"
```

## Usage

### Basic Usage

```python
from watch_directory_change import VaultWatch

# Create watcher instance
watch = VaultWatch("/path/to/watch")

# Define callback function
def on_file_created(path):
    print(f"New file created: {path}")

# Connect callback to signal
watch.event_handler.create_signal.connect(on_file_created)

# Start watching
watch.start()

# ... do your work ...

# Stop watching
watch.stop()
```

### Context Manager (Recommended)

```python
from watch_directory_change import VaultWatch

def handle_creation(path):
    print(f"Created: {path}")

def handle_modification(path):
    print(f"Modified: {path}")

# Automatic cleanup with context manager
with VaultWatch("/path/to/watch") as watch:
    watch.event_handler.create_signal.connect(handle_creation)
    watch.event_handler.change_signal.connect(handle_modification)
    
    # Watcher is running here
    # ... do your work ...
    
# Watcher is automatically stopped here
```

### Non-Recursive Watching

```python
# Watch only the specified directory, not subdirectories
watch = VaultWatch("/path/to/watch", recursive=False)
```

## Available Signals

### File Events
- `create_signal` - File created
- `change_signal` - File modified
- `delete_signal` - File deleted
- `move_signal` - File moved (emits tuple: `(src_path, dest_path)`)

### Directory Events
- `dir_create_signal` - Directory created
- `dir_change_signal` - Directory modified
- `dir_delete_signal` - Directory deleted
- `dir_move_signal` - Directory moved (emits tuple: `(src_path, dest_path)`)

## Examples

### Example 1: Simple File Monitor

```python
from watch_directory_change import VaultWatch
import time

def log_change(path):
    print(f"File changed: {path}")

watch = VaultWatch("/tmp/myfiles")
watch.event_handler.change_signal.connect(log_change)
watch.start()

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    watch.stop()
```

### Example 2: Multiple Event Handlers

```python
from watch_directory_change import VaultWatch

def on_create(path):
    print(f"✓ Created: {path}")

def on_modify(path):
    print(f"✎ Modified: {path}")

def on_delete(path):
    print(f"✗ Deleted: {path}")

def on_move(paths):
    src, dest = paths
    print(f"→ Moved: {src} → {dest}")

with VaultWatch("/home/user/documents") as watch:
    # Connect all handlers
    watch.event_handler.create_signal.connect(on_create)
    watch.event_handler.change_signal.connect(on_modify)
    watch.event_handler.delete_signal.connect(on_delete)
    watch.event_handler.move_signal.connect(on_move)
    
    input("Press Enter to stop watching...\n")
```

### Example 3: Directory-Specific Monitoring

```python
from watch_directory_change import VaultWatch

def on_dir_created(path):
    print(f"New directory: {path}")
    # Perform some action when a new directory is created

with VaultWatch("/project/src") as watch:
    watch.event_handler.dir_create_signal.connect(on_dir_created)
    input("Monitoring directories. Press Enter to exit...\n")
```

## API Reference

### `VaultWatch(watch_directory, recursive=True)`

Main watcher class.

**Parameters:**
- `watch_directory` (str): Path to the directory to watch
- `recursive` (bool, optional): Watch subdirectories recursively. Default: True

**Raises:**
- `ValueError`: If the directory doesn't exist or is not a directory

**Methods:**
- `start()`: Start watching the directory
- `stop(timeout=5.0)`: Stop watching with optional timeout
- `is_running()`: Check if watcher is currently active

### `Handler`

Event handler class with signals.

**Signals:**
- File signals: `create_signal`, `change_signal`, `delete_signal`, `move_signal`
- Directory signals: `dir_create_signal`, `dir_change_signal`, `dir_delete_signal`, `dir_move_signal`

## Running the Demo

The module includes a built-in demo that creates temporary files and monitors them:

```bash
python watch_directory_change.py
```

## Logging

The module uses Python's built-in logging. To adjust the log level:

```python
import logging

# Set to DEBUG to see all events
logging.getLogger('watch_directory_change').setLevel(logging.DEBUG)

# Set to WARNING to see only warnings and errors
logging.getLogger('watch_directory_change').setLevel(logging.WARNING)
```

## Error Handling

The watcher includes comprehensive error handling:

- Directory validation on initialization
- Graceful observer shutdown
- Exception handling in event callbacks
- Timeout handling for stop operations

## Technical Details

- Built on `watchdog` for cross-platform filesystem monitoring
- Uses `psygnal` for event emission and callback management
- Thread-safe operation using watchdog's Observer pattern
- Proper resource cleanup with context manager protocol

## Common Issues

### Watcher doesn't detect changes immediately

Some operating systems batch filesystem events. Small delays (0.1-0.5s) are normal.

### Observer thread doesn't stop

Check that you're calling `stop()` and not forcefully killing the process. The default timeout is 5 seconds.

### High CPU usage

Watching very large directory trees recursively can be resource-intensive. Consider:
- Using `recursive=False` if you don't need subdirectory monitoring
- Implementing filtering logic in your callbacks
- Watching specific subdirectories instead of root directories

## License

- Copyright [2025] [ecki]
- SPDX-License-Identifier: Apache-2.0

- This project is provided as-is for educational and commercial use.

## Contributing

Suggestions and improvements are welcome!

## Dependencies

- `watchdog>=5.0.3` - Cross-platform filesystem event monitoring
- `psygnal>=0.9.0` - Signal/slot implementation for Python
