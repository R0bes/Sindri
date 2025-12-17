"""Command implementations organized by groups."""

from sindri.commands.command import Command
from sindri.commands.group import CommandGroup
from sindri.commands.shell_command import ShellCommand

# Import command groups
from sindri.commands.general import GeneralGroup
from sindri.commands.quality import QualityGroup
from sindri.commands.application import ApplicationGroup
from sindri.commands.docker import DockerGroup
from sindri.commands.compose import ComposeGroup
from sindri.commands.git import GitGroup
from sindri.commands.pypi import PyPIGroup
from sindri.commands.sindri import SindriGroup
from sindri.commands.version import VersionGroup

__all__ = [
    "Command",
    "CommandGroup",
    "ShellCommand",
    "SindriGroup",
    "GeneralGroup",
    "QualityGroup",
    "ApplicationGroup",
    "DockerGroup",
    "ComposeGroup",
    "GitGroup",
    "VersionGroup",
    "PyPIGroup",
]
