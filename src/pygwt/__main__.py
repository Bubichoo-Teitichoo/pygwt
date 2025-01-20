"""Main Module."""

from pygwt.cli.commands import main
from pygwt.completions import PowershellComplete  # noqa: F401 - required to enable powershell completions

if __name__ == "__main__":
    main()
