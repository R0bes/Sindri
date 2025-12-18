"""Built-in command groups.

All groups use the new core/ architecture:
- Commands implement the Command Protocol
- ShellCommand for simple shell commands
- CustomCommand for complex logic
"""

from sindri.groups.sindri_group import SindriGroup
from sindri.groups.general import GeneralGroup
from sindri.groups.quality import QualityGroup
from sindri.groups.application import ApplicationGroup
from sindri.groups.docker import DockerGroup
from sindri.groups.compose import ComposeGroup
from sindri.groups.git import GitGroup
from sindri.groups.version import VersionGroup
from sindri.groups.pypi import PyPIGroup

__all__ = [
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


def get_all_builtin_groups():
    """Get instances of all built-in groups.
    
    Returns groups in display order.
    """
    return [
        SindriGroup(),      # order=0
        GeneralGroup(),     # order=1
        VersionGroup(),     # order=2
        QualityGroup(),     # order=2
        ApplicationGroup(), # order=2
        DockerGroup(),      # order=3
        ComposeGroup(),     # order=4
        GitGroup(),         # order=5
        PyPIGroup(),        # order=6
    ]
