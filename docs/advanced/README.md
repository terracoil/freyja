![Freyja Action](https://github.com/terracoil/freyja/raw/main/docs/freyja-action.png)
# Advanced Topics

[↑ Documentation Hub](../README.md)

Advanced patterns and techniques for power users of freyja.

## Topics

### 🔄 State Management
Managing state in class-based CLIs - see [Class CLI Guide](../user-guide/class-cli.md).
- Instance lifecycle patterns
- Shared state between commands
- Database connection management
- Session and context handling
- Thread safety considerations

### ⚙️ Custom Configuration
Advanced CLI configuration options - see [Type Annotations](../features/type-annotations.md).
- Function/method metadata
- Custom parameter handlers
- Argument validation hooks
- Command aliases and shortcuts
- Dynamic command generation

### 🧪 Testing CLIs
Comprehensive testing strategies - see [Best Practices](../guides/best-practices.md).
- Unit testing functions/methods
- Integration testing CLIs
- Mocking and fixtures
- Output capture techniques
- Coverage best practices

### 🔀 Migration Guide
Migrating from other CLI frameworks - see [Getting Started](../getting-started/README.md).
- From argparse to freyja
- From click to freyja
- From fire to freyja
- Preserving backward compatibility
- Gradual migration strategies

## Advanced Patterns

### Architectural Patterns
- Command pattern implementation
- Strategy pattern for handlers
- Factory pattern for commands
- Observer pattern for events
- Decorator pattern extensions

### Performance Optimization
- Lazy loading strategies
- Command caching
- Efficient parameter parsing
- Memory usage optimization
- Startup time reduction

### Integration Patterns
- Async command support
- Background job handling
- Progress bar integration
- Logging framework setup
- Monitoring and metrics

## Code Examples

### Dynamic Command Registration
```python
class DynamicCLI:
    """Freyja with runtime command registration."""
    
    def __init__(self):
        self._commands = {}
    
    def register_command(self, name: str, func: callable):
        """Register a new command at runtime."""
        self._commands[name] = func
        setattr(self, name, func)
```

### Advanced State Management
```python
class StatefulCLI:
    """Freyja with sophisticated state handling."""
    
    def __init__(self):
        self._state = {}
        self._history = []
        self._observers = []
    
    def _notify_observers(self, event: str, data: dict):
        """Notify all observers of state changes."""
        for observer in self._observers:
            observer(event, data)
```

### Custom Validation
```python
from typing import Annotated

def validate_port(port: int) -> int:
    """Validate port number."""
    if not 1 <= port <= 65535:
        raise ValueError(f"Port must be 1-65535, got {port}")
    return port

class NetworkCLI:
    def connect(self, host: str, port: Annotated[int, validate_port]) -> None:
        """Connect to a host."""
        print(f"Connecting to {host}:{port}")
```

## Best Practices

### Design Principles
- Keep commands focused and single-purpose
- Use consistent naming conventions
- Provide meaningful defaults
- Design for testability
- Document edge cases

### Error Handling
- Fail fast with clear messages
- Provide recovery suggestions
- Use appropriate exit codes
- Log errors for debugging
- Handle interrupts gracefully

## Next Steps

- Implement State Management patterns (see [Class CLI Guide](../user-guide/class-cli.md))
- Configure Custom Behavior (see [Type Annotations](../features/type-annotations.md))
- Set up Comprehensive Testing (see [Best Practices](../guides/best-practices.md))
- Plan your Migration Strategy (see [Getting Started](../getting-started/README.md))

---

**Need more?** Check the [API Reference](../reference/README.md) for detailed documentation