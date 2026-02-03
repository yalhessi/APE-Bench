#!/usr/bin/env python3
"""
Convert miniCTX-v2 Dataset to LeanProofEngineeringData format with Reference Workspace Support

This script converts the miniCTX-v2 dataset to the LeanProofEngineeringData format,
using fixed commit versions as specified in the dataset documentation.
"""

import argparse
import json
from pathlib import Path, PurePosixPath
from typing import Any, Dict, Optional, List

from datasets import load_dataset

from .github_utils import fetch_file_from_github, get_default_target
from ..taxonomy.lean_task_taxonomy import annotate_record_metadata


# Fixed project configurations (repo URL + commit) from miniCTX-v2 documentation
PROJECT_CONFIGS = {
    'carleson': {
        'repo_url': 'https://github.com/fpvandoorn/carleson.git',
        'commit_hash': 'a5d265f109105809de4aaff16776b7c16b1c0bd5',
    },
    'ConNF': {
        'repo_url': 'https://github.com/leanprover-community/con-nf.git',
        'commit_hash': '51c38ad244870b8b1f40b8272b281678397dfa4f',
    },
    'FLT': {
        'repo_url': 'https://github.com/ImperialCollegeLondon/FLT.git',
        'commit_hash': '4a97c893071433d0d39cbf5261d0877f864c2189',
    },
    'foundation': {
        'repo_url': 'https://github.com/FormalizedFormalLogic/Foundation.git',
        'commit_hash': '54324e6e009f0d0a288897312d3feb1c0165ad19',
    },
    'HepLean': {
        'repo_url': 'https://github.com/HEPLean/PhysLean.git',
        'commit_hash': 'fe082d93c2775beee6634b24b34c8482a02ba8a8',
    },
    'mathlib': {
        'repo_url': 'https://github.com/leanprover-community/mathlib4.git',
        'commit_hash': 'a6276f4c6097675b1cf5ebd49b1146b735f38c02',
    },
    'Seymour': {
        'repo_url': 'https://github.com/Ivan-Sergeyev/seymour.git',
        'commit_hash': '27c0384977032b693daca8c4fcfc5cc274e1f2d6',
    },
}

def parse_mathlib_dependency(manifest_content: str) -> Optional[str]:
    """Parse mathlib dependency from lake-manifest.json content."""
    try:
        manifest = json.loads(manifest_content)
        packages = manifest.get('packages', [])
        for package in packages:
            if package.get('name') == 'mathlib':
                return package.get('rev')
        return None
    except Exception as e:
        print(f"  Warning: Failed to parse lake-manifest.json: {e}")
        return None


def get_mathlib_reference_workspace(config_name: str) -> Optional[Dict[str, str]]:
    """
    Get mathlib4 reference workspace configuration by parsing lake-manifest.json.
    
    Returns None if target is already mathlib or if mathlib dependency cannot be determined.
    """
    if config_name.lower() == 'mathlib':
        return None

    project_config = PROJECT_CONFIGS[config_name]
    repo_url = project_config['repo_url']
    commit_hash = project_config['commit_hash']

    manifest_content = fetch_file_from_github(repo_url, commit_hash, 'lake-manifest.json')
    if not manifest_content:
        print(f"  Warning: Could not fetch lake-manifest.json, mathlib dependency unavailable")
        return None

    mathlib_commit = parse_mathlib_dependency(manifest_content)
    if not mathlib_commit:
        print(f"  Warning: Could not parse mathlib dependency from lake-manifest.json")
        return None

    # Fetch toolchain for mathlib reference workspace
    mathlib_repo_url = 'https://github.com/leanprover-community/mathlib4.git'
    mathlib_toolchain = fetch_file_from_github(mathlib_repo_url, mathlib_commit, 'lean-toolchain')
    if mathlib_toolchain:
        mathlib_toolchain = mathlib_toolchain.strip()

    mathlib_default_target = get_default_target(mathlib_repo_url, mathlib_commit) or "Mathlib"

    return {
        'name': 'mathlib',
        'repo_url': mathlib_repo_url,
        'commit_hash': mathlib_commit,
        'toolchain': mathlib_toolchain,
        'default_target': mathlib_default_target,
        'read_only_path_patterns': ['**/*']
    }


def _normalize_file_path(file_path: str, default_target: Optional[str]) -> tuple[Optional[str], Optional[str]]:
    """
    Normalize repository file paths so they are relative to the nearest default target segment.

    Returns a tuple of (relative_path, original_path). Both values use POSIX separators.
    """
    if not file_path:
        return None, None

    path = PurePosixPath(file_path)
    original = path.as_posix()

    if default_target:
        default_lower = default_target.lower()
        parts = path.parts

        # Walk from the end to keep the innermost default_target segment
        for idx in range(len(parts) - 1, -1, -1):
            if parts[idx].lower() == default_lower:
                remainder = parts[idx + 1 :]
                if remainder:
                    return str(PurePosixPath(*remainder)), original
                # Edge case: file lives directly at the target root
                return parts[idx], original

    return original, original


def _ensure_default_target_prefix(path: str, default_target: str) -> str:
    """Ensure path is relative to workspace root with default_target prefix.

    Access control patterns are resolved relative to workspace root (not target_path),
    so we must block `<default_target>/<relative_path_inside_target>`.
    """
    p = PurePosixPath(path)
    if not default_target:
        return p.as_posix()
    if p.parts and p.parts[0].lower() == default_target.lower():
        return p.as_posix()
    return (PurePosixPath(default_target) / p).as_posix()


def convert_record(
    record: Dict[str, Any],
    config_name: str,
    include_mathlib_reference: bool = True
) -> Dict[str, Any]:
    """Convert a single miniCTX-v2 record to LeanProofEngineeringData format."""
    
    # Extract core fields from record
    theorem_name = record.get('theoremName', '')
    theorem_statement = record.get('theoremStatement', '')
    src_context = record.get('srcContext', '')
    file_path = record.get('file', '')
    module_name = record.get('module', '')

    # Use fixed commit from project configuration
    project_config = PROJECT_CONFIGS[config_name]
    repo_url = project_config['repo_url']
    commit_hash = project_config['commit_hash']

    # Fetch toolchain from repository
    toolchain_content = fetch_file_from_github(repo_url, commit_hash, 'lean-toolchain')
    if toolchain_content:
        toolchain_content = toolchain_content.strip()

    default_target = get_default_target(repo_url, commit_hash)
    if not default_target:
        raise RuntimeError(
            f"Failed to determine default target for repository {repo_url} at commit {commit_hash}"
        )

    # Create complete original code with sorry placeholder
    original_code = f"{src_context}\n\n{theorem_statement.rstrip()} := by\n  sorry"

    # Create task description
    task_description = f"""Complete the proof for the theorem `{theorem_name}`.

The theorem statement is:
```lean
{theorem_statement}
```

You need to provide a complete proof that satisfies the theorem statement.
The surrounding context from the file is provided for reference."""

    # Extract creation info and convert datetime to string
    theorem_created = record.get('theoremCreated', {})
    file_created = record.get('fileCreated', {})
    
    metadata = {
        'dataset': 'miniCTX-v2',
        'config': config_name,
        'theorem_name': theorem_name,
        'file': file_path,
        'module': module_name,
        'theorem_created_commit': theorem_created.get('commit', ''),
        'theorem_created_time': str(theorem_created.get('time', '')) if theorem_created.get('time') else '',
        'file_created_commit': file_created.get('commit', ''),
        'file_created_time': str(file_created.get('time', '')) if file_created.get('time') else '',
    }

    # Add proof statistics if available (from proofMetadata)
    proof_metadata = record.get('proofMetadata', {})
    if proof_metadata.get('hasProof') and proof_metadata.get('proof'):
        metadata['original_proof_lines'] = proof_metadata.get('proofLengthLines', 0)
        metadata['original_proof_tokens'] = proof_metadata.get('proofLengthTokens', 0)
        metadata['proof_type'] = proof_metadata.get('proofType', '')
        metadata['reference_implementation'] = proof_metadata.get('proof', '')

    # Add premise statistics
    metadata['num_premises'] = record.get('numPremises', 0)
    metadata['num_in_file_premises'] = record.get('numInFilePremises', 0)
    metadata['num_repository_premises'] = record.get('numRepositoryPremises', 0)

    # Position metadata
    if 'positionMetadata' in record:
        pos_meta = record['positionMetadata']
        metadata['line_number'] = pos_meta.get('lineNumber', 0)
        metadata['theorem_pos_in_file'] = pos_meta.get('theoremPositionInFile', 0)

    # Process filename to be relative to default_target
    relative_filename, original_dataset_file = _normalize_file_path(
        file_path=file_path,
        default_target=default_target
    )

    normalized_filename = relative_filename or original_dataset_file

    # Leakage-safe blocking: block the corresponding target file path
    blocked_target_path: Optional[str] = None
    if normalized_filename:
        blocked_target_path = _ensure_default_target_prefix(
            PurePosixPath(normalized_filename).as_posix(),
            default_target=default_target
        )

    mathlib_source_path = original_dataset_file or normalized_filename or ''
    mathlib_parts = PurePosixPath(mathlib_source_path).parts
    is_mathlib_target = any(part.lower() == 'mathlib' for part in mathlib_parts)

    reference_workspaces: List[Dict[str, Any]] = []
    if (
        include_mathlib_reference
        and config_name.lower() != 'mathlib'
        and is_mathlib_target
    ):
        mathlib_ref = get_mathlib_reference_workspace(config_name)
        if mathlib_ref:
            reference_workspaces.append(mathlib_ref)

    target_workspace: Dict[str, Any] = {
        'name': 'target',
        'commit_hash': commit_hash,
        'repo_url': repo_url,
        'default_target': default_target,
        'toolchain': toolchain_content,
        'read_only_path_patterns': ['**/*'],
    }
    if blocked_target_path:
        target_workspace['blocked_path_patterns'] = [blocked_target_path]

    converted = {
        'task_type': 'lean_proof_engineering',
        'task_id': f"minictx_v2_{config_name}_{theorem_name}",
        'task_description': task_description,
        'original_code': original_code,
        'target_workspace': {
            'name': 'target',
            'commit_hash': commit_hash,
            'repo_url': repo_url,
            'default_target': default_target,
            'toolchain': toolchain_content,
            'read_only_path_patterns': ['**/*']
        },
        'filename': normalized_filename,
        'metadata': metadata
    }
    
    if reference_workspaces:
        # If the theorem lives in Mathlib and we're providing a mathlib reference workspace,
        # block the same file path there as well (defense-in-depth).
        for ref_ws in reference_workspaces:
            ref_default_target = ref_ws.get('default_target')
            if not ref_default_target:
                continue
            if blocked_target_path and ref_default_target.lower() == default_target.lower():
                # Same target root name; reuse blocked path
                ref_ws.setdefault('blocked_path_patterns', [])
                if blocked_target_path not in ref_ws['blocked_path_patterns']:
                    ref_ws['blocked_path_patterns'].append(blocked_target_path)
        converted['reference_workspaces'] = reference_workspaces

    # Update metadata with normalized paths
    metadata['file'] = normalized_filename if normalized_filename else None
    if original_dataset_file and normalized_filename != original_dataset_file:
        metadata['original_dataset_file'] = original_dataset_file
    else:
        metadata.pop('original_dataset_file', None)

    annotate_record_metadata(converted)
    return converted


def convert_minictx_v2(
    config_name: str,
    split: str,
    output_file: Path,
    include_mathlib_reference: bool = True,
    max_records: Optional[int] = None
):
    """Convert a miniCTX-v2 configuration/split to LeanProofEngineeringData format."""
    
    print(f"\nConverting miniCTX-v2 config={config_name}, split={split}")
    print(f"  Using fixed commit: {PROJECT_CONFIGS[config_name]['commit_hash'][:8]}")
    print(f"  Loading dataset from Hugging Face...")

    try:
        dataset = load_dataset('l3lab/miniCTX-v2', name=config_name, split=split)
    except Exception as e:
        print(f"  Error loading dataset: {e}")
        print(f"  Make sure you have datasets library installed: pip install datasets")
        raise

    print(f"  Loaded {len(dataset)} records")

    if max_records and max_records < len(dataset):
        dataset = dataset.select(range(max_records))
        print(f"  Limited to {max_records} records")

    converted_count = 0
    error_count = 0

    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w', encoding='utf-8') as outfile:
        for idx, record in enumerate(dataset):
            try:
                converted = convert_record(
                    record,
                    config_name,
                    include_mathlib_reference=include_mathlib_reference
                )

                json.dump(converted, outfile, ensure_ascii=False)
                outfile.write('\n')

                converted_count += 1

                if (idx + 1) % 10 == 0:
                    print(f"  Processed {idx + 1}/{len(dataset)} records...")

            except Exception as e:
                print(f"  Error processing record {idx}: {e}")
                error_count += 1
                continue

    print(f"  Completed: {converted_count} records converted, {error_count} errors")
    print(f"  Output written to: {output_file}")

    return converted_count, error_count


def merge_jsonl_files(input_files: list[Path], output_file: Path) -> int:
    """Merge multiple JSONL files into a single file."""
    total_records = 0
    
    with open(output_file, 'w', encoding='utf-8') as outfile:
        for input_file in input_files:
            if not input_file.exists():
                print(f"  Warning: File {input_file} does not exist, skipping")
                continue
                
            with open(input_file, 'r', encoding='utf-8') as infile:
                for line in infile:
                    line = line.strip()
                    if line:
                        outfile.write(line)
                        outfile.write('\n')
                        total_records += 1
    
    return total_records


def main():
    parser = argparse.ArgumentParser(
        description='Convert miniCTX-v2 dataset to LeanProofEngineeringData format with fixed commit versions',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Convert ConNF validation set
  python -m src.datasets.external_benchmarks.convert_minictx_v2.py --config ConNF --split valid

  # Convert all configurations (both splits)
  python -m src.datasets.external_benchmarks.convert_minictx_v2.py --config all

  # Convert without mathlib reference workspace
  python -m src.datasets.external_benchmarks.convert_minictx_v2.py --config mathlib --split valid --no-mathlib-reference
        """
    )

    parser.add_argument(
        '--config',
        type=str,
        default='all',
        help='Dataset configuration (ConNF, FLT, HepLean, Seymour, carleson, foundation, mathlib, or "all")'
    )
    parser.add_argument(
        '--split',
        type=str,
        choices=['valid', 'test', 'both'],
        default='both',
        help='Dataset split to convert (default: both)'
    )
    parser.add_argument(
        '--output-dir',
        type=Path,
        default=Path('inputs/minictx_v2'),
        help='Output directory for converted JSONL files (default: inputs/minictx_v2)'
    )
    parser.add_argument(
        '--no-mathlib-reference',
        action='store_true',
        help='Do not add mathlib as reference workspace'
    )
    parser.add_argument(
        '--max-records',
        type=int,
        default=None,
        help='Maximum number of records to convert per config/split (for testing)'
    )

    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)

    available_configs = list(PROJECT_CONFIGS.keys())

    if args.config == 'all':
        configs_to_convert = available_configs
    elif args.config in available_configs:
        configs_to_convert = [args.config]
    else:
        print(f"Error: Unknown configuration '{args.config}'")
        print(f"Available configurations: {', '.join(available_configs)}, all")
        return 1

    if args.split == 'both':
        splits_to_convert = ['valid', 'test']
    else:
        splits_to_convert = [args.split]

    print(f"Converting miniCTX-v2 dataset:")
    print(f"  Configurations: {', '.join(configs_to_convert)}")
    print(f"  Splits: {', '.join(splits_to_convert)}")
    print(f"  Add mathlib reference: {not args.no_mathlib_reference}")
    if args.max_records:
        print(f"  Max records per config/split: {args.max_records}")

    total_converted = 0
    total_errors = 0
    
    # Track generated files for merging
    generated_files = {'valid': [], 'test': []}

    for config in configs_to_convert:
        for split in splits_to_convert:
            try:
                output_file = args.output_dir / f"{config}_{split}.jsonl"

                converted, errors = convert_minictx_v2(
                    config_name=config,
                    split=split,
                    output_file=output_file,
                    include_mathlib_reference=not args.no_mathlib_reference,
                    max_records=args.max_records
                )

                total_converted += converted
                total_errors += errors
                
                # Track the generated file
                if split in generated_files:
                    generated_files[split].append(output_file)

            except Exception as e:
                print(f"\nError converting {config}/{split}: {e}")
                import traceback
                traceback.print_exc()
                continue

    # Merge files by split
    print(f"\n{'='*70}")
    print("Merging files by split...")
    
    merged_summary = {}
    
    for split in ['valid', 'test']:
        if generated_files[split]:
            merged_file = args.output_dir / f"all_{split}.jsonl"
            print(f"\n  Merging {len(generated_files[split])} files into {merged_file.name}...")
            merged_count = merge_jsonl_files(generated_files[split], merged_file)
            merged_summary[split] = merged_count
            print(f"  -> {merged_count} records written to {merged_file}")
    
    # Merge all files (valid + test)
    all_files = generated_files['valid'] + generated_files['test']
    if all_files:
        all_merged_file = args.output_dir / "all.jsonl"
        print(f"\n  Merging all {len(all_files)} files into {all_merged_file.name}...")
        all_merged_count = merge_jsonl_files(all_files, all_merged_file)
        merged_summary['all'] = all_merged_count
        print(f"  -> {all_merged_count} records written to {all_merged_file}")

    print(f"\n{'='*70}")
    print(f"Conversion Summary:")
    print(f"  Total records converted: {total_converted}")
    print(f"  Total errors: {total_errors}")
    print(f"  Output directory: {args.output_dir}")
    if merged_summary:
        print(f"\nMerged files:")
        for split, count in merged_summary.items():
            print(f"  all_{split}.jsonl: {count} records" if split != 'all' else f"  all.jsonl: {count} records")
    print(f"{'='*70}")

    return 0


if __name__ == '__main__':
    exit(main())
