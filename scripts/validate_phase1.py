#!/usr/bin/env python
"""Quick validation script for Phase 1 core modules."""

import sys
from pathlib import Path

def main():
    """Run basic validation checks."""
    print("=" * 60)
    print("Phase 1 Core Module Validation")
    print("=" * 60)
    
    errors = []
    
    # Test 1: Import core modules
    print("\n[1/5] Testing core module imports...")
    try:
        from sindri.core import CommandResult, ExecutionContext, TemplateEngine
        print("  ✓ Core modules imported successfully")
    except ImportError as e:
        errors.append(f"Import error: {e}")
        print(f"  ✗ Import failed: {e}")
    
    # Test 2: Backward compatibility - runner imports
    print("\n[2/5] Testing backward compatibility (runner imports)...")
    try:
        from sindri.runner import CommandResult as RunnerResult
        from sindri.runner.result import CommandResult as ResultResult
        assert RunnerResult is ResultResult
        print("  ✓ Backward compatible imports work")
    except Exception as e:
        errors.append(f"Backward compat error: {e}")
        print(f"  ✗ Failed: {e}")
    
    # Test 3: CommandResult functionality
    print("\n[3/5] Testing CommandResult...")
    try:
        from sindri.core import CommandResult
        
        # Success case
        result = CommandResult(command_id="test", exit_code=0, stdout="OK")
        assert result.success is True
        assert bool(result) is True
        
        # Failure case
        result = CommandResult(command_id="test", exit_code=1, error="Failed")
        assert result.success is False
        assert bool(result) is False
        
        print("  ✓ CommandResult works correctly")
    except Exception as e:
        errors.append(f"CommandResult error: {e}")
        print(f"  ✗ Failed: {e}")
    
    # Test 4: ExecutionContext functionality
    print("\n[4/5] Testing ExecutionContext...")
    try:
        from sindri.core import ExecutionContext
        
        ctx = ExecutionContext(cwd=Path.cwd())
        assert ctx.cwd.is_absolute()
        assert ctx.project_name == Path.cwd().name
        assert isinstance(ctx.get_env(), dict)
        
        # Test child context
        child = ctx.child(dry_run=True)
        assert child.dry_run is True
        assert ctx.dry_run is False
        
        print("  ✓ ExecutionContext works correctly")
    except Exception as e:
        errors.append(f"ExecutionContext error: {e}")
        print(f"  ✗ Failed: {e}")
    
    # Test 5: TemplateEngine functionality
    print("\n[5/5] Testing TemplateEngine...")
    try:
        from sindri.core import ExecutionContext, TemplateEngine
        
        engine = TemplateEngine()
        ctx = ExecutionContext(cwd=Path.cwd())
        
        # Test expansion
        result = engine.expand("{project_name}", ctx)
        assert result == ctx.cwd.name
        
        # Test custom variable
        engine.register("custom", lambda c: "custom_value")
        result = engine.expand("{custom}", ctx)
        assert result == "custom_value"
        
        # Test context integration
        result = ctx.expand_templates("{project_name}")
        assert ctx.cwd.name in result
        
        print("  ✓ TemplateEngine works correctly")
    except Exception as e:
        errors.append(f"TemplateEngine error: {e}")
        print(f"  ✗ Failed: {e}")
    
    # Summary
    print("\n" + "=" * 60)
    if errors:
        print(f"FAILED: {len(errors)} error(s)")
        for error in errors:
            print(f"  - {error}")
        return 1
    else:
        print("SUCCESS: All Phase 1 core modules validated!")
        print("\nNext steps:")
        print("  1. Run full test suite: pytest tests/ -v")
        print("  2. Run new unit tests: pytest tests/unit/ -v")
        return 0


if __name__ == "__main__":
    sys.exit(main())
