"""Tests for sindri.core.templates module."""

from unittest.mock import MagicMock

import pytest
from sindri.core.context import ExecutionContext
from sindri.core.templates import (
    TemplateEngine,
    expand_templates,
    get_template_engine,
)


class TestTemplateEngine:
    """Tests for TemplateEngine class."""
    
    @pytest.fixture
    def engine(self):
        """Create a fresh template engine."""
        return TemplateEngine()
    
    @pytest.fixture
    def ctx(self, tmp_path):
        """Create an execution context."""
        return ExecutionContext(cwd=tmp_path)
    
    def test_default_variables_registered(self, engine):
        """Engine should have default variables registered."""
        assert engine.has("project_name")
        assert engine.has("registry")
        assert engine.has("version")
        assert engine.has("workspace")
        assert engine.has("cwd")
    
    def test_variables_property(self, engine):
        """variables property should list all registered names."""
        variables = engine.variables
        assert "project_name" in variables
        assert "registry" in variables


class TestTemplateEngineExpand:
    """Tests for expand() method."""
    
    @pytest.fixture
    def engine(self):
        return TemplateEngine()
    
    @pytest.fixture
    def ctx(self, tmp_path):
        return ExecutionContext(cwd=tmp_path)
    
    def test_expand_braces_syntax(self, engine, ctx):
        """Should expand {variable} syntax."""
        result = engine.expand("Project: {project_name}", ctx)
        assert ctx.cwd.name in result
    
    def test_expand_dollar_braces_syntax(self, engine, ctx):
        """Should expand ${variable} syntax."""
        result = engine.expand("Project: ${project_name}", ctx)
        assert ctx.cwd.name in result
    
    def test_expand_multiple_variables(self, engine, ctx):
        """Should expand multiple variables in same string."""
        result = engine.expand("{project_name}:{version}", ctx)
        assert ctx.cwd.name in result
    
    def test_expand_unknown_variable_unchanged(self, engine, ctx):
        """Unknown variables should be left unchanged."""
        result = engine.expand("Value: {unknown_var}", ctx)
        assert result == "Value: {unknown_var}"
    
    def test_expand_no_variables(self, engine, ctx):
        """Text without variables should be unchanged."""
        result = engine.expand("No variables here", ctx)
        assert result == "No variables here"
    
    def test_expand_empty_string(self, engine, ctx):
        """Empty string should return empty string."""
        result = engine.expand("", ctx)
        assert result == ""
    
    def test_expand_project_name_from_config(self, engine, tmp_path):
        """project_name should prefer config value."""
        mock_config = MagicMock()
        mock_config.project_name = "configured-name"
        ctx = ExecutionContext(cwd=tmp_path, config=mock_config)
        
        result = engine.expand("{project_name}", ctx)
        assert result == "configured-name"
    
    def test_expand_registry_from_defaults(self, engine, tmp_path):
        """registry should use config defaults if available."""
        mock_config = MagicMock()
        mock_defaults = MagicMock()
        mock_defaults.docker_registry = "my-registry.com:5000"
        mock_config._defaults = mock_defaults
        
        ctx = ExecutionContext(cwd=tmp_path, config=mock_config)
        
        result = engine.expand("{registry}", ctx)
        assert result == "my-registry.com:5000"
    
    def test_expand_cwd(self, engine, ctx):
        """cwd should expand to working directory."""
        result = engine.expand("{cwd}", ctx)
        assert result == str(ctx.cwd)


class TestTemplateEngineRegister:
    """Tests for register() and unregister() methods."""
    
    @pytest.fixture
    def engine(self):
        return TemplateEngine()
    
    @pytest.fixture
    def ctx(self, tmp_path):
        return ExecutionContext(cwd=tmp_path)
    
    def test_register_custom_variable(self, engine, ctx):
        """Should be able to register custom variables."""
        engine.register("custom", lambda c: "custom_value")
        
        result = engine.expand("{custom}", ctx)
        assert result == "custom_value"
    
    def test_register_overrides_existing(self, engine, ctx):
        """Registering existing variable should override."""
        engine.register("project_name", lambda c: "overridden")
        
        result = engine.expand("{project_name}", ctx)
        assert result == "overridden"
    
    def test_unregister_variable(self, engine, ctx):
        """Should be able to unregister variables."""
        engine.register("temp", lambda c: "temp_value")
        assert engine.has("temp")
        
        removed = engine.unregister("temp")
        
        assert removed is True
        assert not engine.has("temp")
        assert engine.expand("{temp}", ctx) == "{temp}"
    
    def test_unregister_nonexistent(self, engine):
        """Unregistering nonexistent variable should return False."""
        removed = engine.unregister("nonexistent")
        assert removed is False
    
    def test_register_with_context_access(self, engine, ctx):
        """Custom resolver should have access to context."""
        engine.register("cwd_name", lambda c: c.cwd.name)
        
        result = engine.expand("{cwd_name}", ctx)
        assert result == ctx.cwd.name


class TestTemplateEngineResolve:
    """Tests for resolve() method."""
    
    @pytest.fixture
    def engine(self):
        return TemplateEngine()
    
    @pytest.fixture
    def ctx(self, tmp_path):
        return ExecutionContext(cwd=tmp_path)
    
    def test_resolve_existing_variable(self, engine, ctx):
        """Should resolve registered variables."""
        result = engine.resolve("project_name", ctx)
        assert result is not None
        assert result == ctx.cwd.name
    
    def test_resolve_nonexistent_variable(self, engine, ctx):
        """Should return None for unknown variables."""
        result = engine.resolve("nonexistent", ctx)
        assert result is None


class TestTemplateEngineExpandStrict:
    """Tests for expand_strict() method."""
    
    @pytest.fixture
    def engine(self):
        return TemplateEngine()
    
    @pytest.fixture
    def ctx(self, tmp_path):
        return ExecutionContext(cwd=tmp_path)
    
    def test_expand_strict_success(self, engine, ctx):
        """Should expand known variables without error."""
        result = engine.expand_strict("{project_name}", ctx)
        assert ctx.cwd.name in result
    
    def test_expand_strict_raises_on_unknown(self, engine, ctx):
        """Should raise ValueError on unknown variables."""
        with pytest.raises(ValueError) as exc_info:
            engine.expand_strict("{unknown_var}", ctx)
        
        assert "unknown_var" in str(exc_info.value)
    
    def test_expand_strict_raises_on_multiple_unknown(self, engine, ctx):
        """Should list all unknown variables in error."""
        with pytest.raises(ValueError) as exc_info:
            engine.expand_strict("{foo} and {bar}", ctx)
        
        error_msg = str(exc_info.value)
        assert "foo" in error_msg or "bar" in error_msg


class TestTemplateEngineFindVariables:
    """Tests for find_variables() method."""
    
    @pytest.fixture
    def engine(self):
        return TemplateEngine()
    
    def test_find_braces_variables(self, engine):
        """Should find {variable} syntax."""
        variables = engine.find_variables("Hello {name}")
        assert "name" in variables
    
    def test_find_dollar_braces_variables(self, engine):
        """Should find ${variable} syntax."""
        variables = engine.find_variables("Hello ${name}")
        assert "name" in variables
    
    def test_find_multiple_variables(self, engine):
        """Should find multiple variables."""
        variables = engine.find_variables("{a} and {b} and ${c}")
        assert "a" in variables
        assert "b" in variables
        assert "c" in variables
    
    def test_find_no_duplicates(self, engine):
        """Should not return duplicates."""
        variables = engine.find_variables("{name} {name} {name}")
        assert variables.count("name") == 1
    
    def test_find_empty_string(self, engine):
        """Should return empty list for empty string."""
        variables = engine.find_variables("")
        assert variables == []
    
    def test_find_no_variables(self, engine):
        """Should return empty list when no variables."""
        variables = engine.find_variables("No variables here")
        assert variables == []


class TestGlobalFunctions:
    """Tests for module-level functions."""
    
    def test_get_template_engine_returns_engine(self):
        """get_template_engine should return a TemplateEngine."""
        engine = get_template_engine()
        assert isinstance(engine, TemplateEngine)
    
    def test_get_template_engine_returns_same_instance(self):
        """get_template_engine should return same instance."""
        engine1 = get_template_engine()
        engine2 = get_template_engine()
        assert engine1 is engine2
    
    def test_expand_templates_function(self, tmp_path):
        """expand_templates function should use default engine."""
        ctx = ExecutionContext(cwd=tmp_path)
        
        result = expand_templates("{project_name}", ctx)
        
        assert ctx.cwd.name in result


class TestTemplateEngineErrorHandling:
    """Tests for error handling in template expansion."""
    
    @pytest.fixture
    def engine(self):
        return TemplateEngine()
    
    @pytest.fixture
    def ctx(self, tmp_path):
        return ExecutionContext(cwd=tmp_path)
    
    def test_resolver_exception_leaves_pattern(self, engine, ctx):
        """If resolver raises, pattern should be left unchanged."""
        def failing_resolver(c):
            raise RuntimeError("Resolver failed")
        
        engine.register("failing", failing_resolver)
        
        # Should not raise, should leave pattern unchanged
        result = engine.expand("{failing}", ctx)
        assert result == "{failing}"
    
    def test_mixed_success_and_failure(self, engine, ctx):
        """Should expand successful vars even if others fail."""
        def failing_resolver(c):
            raise RuntimeError("Failed")
        
        engine.register("failing", failing_resolver)
        
        result = engine.expand("{project_name} and {failing}", ctx)
        
        assert ctx.cwd.name in result
        assert "{failing}" in result
