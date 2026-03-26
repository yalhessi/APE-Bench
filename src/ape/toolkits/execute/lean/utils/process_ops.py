"""
Process operation tools - split from original utils.py for process execution functionality
"""

import os
import sys
import platform
import asyncio
import tempfile
import resource
import psutil
from typing import Optional, List, Dict, Tuple, TYPE_CHECKING
from pathlib import Path
from contextlib import contextmanager
from ape.utils.logging import create_logger

if TYPE_CHECKING:
    import logging

# ==================== Process status check ====================

def is_process_alive(pid: Optional[int]) -> bool:
    """Check if process is still alive
    
    Args:
        pid: Process ID, can be None
        
    Returns:
        bool: Whether process is alive
    """
    if pid is None or pid <= 0:
        return False
    
    try:
        exists = psutil.pid_exists(pid)
    except Exception:
        exists = None

    if exists:
        return True

    # Further confirmation: use os.kill to detect when psutil returns False or an exception occurs
    try:
        # os.kill(pid, 0) throws PermissionError when process exists but has no permission
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except Exception:
        return True

    return True


# ==================== Temporary file tool ====================

@contextmanager
def temporary_file(content: str, suffix: str = ".lean", prefix: str = "verification_"):
    """Create temporary file and automatically clean up"""
    temp_file = None
    try:
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix=suffix,
            prefix=prefix,
            delete=False,
            encoding='utf-8'
        ) as f:
            f.write(content)
            temp_file = f.name
        
        yield temp_file
        
    finally:
        if temp_file and os.path.exists(temp_file):
            os.unlink(temp_file)


# ==================== Resource control function ====================

def set_memory_limit(max_memory_gb: Optional[float], logger: Optional['logging.LoggerAdapter'] = None):
    """Set process memory limit (cross-platform compatible)"""
    if logger is None:
        logger = create_logger()
    
    try:
        if max_memory_gb is not None and False: # WARNING: Memory limit temporarily disabled; do not change
            max_memory_bytes = int(max_memory_gb * 1024 * 1024 * 1024)
            
            # Get current limit
            current_soft, current_hard = resource.getrlimit(resource.RLIMIT_AS)
            
            # On macOS and other systems, if the requested limit exceeds the hard limit or current limit, skip setting
            if current_hard != resource.RLIM_INFINITY and max_memory_bytes > current_hard:
                logger.debug(f"Skip memory limit setting: Request {max_memory_gb}GB exceeds system hard limit")
            elif max_memory_bytes > current_soft and platform.system() == "Darwin":
                # Special handling on macOS: only set in safe cases
                safe_limit = min(max_memory_bytes, current_hard if current_hard != resource.RLIM_INFINITY else max_memory_bytes)
                resource.setrlimit(resource.RLIMIT_AS, (safe_limit, current_hard))
                logger.debug(f"Set memory limit to {safe_limit/1024/1024/1024:.1f}GB on macOS")
            else:
                # Normal setting on Linux and other systems
                resource.setrlimit(resource.RLIMIT_AS, (max_memory_bytes, max_memory_bytes))
                logger.debug(f"Set memory limit to {max_memory_gb}GB on Linux and other systems")
        
        os.setsid()  # Create new process group
    except (ValueError, OSError, resource.error) as e:
        logger.debug(f"Memory limit setting skipped: {e} (system not supported or permission denied)")


def get_process_children(pid: int) -> List[psutil.Process]:
    """Get all child processes of the process"""
    try:
        parent = psutil.Process(pid)
        children = parent.children(recursive=True)
        return children
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return []

async def terminate_async_process_tree(process, timeout: float = 5.0, logger: Optional['logging.LoggerAdapter'] = None):
    """Gracefully terminate asynchronous process tree
    
    Strategy:
    1. First force kill all child processes (to avoid main process waiting for child processes)
    2. Then terminate main process (give main process cleanup opportunity)
    3. If main process does not exit, force kill
    """
    if logger is None:
        logger = create_logger()
    
    if process.returncode is not None:
        return  # Process has terminated
    
    try:
        # Get all child processes (excluding main process)
        # If process has exited, process.pid may be invalid
        try:
            children = get_process_children(process.pid) if process.pid else []
        except (psutil.NoSuchProcess, psutil.AccessDenied, AttributeError):
            children = []
        
        # Strategy 1: Immediately force kill all child processes
        # This way the main process will not wait for child processes to complete
        for child in children:
            try:
                child.kill()  # Direct SIGKILL, no child process cleanup opportunity
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        # Strategy 2: Try to gracefully terminate main process
        try:
            process.terminate()  # SIGTERM, give main process cleanup opportunity
        except (ProcessLookupError, OSError):
            pass  # Process may already not exist
        
        # Wait for main process to terminate
        try:
            await asyncio.wait_for(process.wait(), timeout=timeout)
        except asyncio.TimeoutError:
            # Strategy 3: Force kill main process
            logger.warning(f"Process {process.pid} did not respond to SIGTERM within {timeout} seconds, using SIGKILL")
            try:
                process.kill()
            except (ProcessLookupError, OSError):
                pass
            # Wait again, with timeout to avoid hanging indefinitely
            try:
                await asyncio.wait_for(process.wait(), timeout=5.0)
            except asyncio.TimeoutError:
                logger.warning(f"Process {process.pid} did not exit after SIGKILL (possibly in uninterruptible state), giving up")
            
    except Exception as e:
        logger.warning(f"Failed to terminate asynchronous process tree: {e}")
        # Last resort, directly kill main process
        try:
            process.kill()
            # Wait with timeout to avoid hanging indefinitely
            try:
                await asyncio.wait_for(process.wait(), timeout=5.0)
            except asyncio.TimeoutError:
                logger.warning(f"Process {process.pid} did not exit after kill in exception handling")
        except:
            pass


# ==================== Asynchronous process execution ====================

async def run_command(
    command: List[str],
    cwd: Optional[Path] = None,
    timeout: Optional[float] = None,
    input_text: Optional[str] = None,
    env: Optional[Dict[str, str]] = None,
    max_memory_gb: Optional[float] = None,
    nproc: Optional[int] = None,
    print_output: bool = False,
    operation_name: Optional[str] = None,
    logger: Optional['logging.LoggerAdapter'] = None
) -> Tuple[str, str, int]:
    """Asynchronous command execution, support nproc, memory limit and real-time output
    
    Args:
        command: List of commands to execute
        cwd: Working directory (Path object)
        timeout: Timeout (seconds)
        input_text: Input text
        env: Environment variables
        max_memory_gb: Memory limit (GB)
        nproc: Process number limit
        print_output: Whether to print output in real-time
        operation_name: Operation name (for logging)
        logger: Logger
        
    Returns:
        (stdout, stderr, return_code) Tuple
    """
    if logger is None:
        logger = create_logger()
    
    process_env = os.environ.copy()
    if env:
        process_env.update(env)
    
    # Set nproc (through LEAN_NUM_THREADS environment variable)
    if nproc is not None and nproc > 0:
        # If nproc=1, it will cause apply? to hang, so it is adjusted to 2
        if nproc == 1:
            nproc = 2
        process_env["LEAN_NUM_THREADS"] = str(nproc)
        
        # Set -j parameter (if command supports)
        if "lean" in command:
            # Add -j parameter after lean command
            lean_index = command.index("lean")
            command = command[:lean_index+1] + ["-j", str(nproc)] + command[lean_index+1:]
    
    # Prepare operation name for real-time output
    if print_output:
        op_name = operation_name or "command"
        logger.info(f"[{op_name}] Starting execution: {' '.join(command)}")
        if cwd:
            logger.info(f"[{op_name}] Working directory: {cwd}")
    
    try:
        # Note: In asynchronous version, setting memory limit needs special handling
        preexec_fn = lambda: set_memory_limit(max_memory_gb) if max_memory_gb else None
        
        process = await asyncio.create_subprocess_exec(
            *command,
            cwd=cwd,
            stdin=asyncio.subprocess.PIPE if input_text else asyncio.subprocess.DEVNULL,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=process_env,
            preexec_fn=preexec_fn if max_memory_gb else None
        )

        if input_text and process.stdin is not None:
            process.stdin.write(input_text.encode("utf-8"))
            await process.stdin.drain()
            process.stdin.close()
        
        # Unified streaming read mode (use same logic whether print output or not)
        stdout_lines = []
        stderr_lines = []
        
        async def read_stream(stream, lines_storage, stream_name):
            """Read stream and optionally print in real-time"""
            buffer = b''
            chunk_size = 8192  # Read 8KB each time
            
            while True:
                try:
                    # Use read() instead of readline() to avoid delimiter limit problem
                    chunk = await stream.read(chunk_size)
                    if not chunk:
                        # Process remaining data in buffer
                        if buffer:
                            remaining_str = buffer.decode('utf-8', errors='replace').rstrip()
                            if remaining_str:
                                lines_storage.append(remaining_str)
                                if print_output:
                                    logger.info(f"[{op_name}] {stream_name}: {remaining_str}")
                        break
                    
                    buffer += chunk
                    
                    # Split buffer by line
                    while b'\n' in buffer:
                        line, buffer = buffer.split(b'\n', 1)
                        line_str = line.decode('utf-8', errors='replace').rstrip()
                        if line_str:
                            lines_storage.append(line_str)
                            if print_output:
                                logger.info(f"[{op_name}] {stream_name}: {line_str}")
                    
                    # If buffer is too large (long output without newline), output and clear
                    if len(buffer) > 1024 * 1024:  # 1MB limit
                        buffer_str = buffer.decode('utf-8', errors='replace').rstrip()
                        if buffer_str:
                            lines_storage.append(buffer_str)
                            if print_output:
                                logger.info(f"[{op_name}] {stream_name}: {buffer_str}")
                        buffer = b''
                        
                except asyncio.CancelledError:
                    # Task cancelled, exit immediately
                    logger.debug(f"Stream reading task cancelled: {stream_name}")
                    raise  # Re-throw to correctly propagate cancellation signal
                except Exception as e:
                    logger.warning(f"Error reading {stream_name} stream: {e}")
                    break
        
        # Read stdout and stderr simultaneously
        stdout_task = asyncio.create_task(
            read_stream(process.stdout, stdout_lines, "stdout")
        )
        stderr_task = asyncio.create_task(
            read_stream(process.stderr, stderr_lines, "stderr")
        )
        
        # Wait for process to complete
        try:
            if timeout is not None and timeout > 0:
                returncode = await asyncio.wait_for(process.wait(), timeout=timeout)
            else:
                # No timeout limit
                returncode = await process.wait()
                
            # Normal completion: wait for stream reading to complete
            await asyncio.gather(stdout_task, stderr_task, return_exceptions=True)
            
        except asyncio.TimeoutError:
            if print_output:
                logger.warning(f"[{op_name}] Command execution timed out ({timeout}s)!")
            else:
                logger.warning(f"Command execution timed out ({timeout}s), returning collected output")
                
            # First terminate process
            await terminate_async_process_tree(process, timeout=5.0, logger=logger)
            returncode = -15
            
            # Cancel stream reading task (no longer wait indefinitely)
            stdout_task.cancel()
            stderr_task.cancel()
            
            # Give task a brief time to clean up (up to 2 seconds)
            try:
                await asyncio.wait_for(
                    asyncio.gather(stdout_task, stderr_task, return_exceptions=True),
                    timeout=2.0
                )
            except asyncio.TimeoutError:
                logger.warning(f"Stream reading task did not complete within 2 seconds, forcing continue")
        
        # Merge output
        stdout = '\n'.join(stdout_lines)
        stderr = '\n'.join(stderr_lines)
        
        return stdout, stderr, returncode
            
    except Exception as e:
        if print_output:
            logger.error(f"[{operation_name or 'command'}] Execution exception: {e}")
        logger.error(f"Command execution failed: {e}")
        # Ensure process is cleaned up
        if 'process' in locals() and process.returncode is None:
            await terminate_async_process_tree(process, timeout=2.0, logger=logger)
        raise RuntimeError(f"Command execution failed: {e}")
