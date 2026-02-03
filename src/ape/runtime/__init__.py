"""APE Runtime Module.

Provides runtime environment abstraction for task execution:
- Sandbox Runtime: Isolated execution on host machine (bubblewrap/sandbox-exec)
- Container Runtime: Container-based execution (Docker)
- Local Runtime: Direct in-process execution without sandboxing
- Isolated Local Runtime: Local execution with workspace isolation via full copying

Architecture:
- base.py: Core abstractions (BaseRuntime, RuntimeConfig)
- utils.py: Common utilities (access control, early stop, path conversion)
- sandbox/: Sandbox runtime implementation (Linux + macOS, auto-registered)
- container/: Container runtime implementation (Docker, auto-registered)
- local/: Local runtime implementation (direct execution)
- isolated_local/: Isolated local runtime (copy-on-execute with permission control)
- registry.py: Runtime registration system
- factory.py: Runtime creation factory functions
"""

# Core abstractions
from ape.runtime.base import BaseRuntime, RuntimeConfig

# Registry functions
from ape.runtime.registry import (
    register_runtime,
    get_runtime_class,
    list_runtime_types,
    get_all_runtime_config_classes,
)

# Factory functions
from ape.runtime.factory import (
    create_runtime,
    create_runtime_config_for_type,
)

# Runtime implementations (automatically registered on import)
from ape.runtime.sandbox import (
    LinuxSandbox,
    MacOSSandbox,
    SandboxRuntimeConfig,
)
from ape.runtime.container import (
    ContainerRuntime,
    ContainerRuntimeConfig,
)
from ape.runtime.local import (
    LocalRuntime,
    LocalRuntimeConfig,
)
from ape.runtime.isolated_local import (
    IsolatedLocalRuntime,
    IsolatedLocalRuntimeConfig,
)


__all__ = [
    # Core abstractions
    'BaseRuntime',
    'RuntimeConfig',
    # Registry functions
    'register_runtime',
    'get_runtime_class',
    'list_runtime_types',
    # Factory functions
    'create_runtime',
    'create_runtime_config_for_type',
    # Runtime implementations
    'LinuxSandbox',
    'MacOSSandbox',
    'ContainerRuntime',
    'LocalRuntime',
    'IsolatedLocalRuntime',
    # Configuration classes
    'SandboxRuntimeConfig',
    'ContainerRuntimeConfig',
    'LocalRuntimeConfig',
    'IsolatedLocalRuntimeConfig',
]
