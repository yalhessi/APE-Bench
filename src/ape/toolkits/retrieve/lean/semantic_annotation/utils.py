"""
Simplified utility function collection
"""

from typing import List, Dict, Any, Optional, Tuple, Set
from pathlib import Path
import hashlib
import git
import json
import re
import time
from bisect import bisect_left

from .config import AnnotationConfig
from ape.toolkits.code.lean.lean_parser import parse_major_declarations
from .models import DeclarationInfo, ScanResult


def normalize_lean_text(text: str) -> str:
    """Normalize Lean text: remove comments, empty lines, extra spaces"""
    if not text:
        return ""
    
    # Remove comments
    text = re.sub(r'--.*?(?=\n|$)', '', text)  # Line comments
    text = re.sub(r'/-.*?-/', '', text, flags=re.DOTALL)  # Block comments
    
    # Remove non-core statements
    for pattern in [r'#align.*?(?=\n|$)', r'set_option.*?(?=\n|$)', 
                   r'import.*?(?=\n|$)', r'open.*?(?=\n|$)']:
        text = re.sub(pattern, '', text)
    
    # Completely normalize: remove all whitespace, only keep core content
    return re.sub(r'\s+', '', text)


def compute_item_id(kind: str, name: Optional[str], signature: str, proof: str) -> str:
    """
    Compute unique ID based on declaration type
    
    Strategy:
    - theorem/lemma: only care about signature (signature already contains kind information)
    - Other types (def/example etc.): care about signature and proof
    """
    h = hashlib.sha256()
    
    # Normalize text
    normalized_signature = normalize_lean_text(signature)
    normalized_proof = normalize_lean_text(proof)
    
    # Use different strategies based on declaration type
    if kind.lower() in ('theorem', 'lemma'):
        # theorem/lemma only care about signature (signature already contains kind and name information)
        h.update(normalized_signature.encode("utf-8"))
    else:
        # Other types (def/example etc.) care about signature and proof
        h.update(normalized_signature.encode("utf-8"))
        h.update(normalized_proof.encode("utf-8"))
    
    return h.hexdigest()


def parse_declarations(file_content: str) -> List[Dict[str, Any]]:
    """Parse file content, extract declarations, span directly converted to line numbers"""
    decls = []
    for d in parse_major_declarations(file_content or ""):
        # Convert character position to line number
        char_start, char_end = d.span
        line_start = char_pos_to_line_number(file_content, char_start)
        line_end = char_pos_to_line_number(file_content, char_end)
        
        decls.append({
            "kind": d.kind,
            "name": d.name,
            "fullname": d.fullname,
            "variables": d.variables,
            "signature": d.signature,
            "proof": d.proof,
            "span": (line_start, line_end),  # Directly store line numbers
        })
    return decls


def char_pos_to_line_number(src: str, char_pos: int) -> int:
    """Convert character position to line number (1-based)"""
    line_starts = [0]
    for i, ch in enumerate(src):
        if ch == '\n':
            line_starts.append(i + 1)
    
    line_idx = bisect_left(line_starts, char_pos + 1) - 1
    return max(1, line_idx + 1)

# Configuration and cache functionality

def compute_config_hash(config: AnnotationConfig) -> str:
    """Compute configuration hash"""
    exclude_fields = {'num_processes', 'max_retries', 'batch_size', 'io_workers', 'cache_dir'}
    config_dict = config.model_dump(mode='json', exclude=exclude_fields)
    payload = json.dumps(config_dict, sort_keys=True, ensure_ascii=False)
    return hashlib.md5(payload.encode('utf-8')).hexdigest()[:16]


def get_cache_file_path(cache_dir: Path, config_hash: str, cache_tokens: List[str]) -> Path:
    """Get cache file path (based on configuration hash and additional tokens)"""
    cache_dir.mkdir(parents=True, exist_ok=True)
    token_payload = '\n'.join(sorted(cache_tokens)) if cache_tokens else 'empty'
    commits_summary = hashlib.md5(token_payload.encode()).hexdigest()[:8]
    return cache_dir / f"phase1_cache_{config_hash}_{commits_summary}.json"


def load_cache(cache_file: Path) -> Optional[ScanResult]:
    """Load cache and deserialize to ScanResult"""
    if not cache_file.exists():
        return None
    
    try:
        with open(cache_file, 'r', encoding='utf-8') as f:
            cache_data = json.load(f)
        
        global_decls = {
            item_id: DeclarationInfo.model_validate(decl_data)
            for item_id, decl_data in cache_data.get('global_declarations', {}).items()
        }
        
        commit_index_raw = cache_data.get('commit_index', {})
        commit_index: Dict[str, Dict[str, List[Tuple[str, Optional[str], str, List[str]]]]] = {}
        for repo_url, commits in commit_index_raw.items():
            repo_commits: Dict[str, List[Tuple[str, Optional[str], str, List[str]]]] = {}
            for commit_hash, items in commits.items():
                normalized_items = []
                for entry in items:
                    if isinstance(entry, (list, tuple)) and len(entry) >= 3:
                        variables = entry[3] if len(entry) >= 4 and entry[3] else []
                        if isinstance(variables, str):
                            if variables.strip():
                                try:
                                    variables = json.loads(variables)
                                except Exception:
                                    variables = [variables]
                            else:
                                variables = []
                        if not isinstance(variables, list):
                            variables = []
                        # Format: (item_id, name, filename, variables)
                        normalized_items.append((entry[0], entry[1], entry[2], list(variables)))
                repo_commits[commit_hash] = normalized_items
            commit_index[repo_url] = repo_commits
        
        return ScanResult(
            global_declarations=global_decls,
            commit_index=commit_index,
            total_declarations=cache_data.get('total_declarations', len(global_decls)),
            existing_skipped=cache_data.get('existing_skipped', 0),
            unique_blobs=cache_data.get('unique_blobs', 0)
        )
    except Exception:
        return None


def save_cache(cache_file: Path, scan_result: ScanResult) -> None:
    """Save scan result cache"""
    try:
        serializable_decls = {
            item_id: decl.model_dump(mode='json')
            for item_id, decl in scan_result.global_declarations.items()
        }
        
        # JSON cannot serialize tuple, convert to list
        # New format: [item_id, name, filename, variables]
        serializable_commit_index = {
            repo_url: {
                commit_hash: [[item_id, name, filename, variables] for item_id, name, filename, variables in items]
                for commit_hash, items in commits.items()
            }
            for repo_url, commits in scan_result.commit_index.items()
        }
        
        cache_data = {
            'global_declarations': serializable_decls,
            'commit_index': serializable_commit_index,
            'total_declarations': scan_result.total_declarations,
            'existing_skipped': scan_result.existing_skipped,
            'unique_blobs': scan_result.unique_blobs,
            'timestamp': time.time()
        }
        
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, ensure_ascii=False)
    except Exception:
        pass  # Ignore cache save failure


def generate_task_id(commit_hash: str, file_path: str, chunk_idx: Optional[int] = None) -> str:
    """Generate unified task ID function"""
    commit_short = commit_hash[:8]
    file_safe = file_path.replace('/', '_')
    
    if chunk_idx is not None:
        return f"annot_{commit_short}_{file_safe}_chunk{chunk_idx + 1}"
    else:
        return f"annot_{commit_short}_{file_safe}"


def load_existing_ids(annotated_ids_file: Path) -> Set[str]:
    """Load existing annotated ID set"""
    if not annotated_ids_file.exists():
        return set()
    
    try:
        with open(annotated_ids_file, 'r', encoding='utf-8') as f:
            return {
                line.strip() 
                for line in f 
                if line.strip() and len(line.strip()) == 64
            }
    except Exception:
        return set()
