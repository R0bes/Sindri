"""Built-in command groups."""

from sindri.groups.general import GeneralGroup
from sindri.groups.quality import QualityGroup
from sindri.groups.application import ApplicationGroup
from sindri.groups.docker import DockerGroup
from sindri.groups.compose import ComposeGroup
from sindri.groups.git import GitGroup
from sindri.groups.version import VersionGroup
from sindri.groups.pypi import PyPIGroup
from sindri.groups.sindri_group import SindriGroup

__all__ = [
    "GeneralGroup",
    "QualityGroup",
    "ApplicationGroup",
    "DockerGroup",
    "ComposeGroup",
    "GitGroup",
    "VersionGroup",
    "PyPIGroup",
    "SindriGroup",
]


def get_all_builtin_groups():
    """Get instances of all built-in groups."""
    return [
        SindriGroup(),
        GeneralGroup(),
        QualityGroup(),
        ApplicationGroup(),
        DockerGroup(),
        ComposeGroup(),
        GitGroup(),
        VersionGroup(),
        PyPIGroup(),
    ]
