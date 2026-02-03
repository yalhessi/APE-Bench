"""
Simplified snapshot manager - new simplified snapshot system
"""

import struct
import io
from pathlib import Path
from typing import Dict, List, Optional, TYPE_CHECKING

import aiofiles
import aiofiles.os
from ..config import LeanVerifyToolConfig
from ape.utils.file_ops import atomic_write
from ape.utils.logging import create_logger

if TYPE_CHECKING:
    import logging

class SnapshotManager:
    """Simplified snapshot manager"""

    def __init__(self, config: Optional[LeanVerifyToolConfig] = None, logger: Optional['logging.LoggerAdapter'] = None, repo_name: str = "mathlib4"):
        """Initialize snapshot manager

        Args:
            config: Configuration object
            logger: Logger
            repo_name: Repository name, default is mathlib4 (backward compatibility)
        """
        self.config = config or LeanVerifyToolConfig()
        self.logger = logger or create_logger()
        self.repo_name = repo_name

        self.snapshot_dir = self.config.get_snapshot_dir(repo_name)
        # Note: Do not create directory during initialization, create it asynchronously when needed

        self.logger.info(f"Snapshot manager initialized [{repo_name}]: {self.snapshot_dir}")
    
    async def store_snapshot(self, workspace_id: str, file_mappings: Dict[str, Dict[str, str]]) -> None:
        """Asynchronously store workspace snapshot - using binary format
        
        Args:
            workspace_id: Workspace ID
            file_mappings: File mapping {relative path: {"hash": hash, "type": type}}
        """
        await aiofiles.os.makedirs(self.snapshot_dir, exist_ok=True)
        snapshot_path = self.snapshot_dir / f"{workspace_id}.snap"
        
        try:
            # Use BytesIO to build binary data, improve efficiency
            buffer = io.BytesIO()
            
            # Filter and validate data
            valid_records = []
            for rel_path, file_info in file_mappings.items():
                path_bytes = rel_path.encode('utf-8')
                path_len = len(path_bytes)
                
                if path_len > 65535:  # Exceeds unsigned short integer maximum value
                    self.logger.error(f"Path too long: {rel_path}")
                    continue
                
                # Validate and convert hash
                try:
                    hash_bin = bytes.fromhex(file_info["hash"])
                    if len(hash_bin) != 32:  # SHA-256 is 32 bytes
                        self.logger.error(f"Invalid hash length {rel_path}: {file_info['hash']}")
                        continue
                except ValueError:
                    self.logger.error(f"Invalid hash format {rel_path}: {file_info['hash']}")
                    continue
                
                # File type encoding
                file_type_code = 1 if file_info["type"] == "symlink" else 0
                
                valid_records.append((path_len, hash_bin, file_type_code, path_bytes))
            
            # Write record count
            buffer.write(struct.pack('!I', len(valid_records)))
            
            # Write all valid records
            for path_len, hash_bin, file_type_code, path_bytes in valid_records:
                buffer.write(struct.pack('!H32sB', path_len, hash_bin, file_type_code))
                buffer.write(path_bytes)
            
            # Atomic write
            await atomic_write(snapshot_path, buffer.getvalue(), encoding=None)
            
            self.logger.info(f"Store snapshot {workspace_id}: {len(valid_records)} files")
            
        except Exception as e:
            raise RuntimeError(f"Store snapshot failed {workspace_id}: {e}")
    
    async def load_snapshot(self, workspace_id: str) -> Optional[Dict[str, Dict[str, str]]]:
        """Load a workspace snapshot with a single bulk read for performance.
        
        Args:
            workspace_id: Workspace ID
            
        Returns:
            Optional[Dict]: File mapping, or None if the snapshot does not exist.
        """
        snapshot_path = self.snapshot_dir / f"{workspace_id}.snap"
        
        if not await aiofiles.os.path.exists(snapshot_path):
            self.logger.debug(f"Snapshot does not exist: {workspace_id}")
            return None
        
        try:
            # Read entire snapshot file into memory at once
            async with aiofiles.open(snapshot_path, 'rb') as f:
                data = await f.read()
            
            if len(data) < 4:
                raise ValueError("Invalid snapshot file")
            
            # Parse in memory
            file_mappings = {}
            offset = 0
            
            # Read record count
            record_count = struct.unpack('!I', data[offset:offset+4])[0]
            offset += 4
            self.logger.debug(f"Load snapshot {workspace_id}: {record_count} records")
            
            # Parse all records
            for i in range(record_count):
                # Check if there is enough data to read record header
                if offset + 35 > len(data):
                    self.logger.error(f"Snapshot record {i} is incomplete")
                    break
                
                # Read record header: path length + hash + type
                path_len, hash_bin, file_type_code = struct.unpack('!H32sB', data[offset:offset+35])
                offset += 35
                
                # Check if there is enough data to read path
                if offset + path_len > len(data):
                    self.logger.error(f"Snapshot record {i} path data is incomplete")
                    break
                
                # Read path
                path_data = data[offset:offset+path_len]
                offset += path_len
                
                try:
                    rel_path = path_data.decode('utf-8')
                except UnicodeDecodeError:
                    self.logger.error(f"Snapshot record {i} path encoding is invalid")
                    continue
                
                # Convert data
                file_hash = hash_bin.hex()
                file_type = "symlink" if file_type_code == 1 else "regular"
                
                file_mappings[rel_path] = {
                    "hash": file_hash,
                    "type": file_type
                }
            
            self.logger.info(f"Load snapshot {workspace_id}: {len(file_mappings)} files")
            return file_mappings
            
        except Exception as e:
            raise RuntimeError(f"Load snapshot failed {workspace_id}: {e}")
    
