"""
MCP Manager - Unified MCP lifecycle management in toolkit layer.

This module provides a centralized manager for MCP server/client lifecycle
and tool instance tracking. It supports both direct mode (FastMCP + Client)
and HTTP mode (FastMCP HTTP server).

Architecture:
- MCPManager owns and manages:
  - FastMCP server instance
  - MCP Client instance (direct mode) or HTTP server task (HTTP mode)
  - Tool provider instances (for cleanup)
- Scaffolds use MCPManager, never directly touch tool instances
- All tool binding logic is internal to MCPManager
"""

import asyncio
import logging
import socket
from typing import Optional, Dict, Any, Set, TYPE_CHECKING
from fastmcp import FastMCP, Client

from ape.scaffolds.base import ComponentSetupError
from ape.toolkits.registry import get_all_tool_names, list_registered_tools
from ape.toolkits.file_system import FileSystemToolsProvider
from ape.toolkits.execute.bash import BashExecuteToolsProvider
from ape.utils.logging import create_mcp_log_handler

if TYPE_CHECKING:
	from ape.tasks.base import BaseTask
	from ape.scaffolds.config import BaseScaffoldConfig
	from ape.toolkits.base import BaseToolsProvider


def _allocate_port() -> int:
	"""Allocate a free port for HTTP server."""
	with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
		s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		s.bind(('localhost', 0))
		port = s.getsockname()[1]
	return port


class MCPManager:
	"""
	Unified MCP Manager - Manages MCP server/client lifecycle and tool instances.

	This manager supports two modes:
	1. Direct mode: FastMCP server + Client (in-process communication)
	2. HTTP mode: FastMCP HTTP server (network communication)

	In both modes, it tracks tool provider instances for proper cleanup.

	Usage (Direct mode):
		manager = MCPManager(task, logger, config, confirmation_bridge, is_cli_mode)
		await manager.setup_direct_mode(enabled_tools)
		client = manager.get_client()
		... use client ...
		await manager.cleanup()

	Usage (HTTP mode):
		manager = MCPManager(task, logger, config, is_cli_mode=False)
		server_url = await manager.setup_http_mode(enabled_tools)
		... connect to server_url ...
		await manager.cleanup()
	"""

	def __init__(
		self,
		task: 'BaseTask',
		logger: 'logging.LoggerAdapter',
		config: 'BaseScaffoldConfig',
		confirmation_bridge: Optional[Any] = None,
		is_cli_mode: bool = False,
		use_native_tools: bool = True,
	):
		"""
		Initialize MCP Manager.

		Args:
			task: Task instance
			logger: Logger instance
			config: Scaffold configuration
			confirmation_bridge: User confirmation bridge for CLI mode
			is_cli_mode: Whether in CLI mode
			use_native_tools: Whether to use our native MCP tools (file_system, bash_execute); if False, disable them
		"""
		self.task = task
		self.logger = logger
		self.config = config
		self.confirmation_bridge = confirmation_bridge
		self.is_cli_mode = is_cli_mode
		self.use_native_tools = use_native_tools

		# Core MCP components
		self.mcp_server: Optional[FastMCP] = None
		self.mcp_client: Optional[Client] = None
		self.tool_instances: Dict[type, 'BaseToolsProvider'] = {}

		# HTTP server mode components
		self.http_server_task: Optional[asyncio.Task] = None
		self._http_server: Optional[Any] = None
		self._server_port: Optional[int] = None
		self._server_url: Optional[str] = None

		# Mode tracking
		self._mode: Optional[str] = None  # 'direct' or 'http'

	def calculate_enabled_tools(self, custom_enabled_tools: Optional[Set[str]] = None) -> Set[str]:
		"""
		Calculate enabled tools set.

		Logic:
		1. Get all available tools from registry
		2. If use_native_tools=False, remove our native file system and bash tools (use SDK builtin tools instead)
		3. Apply task configuration filters (enabled_tools / disabled_tools)
		4. Apply custom_enabled_tools if provided (for scaffold-specific filtering)

		Args:
			custom_enabled_tools: Optional custom tool set to use instead of config

		Returns:
			Set of enabled tool names
		"""
		all_available_tools = set(get_all_tool_names())

		# If not using native tools, remove file system and bash execution tools from MCP layer
		# to avoid duplication with SDK builtin tools
		if not self.use_native_tools:
			registered_tools = list_registered_tools()
			native_tools_to_disable = {
				tool_name
				for tool_name, provider_class in registered_tools.items()
				if provider_class in (FileSystemToolsProvider, BashExecuteToolsProvider)
			}
			all_available_tools = all_available_tools - native_tools_to_disable
			self.logger.info(
				f"[MCPManager] use_native_tools=False, disabled native MCP tools (using SDK builtin instead): {sorted(native_tools_to_disable)}"
			)

		# Apply custom enabled tools if provided (scaffold-specific)
		if custom_enabled_tools is not None:
			enabled_tools = custom_enabled_tools & all_available_tools
			self.logger.debug(f"[MCPManager] Applied custom enabled_tools: {sorted(custom_enabled_tools)}")
		# Otherwise apply task configuration filter
		else:
			task_config = self.config.task_config
			if task_config.enabled_tools is not None:
				enabled_tools = set(task_config.enabled_tools) & all_available_tools
				self.logger.debug(f"[MCPManager] Applied enabled_tools filter: {sorted(task_config.enabled_tools)}")
			elif task_config.disabled_tools is not None:
				enabled_tools = all_available_tools - set(task_config.disabled_tools)
				self.logger.debug(f"[MCPManager] Applied disabled_tools filter: {sorted(task_config.disabled_tools)}")
			else:
				enabled_tools = all_available_tools

		self.logger.info(f"[MCPManager] Enabled tools ({len(enabled_tools)}): {sorted(enabled_tools)}")
		return enabled_tools

	def _configure_fastmcp_logger(self) -> None:
		"""Configure FastMCP logger to output to file instead of console."""
		for logger_name in ["FastMCP", "fastmcp", "fastmcp.tools", "fastmcp.tools.tool_manager", "mcp"]:
			fmcp_logger = logging.getLogger(logger_name)
			fmcp_logger.propagate = False
			fmcp_logger.setLevel(logging.WARNING)

			# Remove all existing handlers
			for h in list(fmcp_logger.handlers):
				fmcp_logger.removeHandler(h)

			# Add file handler if available
			if self.logger.logger.handlers:
				file_handler = logging.FileHandler(
					self.logger.logger.handlers[0].baseFilename,
					encoding="utf-8"
				)
				file_handler.setFormatter(logging.Formatter(
					"%(asctime)s | %(levelname)-8s | %(name)s - %(message)s"
				))
				fmcp_logger.addHandler(file_handler)

	def _configure_uvicorn_logger(self) -> None:
		"""Configure uvicorn logger to output to our log file."""
		for logger_name in ["uvicorn", "uvicorn.error", "uvicorn.access"]:
			uvicorn_logger = logging.getLogger(logger_name)
			uvicorn_logger.propagate = False
			uvicorn_logger.setLevel(logging.ERROR)  # Only capture errors

			# Remove existing handlers
			for h in list(uvicorn_logger.handlers):
				uvicorn_logger.removeHandler(h)

			# Add file handler if available
			if self.logger.logger.handlers:
				file_handler = logging.FileHandler(
					self.logger.logger.handlers[0].baseFilename,
					encoding="utf-8"
				)
				file_handler.setFormatter(logging.Formatter(
					"%(asctime)s | %(levelname)-8s | [uvicorn] %(message)s"
				))
				uvicorn_logger.addHandler(file_handler)

	def _bind_tools_to_server(self, enabled_tools: Set[str]) -> None:
		"""
		Bind tools to MCP server and store tool instances.

		This method:
		1. Creates tool provider instances based on enabled tools
		2. Syncs tool_instances to all providers after all are created
		3. Registers tools to the MCP server
		4. Stores instances in self.tool_instances for cleanup

		Args:
			enabled_tools: Set of enabled tool names
		"""
		# Phase 1: Construct all tool instances
		processed_tool_classes = set()

		for tool_name, tool_class in list_registered_tools().items():
			# Avoid processing the same tool class more than once
			if tool_class in processed_tool_classes:
				continue

			# Check whether this class has any enabled tools
			supported_tools = tool_class.SUPPORTED_TOOLS
			tools_needed = any(tool in enabled_tools for tool in supported_tools)

			if tools_needed:
				try:
					# Create tool instance (without tool_instances parameter)
					tool_instance = tool_class(
						task=self.task,
						config=self.config,
						logger=self.logger,
						confirmation_bridge=self.confirmation_bridge,
						is_cli_mode=self.is_cli_mode,
					)

					# Store instance in dictionary (by class type)
					self.tool_instances[tool_class] = tool_instance

					self.logger.info(f"Constructed {tool_class.__name__} for tools: {[t for t in supported_tools if t in enabled_tools]}")

				except Exception as e:
					self.logger.error(f"Failed to construct {tool_class.__name__}: {e}")
					raise

				processed_tool_classes.add(tool_class)

		# Phase 2: Sync tool_instances to all providers (now that all are created)
		for tool_class, tool_instance in self.tool_instances.items():
			try:
				tool_instance.sync_tool_instances(self.tool_instances)
				self.logger.debug(f"Synced tool_instances to {tool_class.__name__}")
			except Exception as e:
				self.logger.error(f"Failed to sync tool_instances to {tool_class.__name__}: {e}")
				raise

		# Phase 3: Register all tools to MCP server
		for tool_class, tool_instance in self.tool_instances.items():
			try:
				# Register the tool with the MCP server
				tool_instance.register_tools(self.mcp_server, enabled_tools)

				supported_tools = tool_class.SUPPORTED_TOOLS
				self.logger.info(f"Successfully registered {tool_class.__name__} for tools: {[t for t in supported_tools if t in enabled_tools]}")

			except Exception as e:
				self.logger.error(f"Failed to register {tool_class.__name__}: {e}")
				raise

	async def setup_direct_mode(self, custom_enabled_tools: Optional[Set[str]] = None) -> None:
		"""
		Set up MCP in direct mode (FastMCP + Client).

		This mode uses in-process communication between FastMCP server and Client.
		Suitable for scaffolds that need direct access to MCP client.

		Args:
			custom_enabled_tools: Optional custom tool set (otherwise uses config)

		Raises:
			ComponentSetupError: If setup fails
		"""
		if self._mode is not None:
			raise ComponentSetupError(f"MCPManager already set up in {self._mode} mode")

		try:
			self._configure_fastmcp_logger()

			# Create MCP server
			instance_name = f"ape-agent--{self.task.data.task_id}"
			self.mcp_server = FastMCP(instance_name)

			# Calculate and bind tools (stores instances in self.tool_instances)
			enabled_tools = self.calculate_enabled_tools(custom_enabled_tools)
			self._bind_tools_to_server(enabled_tools)

			# Register task-specific tools
			await self.task.register_task_tools(self.mcp_server)

			# Create MCP client
			mcp_log_handler = create_mcp_log_handler(self.logger)
			self.mcp_client = Client(self.mcp_server, log_handler=mcp_log_handler)
			await self.mcp_client.__aenter__()

			self._mode = 'direct'
			self.logger.info(f"[MCPManager] Direct mode setup complete, tools: {sorted(enabled_tools)}")

		except Exception as e:
			await self._cleanup_partial()
			raise ComponentSetupError(f"Failed to setup MCP direct mode: {e}") from e

	async def setup_http_mode(self, custom_enabled_tools: Optional[Set[str]] = None) -> None:
		"""
		Set up MCP in HTTP mode (FastMCP HTTP server) with retry mechanism.

		This mode starts FastMCP as an HTTP server for network communication.
		Includes retry logic to handle transient failures.

		Args:
			custom_enabled_tools: Optional custom tool set (otherwise uses config)

		Raises:
			ComponentSetupError: If setup fails after all retries
		"""
		if self._mode is not None:
			raise ComponentSetupError(f"MCPManager already set up in {self._mode} mode")

		max_retries = 3
		last_error = None

		for attempt in range(max_retries):
			try:
				self.logger.info(
					f"[MCPManager] Starting MCP HTTP mode setup "
					f"(attempt {attempt + 1}/{max_retries})"
				)

				# Try to set up server once
				await self._setup_http_mode_once(custom_enabled_tools, attempt)

				# Success!
				self.logger.info(
					f"[MCPManager] HTTP mode setup succeeded on attempt {attempt + 1}"
				)
				return

			except Exception as e:
				last_error = e
				self.logger.warning(
					f"[MCPManager] MCP HTTP setup failed on attempt {attempt + 1}/{max_retries}: "
					f"{type(e).__name__}: {e}"
				)

				# Cleanup before retry
				await self._cleanup_partial()

				if attempt < max_retries - 1:
					wait_time = 1.0 * (attempt + 1)  # Exponential backoff
					self.logger.info(f"[MCPManager] Waiting {wait_time:.1f}s before retry...")
					await asyncio.sleep(wait_time)
				else:
					# Last attempt failed
					self.logger.error(
						f"[MCPManager] MCP HTTP setup failed after {max_retries} attempts"
					)

		# All retries exhausted
		raise ComponentSetupError(
			f"Failed to setup MCP HTTP mode after {max_retries} attempts: {last_error}"
		) from last_error

	async def _setup_http_mode_once(
		self,
		custom_enabled_tools: Optional[Set[str]],
		attempt_number: int
	) -> None:
		"""
		Single attempt to set up MCP HTTP mode.

		Args:
			custom_enabled_tools: Optional custom tool set
			attempt_number: Current attempt number (for logging)

		Raises:
			Exception: If setup fails
		"""
		# Configure logging
		self._configure_fastmcp_logger()
		self._configure_uvicorn_logger()

		# Create MCP server
		server_name = f"lean-research--{self.task.data.task_id}"
		self.mcp_server = FastMCP(server_name)

		# Calculate and bind tools
		enabled_tools = self.calculate_enabled_tools(custom_enabled_tools)
		self._bind_tools_to_server(enabled_tools)

		# Register task-specific tools
		await self.task.register_task_tools(self.mcp_server)

		# Allocate port (use different port on retry)
		self._server_port = _allocate_port()
		self.logger.debug(
			f"[MCPManager] Allocated port {self._server_port} for attempt {attempt_number + 1}"
		)

		# Create HTTP app (for path computation) and start server via FastMCP
		app = self.mcp_server.http_app(transport="http")
		self.http_server_task = asyncio.create_task(
			self.mcp_server.run_async(
				transport="http",
				show_banner=False,
				host="127.0.0.1",
				port=self._server_port,
				log_level="error",
				uvicorn_config={
					"access_log": False,
					"timeout_graceful_shutdown": 0,
					"lifespan": "on",
				},
			)
		)

		# Build server URL
		path = app.state.path or ""
		if path and not path.startswith("/"):
			path = f"/{path}"
		self._server_url = f"http://127.0.0.1:{self._server_port}{path}"

		self.logger.debug(f"[MCPManager] Server URL: {self._server_url}")

		# Wait for server to start and verify endpoint
		await self._wait_for_http_server_ready(timeout=30.0)

		# Mark as ready
		self._mode = 'http'
		self.logger.info(
			f"[MCPManager] HTTP mode setup complete, "
			f"URL: {self._server_url}, tools: {sorted(enabled_tools)}"
		)

	async def _wait_for_http_server_ready(self, timeout: float = 10.0) -> None:
		"""Wait for MCP HTTP server to be ready and verify direct + HTTP connectivity."""
		start_time = asyncio.get_event_loop().time()
		uvicorn_started = False

		self.logger.debug(
			f"[MCPManager] Waiting for MCP HTTP server ready "
			f"(URL: {self._server_url}, timeout: {timeout}s)"
		)

		while True:
			current_time = asyncio.get_event_loop().time()
			elapsed = current_time - start_time

			if elapsed > timeout:
				raise ComponentSetupError(
					f"MCP HTTP server failed to start within {timeout} seconds "
					f"(uvicorn_started={uvicorn_started})"
				)

			# Check if server task failed
			if self.http_server_task.done():
				try:
					self.http_server_task.result()
				except Exception as e:
					self.logger.error(
						f"[MCPManager] HTTP server task failed after {elapsed:.2f}s: "
						f"{type(e).__name__}: {e}"
					)
					raise ComponentSetupError(f"HTTP server task failed: {e}") from e

			if not uvicorn_started:
				if self.mcp_server and self.mcp_server._started.is_set():
					self.logger.debug(
						f"[MCPManager] MCP server started (took {elapsed:.2f}s, "
						f"port={self._server_port})"
					)
					uvicorn_started = True
				else:
					await asyncio.sleep(0.1)
					continue

			# Ensure TCP port is accepting connections before HTTP verification
			while True:
				current_time = asyncio.get_event_loop().time()
				if current_time - start_time > timeout:
					raise ComponentSetupError(
						f"MCP HTTP server failed to open port within {timeout} seconds "
						f"(uvicorn_started={uvicorn_started})"
					)
				try:
					reader, writer = await asyncio.wait_for(
						asyncio.open_connection("127.0.0.1", self._server_port),
						timeout=0.5,
					)
					writer.close()
					try:
						await writer.wait_closed()
					except Exception:
						pass
					break
				except Exception:
					await asyncio.sleep(0.1)
			# Stage 2: Direct in-process verification
			try:
				async def _verify_direct():
					async with Client(self.mcp_server) as client:
						return await client.list_tools()

				direct_tools = await asyncio.wait_for(_verify_direct(), timeout=5.0)
				self.logger.info(
					f"[MCPManager] Direct MCP verification OK "
					f"(found {len(direct_tools)} tools)"
				)
			except Exception as e:
				raise ComponentSetupError(
					f"Direct MCP verification failed: {type(e).__name__}: {e}"
				) from e

			# Stage 3: HTTP verification
			try:
				async def _verify_http():
					async with Client(self._server_url) as client:
						return await client.list_tools()

				http_tools = await asyncio.wait_for(_verify_http(), timeout=10.0)
				self.logger.info(
					f"[MCPManager] HTTP MCP verification OK "
					f"(found {len(http_tools)} tools)"
				)
				return
			except Exception as e:
				raise ComponentSetupError(
					f"HTTP MCP verification failed: {type(e).__name__}: {e}"
				) from e

	def get_client(self) -> Optional[Client]:
		"""
		Get MCP client (direct mode only).

		Returns:
			MCP Client instance or None if not in direct mode

		Raises:
			RuntimeError: If called before setup or in HTTP mode
		"""
		if self._mode is None:
			raise RuntimeError("MCPManager not set up. Call setup_direct_mode() or setup_http_mode() first")
		if self._mode != 'direct':
			raise RuntimeError(f"get_client() only available in direct mode, current mode: {self._mode}")
		return self.mcp_client

	def get_server_url(self) -> Optional[str]:
		"""
		Get HTTP server URL (HTTP mode only).

		Returns:
			Server URL or None if not in HTTP mode

		Raises:
			RuntimeError: If called before setup or in direct mode
		"""
		if self._mode is None:
			raise RuntimeError("MCPManager not set up. Call setup_direct_mode() or setup_http_mode() first")
		if self._mode != 'http':
			raise RuntimeError(f"get_server_url() only available in HTTP mode, current mode: {self._mode}")
		return self._server_url

	async def _cleanup_partial(self) -> None:
		"""Clean up partial setup (called on setup failure before retry)."""
		self.logger.debug("[MCPManager] Starting partial cleanup...")

		# Clean up tool instances
		for tool_class, tool_instance in self.tool_instances.items():
			try:
				await tool_instance.cleanup()
				self.logger.debug(f"[MCPManager] Cleaned up tool provider: {tool_class.__name__}")
			except Exception as e:
				self.logger.warning(
					f"[MCPManager] Error cleaning tool provider {tool_class.__name__}: {e}"
				)

		# Clean up client
		if self.mcp_client:
			try:
				await self.mcp_client.__aexit__(None, None, None)
				self.logger.debug("[MCPManager] Cleaned up MCP client")
			except Exception as e:
				self.logger.warning(f"[MCPManager] Error cleaning MCP client: {e}")

		# Clean up HTTP server task
		if self.http_server_task:
			if not self.http_server_task.done():
				self.logger.debug(
					f"[MCPManager] Stopping HTTP server (port={self._server_port})..."
				)
				self.http_server_task.cancel()
				try:
					await asyncio.wait_for(self.http_server_task, timeout=2.0)
					self.logger.debug("[MCPManager] HTTP server stopped")
				except (asyncio.CancelledError, asyncio.TimeoutError):
					self.logger.debug("[MCPManager] HTTP server stop timeout/cancelled")
			else:
				self.logger.debug("[MCPManager] HTTP server task already done")

		# Clear state
		self.tool_instances = {}
		self.mcp_server = None
		self.mcp_client = None
		self.http_server_task = None
		self._http_server = None
		self._server_port = None
		self._server_url = None

		self.logger.debug("[MCPManager] Partial cleanup completed")
		self._http_server = None
		self._server_port = None
		self._server_url = None
		self._mode = None

	async def cleanup(self) -> None:
		"""
		Clean up all MCP resources.

		This method:
		1. Cleans up all tool provider instances (e.g., browser sessions)
		2. Cleans up MCP client (direct mode)
		3. Stops HTTP server (HTTP mode)
		4. Clears all state

		Safe to call multiple times.
		"""
		if self._mode is None:
			return

		self.logger.info(f"[MCPManager] Starting cleanup (mode: {self._mode})...")

		# 1. Clean up tool instances first (they may have active resources like browser sessions)
		if self.tool_instances:
			for tool_class, tool_instance in self.tool_instances.items():
				try:
					await tool_instance.cleanup()
					self.logger.debug(f"[MCPManager] Tool provider {tool_class.__name__} cleaned up")
				except Exception as e:
					self.logger.warning(f"[MCPManager] Error cleaning tool provider {tool_class.__name__}: {e}")

		# 2. Clean up MCP client (direct mode)
		if self.mcp_client:
			try:
				await self.mcp_client.__aexit__(None, None, None)
				self.logger.debug("[MCPManager] MCP client cleaned up")
			except Exception as e:
				self.logger.warning(f"[MCPManager] Error cleaning MCP client: {e}")

		# 3. Stop HTTP server (HTTP mode)
		if self.http_server_task:
			try:
				# Give brief moment for pending requests
				await asyncio.sleep(0.5)

				if not self.http_server_task.done():
					try:
						await asyncio.wait_for(self.http_server_task, timeout=3.0)
					except asyncio.TimeoutError:
						self.http_server_task.cancel()
						try:
							await asyncio.wait_for(self.http_server_task, timeout=2.0)
						except asyncio.CancelledError:
							pass
						except asyncio.TimeoutError:
							self.logger.warning("[MCPManager] HTTP server task cancellation timed out")
					except asyncio.CancelledError:
						pass
					except Exception as e:
						# Suppress "Task group is not initialized" errors during shutdown
						if "Task group is not initialized" not in str(e):
							raise

				self.logger.debug("[MCPManager] HTTP server stopped")

			except Exception as e:
				# Suppress "Task group is not initialized" errors during shutdown
				if "Task group is not initialized" in str(e):
					self.logger.debug(f"[MCPManager] Suppressed shutdown error: {e}")
				else:
					self.logger.warning(f"[MCPManager] Error stopping HTTP server: {e}")

		# 4. Clear all state
		self.tool_instances = {}
		self.mcp_server = None
		self.mcp_client = None
		self.http_server_task = None
		self._http_server = None
		self._server_port = None
		self._server_url = None
		mode = self._mode
		self._mode = None

		self.logger.info(f"[MCPManager] Cleanup complete (was in {mode} mode)")

	@property
	def is_setup(self) -> bool:
		"""Check if manager is set up."""
		return self._mode is not None

	@property
	def mode(self) -> Optional[str]:
		"""Get current mode ('direct', 'http', or None)."""
		return self._mode
