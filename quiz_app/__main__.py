"""Allow running as `python -m quiz_app`."""
import os
import sys
import logging

# Completely suppress all logging that could leak to terminal
logging.disable(logging.CRITICAL)

# Ensure Textual dev mode is OFF (dev mode prints debug logs)
os.environ["TEXTUAL"] = ""
os.environ.pop("TEXTUAL_LOG", None)
os.environ.pop("TEXTUAL_DEVTOOLS", None)

# Redirect stderr to /dev/null to prevent any stray output
_original_stderr = sys.stderr
sys.stderr = open(os.devnull, "w")

try:
    from .app import main
    main()
finally:
    sys.stderr.close()
    sys.stderr = _original_stderr
