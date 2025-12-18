"""Utility modules for Sindri."""

from sindri.utils.command_defaults import (
    detect_application_entry_point,
    detect_linter,
    detect_validator,
    get_build_command,
    get_lint_command,
    get_restart_command,
    get_start_command,
    get_stop_command,
    get_validate_command,
)
from sindri.utils.helper import (
    escape_shell_arg,
    find_project_root,
    get_project_name,
    get_shell,
)
from sindri.utils.logging import get_logger, setup_logging
from sindri.utils.name_normalizer import normalize_project_name
from sindri.utils.pyproject_updater import update_pyproject_for_sindri
from sindri.utils.validate_dependencies import validate_pyproject_dependencies
from sindri.utils.venv_helper import (
    get_install_command,
    get_setup_command,
    get_venv_path,
    get_venv_pip,
    get_venv_python,
)

__all__ = [
    "detect_application_entry_point",
    "detect_linter",
    "detect_validator",
    "escape_shell_arg",
    "find_project_root",
    "get_build_command",
    "get_install_command",
    "get_lint_command",
    "get_project_name",
    "get_restart_command",
    "get_setup_command",
    "get_shell",
    "get_venv_path",
    "get_start_command",
    "get_stop_command",
    "get_validate_command",
    "get_venv_pip",
    "get_venv_python",
    "get_logger",
    "setup_logging",
    "normalize_project_name",
    "update_pyproject_for_sindri",
    "validate_pyproject_dependencies",
]

