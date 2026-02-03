"""
Error message enhancement tool - redesigned to provide more precise and helpful hints
"""

import re
from pathlib import Path
from typing import Optional, List, Tuple
from difflib import get_close_matches


def enhance_module_not_found_error(error_msg: str, working_dir: Path) -> str:
    """Enhance module not found error, provide precise diagnosis and suggestions
    
    Handle error pattern: "object file ... of module X does not exist"
    
    Provide precise diagnosis information:
    1. Clearly indicate the file path the user attempted to import
    2. Diagnose problems:
       - File does not exist
       - Parent directory is a file (not a directory) (user added an extra level)
       - Parent directory does not exist
       - Parent directory exists but file is not in it
    3. Provide feasible solutions:
       - List available modules in the parent directory
       - Provide suggestions for similar module names
       - Suggest correct import path
    """
    # Match module name in error message
    match = re.search(r"of module (\S+) does not exist", error_msg)
    if not match:
        return error_msg
    
    module_name = match.group(1)
    parts = module_name.split('.')
    
    if not parts:
        return error_msg
    
    # Build file path
    file_path = working_dir / Path(*parts).with_suffix('.lean')
    file_path_str = '/'.join(parts) + '.lean'
    
    # Start diagnosis
    hints = []
    hints.append(f"\n{'='*60}")
    hints.append(f"IMPORT ERROR DIAGNOSIS: {module_name}")
    hints.append(f"{'='*60}")
    hints.append(f"ATTEMPTED: {file_path_str}")
    
    # Check full path
    if file_path.exists() and file_path.is_file():
        # File exists but still error
        # Check if both file and directory with the same name exist (user may want to access modules in the directory)
        dir_path = file_path.with_suffix('')
        if dir_path.exists() and dir_path.is_dir():
            # Both file and directory with the same name exist, hint user may want to access modules in the directory
            hints.append(f"\nFOUND: Both {module_name}.lean (file) and {module_name}/ (directory) exist")
            
            try:
                lean_files = sorted([f.stem for f in dir_path.glob('*.lean') 
                                    if f.is_file() and not f.stem.startswith('.')])
                if lean_files:
                    hints.append(f"\nAVAILABLE MODULES in {module_name}/:")
                    for i, file_stem in enumerate(lean_files[:10], 1):
                        hints.append(f"  {i}. {module_name}.{file_stem}")
                    if len(lean_files) > 10:
                        hints.append(f"  ... and {len(lean_files) - 10} more")
            except Exception:
                pass
            
            hints.append(f"\nNOTE: If you want the file itself, run 'lake build {module_name}' to compile it")
            return error_msg + '\n' + '\n'.join(hints)
        else:
            # Only file, no directory with the same name
            hints.append(f"\nSTATUS: File exists but .olean object file is missing")
            hints.append(f"SOLUTION: Run 'lake build {module_name}' to compile this module")
            return error_msg + '\n' + '\n'.join(hints)
    
    # File does not exist, start detailed diagnosis
    hints.append(f"\nSTATUS: File does not exist")
    
    # Check parent directory situation
    if len(parts) > 1:
        parent_parts = parts[:-1]
        parent_dir = working_dir / Path(*parent_parts)
        parent_module = '.'.join(parent_parts)
        filename = parts[-1]
        
        # Situation 1: Check parent path
        parent_file = parent_dir.with_suffix('.lean')
        parent_file_exists = parent_file.exists() and parent_file.is_file()
        parent_dir_exists = parent_dir.exists() and parent_dir.is_dir()
        
        # If parent path is only a file (no directory with the same name), user is trying to access sub-modules of the file
        if parent_file_exists and not parent_dir_exists:
            hints.append(f"\nFOUND: {parent_module} is a Lean file (not a directory)")
            hints.append(f"REASON: Lean files cannot have sub-modules")
            hints.append(f"SOLUTION: Use 'import {parent_module}' instead")
            return error_msg + '\n' + '\n'.join(hints)
        
        # Situation 2: Parent directory exists
        if parent_dir.exists() and parent_dir.is_dir():
            # First check if the name the user attempted to import exists as a subdirectory
            target_subdir = parent_dir / filename
            if target_subdir.exists() and target_subdir.is_dir():
                # User attempted to import a directory, should import the specific module in the directory
                hints.append(f"\nFOUND: {module_name} is a directory (not a file)")
                hints.append(f"REASON: Cannot import a directory directly")
                
                try:
                    # List .lean files in the subdirectory
                    lean_files = sorted([f.stem for f in target_subdir.glob('*.lean') 
                                        if f.is_file() and not f.stem.startswith('.')])
                    
                    if lean_files:
                        hints.append(f"\nAVAILABLE MODULES in {module_name}/:")
                        for i, file_stem in enumerate(lean_files[:10], 1):
                            hints.append(f"  {i}. {module_name}.{file_stem}")
                        if len(lean_files) > 10:
                            hints.append(f"  ... and {len(lean_files) - 10} more")
                    else:
                        hints.append(f"\nNOTE: This directory contains no .lean files")
                except Exception:
                    pass
                
                return error_msg + '\n' + '\n'.join(hints)
            
            # filename is not a subdirectory, so the file truly does not exist
            hints.append(f"\nFOUND: Directory {'/'.join(parent_parts)}/")
            hints.append(f"MISSING: {filename}.lean does not exist in this directory")
            
            # List .lean files actually existing in the directory
            try:
                lean_files = sorted([f.stem for f in parent_dir.glob('*.lean') 
                                    if f.is_file() and not f.stem.startswith('.')])
                
                if lean_files:
                    hints.append(f"\nAVAILABLE MODULES in {parent_module}:")
                    for i, file_stem in enumerate(lean_files[:10], 1):
                        hints.append(f"  {i}. {parent_module}.{file_stem}")
                    if len(lean_files) > 10:
                        hints.append(f"  ... and {len(lean_files) - 10} more")
                    
                    # Find similar file names
                    close_matches = get_close_matches(filename, lean_files, n=3, cutoff=0.6)
                    if close_matches:
                        hints.append(f"\nSUGGESTION: Did you mean:")
                        for match in close_matches:
                            hints.append(f"  → import {parent_module}.{match}")
                
                # Check subdirectories (including checking for spelling errors)
                subdirs = sorted([d.name for d in parent_dir.iterdir() 
                                 if d.is_dir() and not d.name.startswith('.')])
                if subdirs:
                    if not lean_files:
                        hints.append(f"\nNOTE: This directory contains no .lean files")
                    hints.append(f"\nAVAILABLE SUBDIRECTORIES:")
                    for subdir in subdirs[:10]:
                        hints.append(f"  → {parent_module}.{subdir}.*")
                    if len(subdirs) > 10:
                        hints.append(f"  ... and {len(subdirs) - 10} more")
                    
                    # Find similar subdirectories
                    close_dir_matches = get_close_matches(filename, subdirs, n=3, cutoff=0.6)
                    if close_dir_matches:
                        hints.append(f"\nSUGGESTION: Did you mean subdirectory:")
                        for match in close_dir_matches:
                            hints.append(f"  → {parent_module}.{match}.*")
            except Exception:
                pass
            
            return error_msg + '\n' + '\n'.join(hints)
        
        # Situation 3: Parent directory also does not exist, continue searching upwards
        hints.append(f"\nMISSING: Parent directory {'/'.join(parent_parts)}/ also does not exist")
        
        # Search for the nearest existing directory upwards
        for i in range(len(parent_parts) - 1, 0, -1):
            ancestor_parts = parent_parts[:i]
            ancestor_dir = working_dir / Path(*ancestor_parts)
            
            if ancestor_dir.exists() and ancestor_dir.is_dir():
                ancestor_module = '.'.join(ancestor_parts)
                hints.append(f"\nFOUND: Ancestor directory {'/'.join(ancestor_parts)}/")
                
                # List available subdirectories and files
                try:
                    items = []
                    for item in sorted(ancestor_dir.iterdir()):
                        if item.name.startswith('.'):
                            continue
                        if item.is_file() and item.suffix == '.lean':
                            items.append((item.stem, 'file'))
                        elif item.is_dir():
                            items.append((item.name, 'dir'))
                    
                    if items:
                        hints.append(f"\nAVAILABLE in {ancestor_module}:")
                        for name, item_type in items[:10]:
                            if item_type == 'file':
                                hints.append(f"  • {ancestor_module}.{name} (module)")
                            else:
                                hints.append(f"  • {ancestor_module}.{name}.* (directory)")
                        if len(items) > 10:
                            hints.append(f"  ... and {len(items) - 10} more")
                        
                        # Find possible errors in the path
                        missing_part = parent_parts[i]
                        available_names = [name for name, _ in items]
                        close_matches = get_close_matches(missing_part, available_names, n=3, cutoff=0.6)
                        if close_matches:
                            hints.append(f"\nSUGGESTION: Did you mean '{missing_part}' → {', '.join(close_matches)}?")
                except Exception:
                    pass
                
                return error_msg + '\n' + '\n'.join(hints)
    
    # Situation 4: Top-level module does not exist
    hints.append(f"\nMISSING: Top-level module '{parts[0]}' does not exist in workspace")
    
    # List top-level modules in the workspace directory
    try:
        top_level = []
        for item in sorted(working_dir.iterdir()):
            if item.name.startswith('.'):
                continue
            if item.is_file() and item.suffix == '.lean':
                top_level.append(item.stem)
            elif item.is_dir():
                # Check if the directory contains .lean files
                has_lean = any(f.suffix == '.lean' for f in item.iterdir() if f.is_file())
                if has_lean:
                    top_level.append(item.name)
        
        if top_level:
            hints.append(f"\nAVAILABLE TOP-LEVEL MODULES:")
            for name in top_level[:10]:
                hints.append(f"  • {name}")
            if len(top_level) > 10:
                hints.append(f"  ... and {len(top_level) - 10} more")
            
            # Find similar top-level modules
            close_matches = get_close_matches(parts[0], top_level, n=3, cutoff=0.6)
            if close_matches:
                hints.append(f"\nSUGGESTION: Did you mean: {', '.join(close_matches)}?")
    except Exception:
        pass

    return error_msg + '\n' + '\n'.join(hints)


def enhance_unexpected_token_in_error(error_msg: str) -> str:
    """Enhance 'unexpected token in' error, provide syntax update hint

    Handle error pattern: "unexpected token 'in'; expected ','"
    """
    if "unexpected token 'in'" in error_msg and "expected ','" in error_msg:
        hints = []
        hints.append(f"\n{'='*60}")
        hints.append("SYNTAX ERROR: Deprecated 'in' keyword")
        hints.append(f"{'='*60}")
        hints.append("\nREASON: 'in' keyword has been deprecated")
        hints.append("SOLUTION: Use '∈' instead (type \\in in editor)")
        hints.append("\nEXAMPLE:")
        hints.append("  INCORRECT:  ∑ x in s, f x")
        hints.append("  CORRECT:  ∑ x ∈ s, f x")

        return error_msg + '\n' + '\n'.join(hints)

    return error_msg


def enhance_lean_error(error_msg: str, working_dir: Path) -> str:
    """Main error enhancement function - applies all available error enhancements

    Args:
        error_msg: Original error message from Lean
        working_dir: Working directory for file path resolution

    Returns:
        Enhanced error message with helpful hints
    """
    # Try each error enhancement in sequence
    enhanced = error_msg

    # Check for module not found errors
    if "does not exist" in error_msg and "module" in error_msg:
        enhanced = enhance_module_not_found_error(enhanced, working_dir)

    # Check for unexpected token 'in' errors
    if "unexpected token 'in'" in error_msg:
        enhanced = enhance_unexpected_token_in_error(enhanced)

    return enhanced
