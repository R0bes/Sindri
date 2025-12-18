"""Tests for sindri.core.group module."""


from sindri.core.command import ShellCommand
from sindri.core.group import CommandGroup


class MockTestGroup(CommandGroup):
    """Test implementation of CommandGroup."""
    
    def __init__(self, commands=None):
        super().__init__(
            group_id="test-group",
            title="Test Group",
            description="A test group",
            order=1,
        )
        self._commands = commands or []
    
    def get_commands(self):
        return self._commands


class TestCommandGroup:
    """Tests for CommandGroup base class."""
    
    def test_command_group_creation(self):
        """Test creating a CommandGroup."""
        group = MockTestGroup()
        assert group.id == "test-group"
        assert group.title == "Test Group"
        assert group.description == "A test group"
        assert group.order == 1
    
    def test_command_group_without_description(self):
        """Test CommandGroup without description."""
        class SimpleGroup(CommandGroup):
            def get_commands(self):
                return []
        
        group = SimpleGroup(group_id="simple", title="Simple")
        assert group.description is None
    
    def test_command_group_without_order(self):
        """Test CommandGroup without order."""
        class SimpleGroup(CommandGroup):
            def get_commands(self):
                return []
        
        group = SimpleGroup(group_id="simple", title="Simple")
        assert group.order is None
    
    def test_command_group_get_commands(self):
        """Test get_commands method."""
        cmd1 = ShellCommand(id="cmd1", shell="echo 1")
        cmd2 = ShellCommand(id="cmd2", shell="echo 2")
        group = MockTestGroup(commands=[cmd1, cmd2])
        
        commands = group.get_commands()
        assert len(commands) == 2
        assert commands[0].id == "cmd1"
        assert commands[1].id == "cmd2"
    
    def test_command_group_get_command_found(self):
        """Test get_command method when command exists."""
        cmd1 = ShellCommand(id="cmd1", shell="echo 1")
        cmd2 = ShellCommand(id="cmd2", shell="echo 2")
        group = MockTestGroup(commands=[cmd1, cmd2])
        
        found = group.get_command("cmd1")
        assert found is not None
        assert found.id == "cmd1"
    
    def test_command_group_get_command_not_found(self):
        """Test get_command method when command doesn't exist."""
        cmd1 = ShellCommand(id="cmd1", shell="echo 1")
        group = MockTestGroup(commands=[cmd1])
        
        found = group.get_command("nonexistent")
        assert found is None
    
    def test_command_group_get_command_empty_group(self):
        """Test get_command with empty group."""
        group = MockTestGroup(commands=[])
        
        found = group.get_command("any")
        assert found is None
    
    def test_command_group_repr(self):
        """Test __repr__ method."""
        cmd1 = ShellCommand(id="cmd1", shell="echo 1")
        cmd2 = ShellCommand(id="cmd2", shell="echo 2")
        group = MockTestGroup(commands=[cmd1, cmd2])
        
        repr_str = repr(group)
        assert "test-group" in repr_str
        assert "Test Group" in repr_str
        assert "2" in repr_str  # command count
    
    def test_command_group_repr_empty(self):
        """Test __repr__ with empty group."""
        group = MockTestGroup(commands=[])
        
        repr_str = repr(group)
        assert "0" in repr_str  # command count

