"""
Verification engine - new simplified verification system
"""

import json
import shutil
from datetime import datetime
from typing import Optional, Dict, Any, List, TYPE_CHECKING
from pathlib import Path

from ..config import LeanVerifyToolConfig
from ..models import LeanMessage, VerificationResult
from ..utils.process_ops import temporary_file, run_command
from ..utils.error_enhancement import enhance_module_not_found_error
from ape.utils.logging import create_logger

if TYPE_CHECKING:
    import logging

def parse_lean_output(code: str, raw_output: str, raw_stderr: str, return_code: int, working_dir: Optional[Path] = None) -> VerificationResult:
    """Parse Lean output to verification result"""
    try:
        # Parse JSON output (each line is a JSON object)
        json_lines = [line.strip() for line in raw_output.strip().split('\n') if line.strip()]
        json_data = []
        for line in json_lines:
            try:
                json_data.append(json.loads(line))
            except json.JSONDecodeError:
                # Skip non-JSON lines
                continue
    except Exception:
        json_data = []
    
    messages = []
    errors = []
    warnings = []
    infos = []
    axioms = []
    
    code_lines = code.split('\n')
    
    # Parse messages
    for msg in json_data:
        try:
            line_num = msg.get('pos', {}).get('line', 1)
            code_line = code_lines[line_num - 1] if 1 <= line_num <= len(code_lines) else None
        except (KeyError, IndexError, TypeError):
            code_line = None
        
        error_data = msg.get('data', '')
        
        # Enhance error message
        if msg.get('severity') == 'error' and working_dir:
            error_data = enhance_module_not_found_error(error_data, working_dir)
        
        lean_msg = LeanMessage(
            severity=msg.get('severity', 'info'),
            data=error_data,
            code_line=code_line,
            pos=msg.get('pos'),
            end_pos=msg.get('endPos')
        )
        
        messages.append(lean_msg)
        
        # Classify messages
        if lean_msg.severity == 'error':
            errors.append(lean_msg)
        elif lean_msg.severity == 'warning':
            warnings.append(lean_msg)
        elif lean_msg.severity in ['info', 'information']:
            infos.append(lean_msg)
            
            # Extract axioms information
            if 'axioms' in lean_msg.data.lower():
                axioms.extend(_extract_axioms_from_message(lean_msg.data))
    
    # Determine success status
    success = return_code == 0 and len(errors) == 0
    
    return VerificationResult(
        success=success,
        messages=messages,
        errors=errors,
        warnings=warnings,
        infos=infos,
        axioms=list(set(axioms)),
        raw_output=raw_output,
        raw_stderr=raw_stderr,
        return_code=return_code
    )

def _extract_axioms_from_message(message: str) -> List[str]:
    """
    Extract axioms names from Lean's #print axioms output
    
    #print axioms output format:
    'foo' depends on axioms: [propext, Classical.choice, Quot.sound]
    or:
    'foo' does not depend on any axioms
    """
    axioms = []
    
    lines = message.split('\n')
    for line in lines:
        line = line.strip()
        
        # Match "depends on axioms: [...]" format
        if 'depends on axioms:' in line.lower():
            # Extract content in square brackets
            import re
            match = re.search(r'\[([^\]]+)\]', line)
            if match:
                axiom_list = match.group(1)
                # Split and clean each axiom name
                for axiom in axiom_list.split(','):
                    axiom = axiom.strip()
                    if axiom:
                        axioms.append(axiom)
    
    return axioms

def _add_print_axioms_commands(code: str) -> str:
    """
    Add #print axioms commands at the end of the code to get all axioms used by theorems
    
    Parse code to get all declaration names, then add print commands for each declaration
    """
    from ape.toolkits.code.lean.lean_parser import parse_major_declarations
    
    try:
        decls = parse_major_declarations(code)
        
        # Collect all declarations with names (theorem, lemma, def, etc.)
        names = []
        for decl in decls:
            if decl.name:
                names.append(decl.name)
        
        # Add print commands at the end of the code
        if names:
            print_commands = '\n\n'.join(f'#print axioms {name}' for name in names)
            return code + '\n\n' + print_commands
        else:
            return code
            
    except Exception:
        # Return original code if parsing fails (does not affect verification)
        return code

class VerificationEngine:
    """Simplified Lean code verification engine"""
    
    def __init__(self, config: Optional[LeanVerifyToolConfig] = None, logger: Optional['logging.LoggerAdapter'] = None):
        """Initialize verification engine"""
        self.config = config or LeanVerifyToolConfig()
        self.logger = logger or create_logger()
        
        self.logger.debug("Verification engine initialized")
    
    async def verify(
        self, 
        code: str,
        working_dir: Optional[Path] = None,
        timeout: Optional[float] = None,
        max_memory_gb: Optional[float] = None,
        allow_sorries: Optional[bool] = None,
        accepted_axioms: Optional[List[str]] = None,
        nproc: Optional[int] = None,
        options: Optional[Dict[str, Any]] = None,
        print_axioms: Optional[bool] = None,  # NEW parameter
    ) -> VerificationResult:
        """Verify Lean code
        
        Args:
            code: Lean code to verify
            working_dir: Working directory (Path object, for dependency resolution)
            timeout: Verification timeout (seconds)
            max_memory_gb: Maximum memory usage (GB)
            allow_sorries: Whether to allow sorry placeholder
            accepted_axioms: Accepted axioms list
            nproc: Number of parallel processes
            options: Lean options configuration
            print_axioms: Whether to print axioms (None uses config default value)
            
        Returns:
            VerificationResult: Verification result
        """
        start_time = datetime.now()
        
        try:
            # Verify input
            if not code or not code.strip():
                raise ValueError("Code cannot be empty")
            
            if working_dir and not working_dir.exists():
                raise ValueError(f"Working directory does not exist: {working_dir}")
            
            # Use config default values
            actual_timeout = timeout if timeout is not None else self.config.timeout
            actual_max_memory_gb = max_memory_gb if max_memory_gb is not None else self.config.max_memory_gb
            actual_allow_sorries = allow_sorries if allow_sorries is not None else self.config.allow_sorries
            actual_accepted_axioms = accepted_axioms if accepted_axioms is not None else self.config.accepted_axioms
            actual_print_axioms = print_axioms if print_axioms is not None else self.config.print_axioms
            
            # Prepare verification options
            lean_options = self.config.lean_options.copy()
            if options:
                lean_options.update(options)
            
            self.logger.debug(f"Start verification, timeout: {actual_timeout}s, working directory: {working_dir or 'default'}")
            
            # Execute verification
            result = await self._verify_with_temp_file(
                code, lean_options, actual_timeout, working_dir,
                actual_max_memory_gb, nproc, actual_print_axioms
            )
            
            execution_time = (datetime.now() - start_time).total_seconds()
            result.execution_time = execution_time
            
            # Validate axioms and sorries
            result = self._validate_axioms_and_sorries(result, actual_accepted_axioms, actual_allow_sorries)
            
            self.logger.debug(f"Verification completed, time: {execution_time:.2f}s")
            return result
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            self.logger.error(f"Verification failed, time: {execution_time:.2f}s: {e}")
            
            # For specific exceptions, raise directly
            if isinstance(e, (ValueError, TimeoutError)):
                raise
            
            # Create error result
            return VerificationResult(
                success=False,
                messages=[],
                errors=[],
                warnings=[],
                infos=[],
                axioms=[],
                execution_time=execution_time,
                raw_output="",
                raw_stderr=str(e),
                return_code=-1
            )
    
    async def _verify_with_temp_file(
        self, 
        code: str, 
        lean_options: Dict[str, Any], 
        timeout: float, 
        working_dir: Optional[Path] = None,
        max_memory_gb: Optional[float] = None,
        nproc: Optional[int] = None,
        print_axioms: bool = False  # NEW parameter
    ) -> VerificationResult:
        """Use temporary file to verify code"""
        
        # Based on parameter, decide whether to add #print axioms command
        code_to_verify = _add_print_axioms_commands(code) if print_axioms else code
        
        # Use temporary file
        with temporary_file(code_to_verify, suffix=".lean") as temp_file:
            return await self._run_lean_verification(
                code, temp_file, lean_options, timeout, 
                working_dir, max_memory_gb, nproc
            )
    
    async def _run_lean_verification(
        self, 
        code: str, 
        lean_file: Path, 
        lean_options: Dict[str, Any], 
        timeout: float, 
        working_dir: Optional[Path] = None,
        max_memory_gb: Optional[float] = None, 
        nproc: Optional[int] = None
    ) -> VerificationResult:
        """Run Lean verification"""
        lean_file_path = lean_file
        
        # Build command - check if stdbuf exists
        if shutil.which("stdbuf"):
            command = ["stdbuf", "-oL", "-eL", "lake", "env", 'lean']
        else:
            # On macOS etc., stdbuf may not exist, use lake env lean directly
            command = ["lake", "env", 'lean']
        
        # Add options
        for key, value in lean_options.items():
            command.extend(["-D", f"{key}={value}"])
        
        # Add file and JSON output
        command.extend(["--json", str(lean_file_path)])
        
        self.logger.debug(f"Run command: {' '.join(command)} in directory {working_dir or 'default'}")
        
        try:
            # Execute command (if timeout, return returncode=-15 and collected output)
            stdout, stderr, return_code = await run_command(
                command,
                cwd=working_dir,
                timeout=timeout,
                max_memory_gb=max_memory_gb,
                nproc=nproc,
                logger=self.logger
            )
            
            # Parse output (even if timeout, can parse collected output)
            result = parse_lean_output(code, stdout, stderr, return_code, working_dir)
            
            # If timeout exit, record log
            if return_code == -15:
                self.logger.warning(f"Lean verification timeout ({timeout}s), {len(result.messages)} messages collected")
            else:
                self.logger.debug(f"Lean command completed, return code: {return_code}")
            
            return result
            
        except Exception as e:
            raise RuntimeError(f"Lean execution failed: {e}")
    
    def _validate_axioms_and_sorries(
        self, 
        result: VerificationResult, 
        accepted_axioms: List[str], 
        allow_sorries: bool
    ) -> VerificationResult:
        """Validate used axioms and sorries"""
        if not result.success:
            return result
        
        errors = list(result.errors)
        
        # Check sorries
        if not allow_sorries:
            for msg in result.messages:
                if 'sorry' in msg.data.lower():
                    errors.append(LeanMessage(
                        severity='error',
                        data='Sorries are not allowed'
                    ))
                    break
        
        # Check axioms
        accepted_set = set(accepted_axioms)
        forbidden_axioms = [axiom for axiom in result.axioms if axiom not in accepted_set]
        
        if forbidden_axioms:
            error_msg = f"Forbidden axioms used: {', '.join(forbidden_axioms)}"
            errors.append(LeanMessage(
                severity='error',
                data=error_msg
            ))
        
        # If there are new errors, update result
        if len(errors) > len(result.errors):
            return VerificationResult(
                success=False,
                messages=result.messages,
                errors=errors,
                warnings=result.warnings,
                infos=result.infos,
                axioms=result.axioms,
                execution_time=result.execution_time,
                raw_output=result.raw_output,
                raw_stderr=result.raw_stderr,
                return_code=result.return_code
            )
        
        return result
