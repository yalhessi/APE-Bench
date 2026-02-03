#!/usr/bin/env python3
"""
Storage integrity verification tool

Traverse the entire content-addressed storage, verify that the content hash of all files matches the file name.
Use multi-process parallel processing to improve performance.

Usage:
    python -m ape.toolkits.execute.lean.utils.verify_storage
"""

import os
import sys
import hashlib
import argparse
import time
import json
from pathlib import Path
from typing import List, Tuple, Optional
from multiprocessing import Pool, cpu_count
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class VerificationResult:
    """Verification result"""
    total_files: int = 0
    verified_files: int = 0
    corrupted_files: int = 0
    missing_files: int = 0
    error_files: int = 0
    corrupted_list: List[Tuple[str, str, str]] = None  # (file path, expected hash, actual hash)
    error_list: List[Tuple[str, str]] = None  # (file path, error message)
    
    def __post_init__(self):
        if self.corrupted_list is None:
            self.corrupted_list = []
        if self.error_list is None:
            self.error_list = []


def compute_file_hash_sync(file_path: Path, algorithm: str = "sha256") -> str:
    """Synchronously compute file hash (for multi-process)"""
    if file_path.is_symlink():
        # Symbolic link: hash target path
        target = os.readlink(file_path)
        hasher = hashlib.new(algorithm)
        hasher.update(target.encode('utf-8'))
        return hasher.hexdigest()
    else:
        # Regular file: compute content hash
        hasher = hashlib.new(algorithm)
        with open(file_path, 'rb') as f:
            while chunk := f.read(65536):  # 64KB chunks for better performance
                hasher.update(chunk)
        return hasher.hexdigest()


def verify_single_file(file_info: Tuple[Path, str]) -> Tuple[str, Optional[str], Optional[str]]:
    """Verify a single file
    
    Args:
        file_info: (file path, expected hash)
    
    Returns:
        (status, expected hash, actual hash or error message)
        status: "ok", "corrupted", "missing", "error"
    """
    file_path, expected_hash = file_info
    
    try:
        # Check if file exists
        if not file_path.exists():
            return ("missing", expected_hash, "file not found")
        
        # Compute actual hash
        actual_hash = compute_file_hash_sync(file_path)
        
        # Verify hash
        if actual_hash == expected_hash:
            return ("ok", expected_hash, actual_hash)
        else:
            return ("corrupted", expected_hash, actual_hash)
            
    except Exception as e:
        return ("error", expected_hash, str(e))


def collect_storage_files(storage_dir: Path) -> List[Tuple[Path, str]]:
    """Collect all files to be verified
    
    Returns:
        List[(file path, expected hash)]
    """
    files = []
    
    # Traverse two-level directory structure: xx/yy/hash
    if not storage_dir.exists():
        print(f"Storage directory not found: {storage_dir}")
        return files
    
    for level1 in storage_dir.iterdir():
        if not level1.is_dir():
            continue
        
        # level1 should be two-character hexadecimal directory
        if len(level1.name) != 2:
            continue
        
        for level2 in level1.iterdir():
            if not level2.is_dir():
                continue
            
            # level2 should be two-character hexadecimal directory
            if len(level2.name) != 2:
                continue
            
            # Collect all files in this directory
            for file_path in level2.iterdir():
                if file_path.is_file() or file_path.is_symlink():
                    # File name is the expected hash
                    expected_hash = file_path.name
                    files.append((file_path, expected_hash))
    
    return files


def save_verification_report(result: VerificationResult, output_file: Path, storage_dir: Path, 
                            workers: int, total_time: float, verify_time: float):
    """Save verification report to file"""
    report = {
        "verification_info": {
            "storage_dir": str(storage_dir),
            "timestamp": datetime.now().isoformat(),
            "workers": workers,
            "total_time_seconds": round(total_time, 2),
            "verify_time_seconds": round(verify_time, 2),
            "verification_rate": round(result.total_files / verify_time if verify_time > 0 else 0, 2)
        },
        "summary": {
            "total_files": result.total_files,
            "verified_files": result.verified_files,
            "corrupted_files": result.corrupted_files,
            "missing_files": result.missing_files,
            "error_files": result.error_files,
            "success_rate": round(result.verified_files * 100 / result.total_files if result.total_files > 0 else 0, 2)
        },
        "corrupted_files": [
            {
                "file_path": file_path,
                "expected_hash": expected,
                "actual_hash": actual
            }
            for file_path, expected, actual in result.corrupted_list
        ],
        "error_files": [
            {
                "file_path": file_path,
                "error": error
            }
            for file_path, error in result.error_list
        ]
    }
    
    # Save as JSON
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\nFull report saved to: {output_file}")


def verify_storage(storage_dir: Path, workers: int, verbose: bool = False, 
                  output_file: Optional[Path] = None) -> VerificationResult:
    """Verify entire storage directory
    
    Args:
        storage_dir: storage directory path
        workers: concurrent number of processes
        verbose: whether to output detailed information
        output_file: output report file path
    
    Returns:
        VerificationResult: verification result
    """
    print(f"Start verifying storage: {storage_dir}")
    print(f"Concurrent number of processes: {workers}")
    if output_file:
        print(f"Report output: {output_file}")
    
    # Collect all files
    print("\nCollecting file list...")
    start_time = time.time()
    files = collect_storage_files(storage_dir)
    collect_time = time.time() - start_time
    
    if not files:
        print("No files found")
        return VerificationResult()
    
    print(f"Collected {len(files)} files (time: {collect_time:.2f}s)")
    
    # Initialize result container
    result = VerificationResult(total_files=len(files))
    
    # Multiprocess verification
    print(f"\nStart verifying {len(files)} files...")
    verify_start = time.time()
    
    with Pool(processes=workers) as pool:
        # Use imap_unordered to display progress in real time
        completed = 0
        last_progress = 0
        
        for status, expected_hash, actual_or_error in pool.imap_unordered(verify_single_file, files, chunksize=100):
            completed += 1
            
            # Update statistics
            if status == "ok":
                result.verified_files += 1
            elif status == "corrupted":
                result.corrupted_files += 1
                file_path = files[completed - 1][0]
                result.corrupted_list.append((str(file_path), expected_hash, actual_or_error))
                if verbose:
                    print(f"Corrupted: {file_path}")
                    print(f"Expected: {expected_hash}")
                    print(f"Actual: {actual_or_error}")
            elif status == "missing":
                result.missing_files += 1
                file_path = files[completed - 1][0]
                result.error_list.append((str(file_path), "File not found"))
                if verbose:
                    print(f"Missing: {file_path}")
            elif status == "error":
                result.error_files += 1
                file_path = files[completed - 1][0]
                result.error_list.append((str(file_path), actual_or_error))
                if verbose:
                    print(f"Error: {file_path} - {actual_or_error}")
            
            # Display progress (every 5% update)
            progress = int(completed * 100 / len(files))
            if progress >= last_progress + 5 or completed == len(files):
                elapsed = time.time() - verify_start
                rate = completed / elapsed if elapsed > 0 else 0
                eta = (len(files) - completed) / rate if rate > 0 else 0
                print(f"Progress: {completed}/{len(files)} ({progress}%) | "
                      f"Speed: {rate:.0f} files/second | ETA: {eta:.0f}s")
                last_progress = progress
    
    verify_time = time.time() - verify_start
    total_time = time.time() - start_time
    
    # Output result summary
    print("\n" + "="*70)
    print("Verification result summary")
    print("="*70)
    print(f"Total files:     {result.total_files:>10,}")
    print(f"Verified files:     {result.verified_files:>10,} ({result.verified_files*100/result.total_files:.2f}%)")
    print(f"Corrupted content:     {result.corrupted_files:>10,} ({result.corrupted_files*100/result.total_files:.2f}%)")
    print(f"Missing files:     {result.missing_files:>10,} ({result.missing_files*100/result.total_files:.2f}%)")
    print(f"Verification errors:     {result.error_files:>10,} ({result.error_files*100/result.total_files:.2f}%)")
    print("-"*70)
    print(f"Collect time:     {collect_time:>10.2f}s")
    print(f"Verify time:     {verify_time:>10.2f}s")
    print(f"Total time:       {total_time:>10.2f}s")
    print(f"Verify rate:     {result.total_files/verify_time:>10.0f} files/second")
    print("="*70)
    
    # Output corrupted file list (only show the first few)
    if result.corrupted_list:
        print("\nCorrupted file list (only show the first few):")
        for file_path, expected, actual in result.corrupted_list[:5]:
            print(f"  - {file_path}")
            print(f"    Expected hash: {expected}")
            print(f"    Actual hash: {actual}")
        if len(result.corrupted_list) > 5:
            print(f"  ... and other {len(result.corrupted_list) - 5} corrupted files")
    
    # Output error file list (only show the first few)
    if result.error_list:
        print("\nError file list (only show the first few):")
        for file_path, error in result.error_list[:5]:
            print(f"  - {file_path}: {error}")
        if len(result.error_list) > 5:
            print(f"  ... and other {len(result.error_list) - 5} error files")
    
    # Save complete report to file
    if output_file:
        save_verification_report(result, output_file, storage_dir, workers, total_time, verify_time)
        if result.corrupted_list or result.error_list:
            print(f"Complete error file list (total {len(result.corrupted_list) + len(result.error_list)} files) saved to report file")
    
    # Final status
    if result.corrupted_files == 0 and result.missing_files == 0 and result.error_files == 0:
        print("\nStorage integrity verification passed! All file hashes are correct.")
        return result
    else:
        print(f"\nStorage has problems! Found {result.corrupted_files + result.missing_files + result.error_files} problem files.")
        if not output_file:
            print("Tip: Use --output parameter to save complete error file list")
        return result


def main():
    parser = argparse.ArgumentParser(
        description="Verify the integrity of content-addressed storage",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Use default storage path, 8 processes, save report
  python verify_storage.py --workers 8 --output verification_report.json
  
  # Specify storage path, use all CPU cores
  python verify_storage.py --storage-dir /path/to/storage --workers auto --output report.json
  
  # Verbose mode, output each problem file
  python verify_storage.py --workers 8 --verbose --output report.json
        """
    )
    
    parser.add_argument(
        '--storage_dir',
        type=str,
        default=None,
        help='Storage directory path (default: read from config)'
    )

    parser.add_argument(
        '--workers',
        type=str,
        default='auto',
        help='Concurrent number of processes ("auto" uses CPU core number, default: auto)'
    )
    
    parser.add_argument(
        '--output', '-o',
        type=str,
        default=None,
        help='Output report file path (JSON format, contains all error file details, default: temp/storage_verification_<timestamp>.json)'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Verbose mode, output each problem file'
    )
    
    args = parser.parse_args()
    
    # Determine storage directory
    if args.storage_dir:
        storage_dir = Path(args.storage_dir)
    else:
        # Use default config
        from ..config import LeanVerifyToolConfig
        config = LeanVerifyToolConfig()
        storage_dir = config.storage_dir
    
    # Determine concurrent number of processes
    if args.workers == 'auto':
        workers = cpu_count()
    else:
        try:
            workers = int(args.workers)
            if workers <= 0:
                print(f"Error: number of processes must be greater than 0")
                sys.exit(1)
        except ValueError:
            print(f"Error: invalid number of processes: {args.workers}")
            sys.exit(1)
    
    # Determine output file - default save to temp directory
    if args.output:
        output_file = Path(args.output)
    else:
        # Get project root directory's temp directory
        script_dir = Path(__file__).resolve().parent
        project_root = script_dir.parent.parent.parent.parent  # 4 levels up from utils/ to project root
        temp_dir = project_root / "temp"
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate file name with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = temp_dir / f"storage_verification_{timestamp}.json"
    
    # Execute verification
    result = verify_storage(storage_dir, workers, args.verbose, output_file)
    
    # Return exit code
    if result.corrupted_files > 0 or result.missing_files > 0 or result.error_files > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == '__main__':
    main()
