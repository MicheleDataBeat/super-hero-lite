"""Keep the documented plain unittest invocation free of package bytecode."""

from pathlib import Path
import sys


sys.dont_write_bytecode = True

# CPython caches a package initializer before executing it, so the flag above
# protects downstream imports but cannot prevent this initializer's own cache.
# Remove that one loader-created artifact immediately and leave no cache dir.
if __cached__:
    cache_path = Path(__cached__)
    cache_path.unlink(missing_ok=True)
    try:
        cache_path.parent.rmdir()
    except OSError:
        pass
