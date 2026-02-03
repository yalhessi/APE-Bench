#!/usr/bin/env python3
"""
Disk usage monitoring CLI tool - minimal design
"""

import os
import sys
import time
import argparse
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Tuple

import matplotlib.pyplot as plt
import matplotlib.dates as mdates

from ape.utils.project import PROJECT_ROOT

def get_disk_usage_gb(path: Path) -> float:
    """Get the disk usage of the specified path (GB)"""
    try:
        total, used, free = shutil.disk_usage(path)
        return used / (1024**3)  # Convert to GB
    except Exception:
        return 0.0


def monitor_disk_usage() -> None:
    """Monitor disk usage and write to file"""
    # Create monitor file with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    data_dir = PROJECT_ROOT / "data/lean_verify/disk_monitor"
    data_dir.mkdir(parents=True, exist_ok=True)
    monitor_file = data_dir / f"{timestamp}.txt"
    
    print(f"Start monitoring disk usage, output file: {monitor_file}")
    print("Press Ctrl+C to stop monitoring")
    
    try:
        with open(monitor_file, 'w', encoding='utf-8') as f:
            # Write file header
            f.write(f"# Disk usage monitoring - start time: {datetime.now().isoformat()}\n")
            f.write(f"# Monitor path: {PROJECT_ROOT}\n")
            f.write("# Format: timestamp, disk usage (GB)\n")
            f.flush()
            
            while True:
                current_time = datetime.now()
                disk_usage = get_disk_usage_gb(PROJECT_ROOT)
                
                # Write data
                line = f"{current_time.isoformat()},{disk_usage:.2f}\n"
                f.write(line)
                f.flush()
                
                # Console output
                print(f"{current_time.strftime('%H:%M:%S')} - Disk usage: {disk_usage:.2f} GB")
                
                time.sleep(10)
                
    except KeyboardInterrupt:
        print(f"\nMonitoring stopped, data saved to: {monitor_file}")
    except Exception as e:
        print(f"Monitoring process error: {e}")


def parse_monitor_file(file_path: Path) -> Tuple[List[datetime], List[float]]:
    """Parse monitor file, return timestamps and disk usage list"""
    timestamps = []
    disk_usages = []
    
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line.startswith('#') or not line:
                continue
                
            try:
                time_str, usage_str = line.split(',')
                timestamp = datetime.fromisoformat(time_str)
                usage = float(usage_str)
                
                timestamps.append(timestamp)
                disk_usages.append(usage)
            except ValueError:
                continue  # Skip invalid lines
    
    return timestamps, disk_usages


def generate_disk_usage_chart(file_path: Path) -> None:
    """Generate disk usage PDF chart"""
    monitor_file = file_path
    if not monitor_file.exists():
        print(f"Error: monitor file not exists: {file_path}")
        return
    
    try:
        timestamps, disk_usages = parse_monitor_file(monitor_file)
        
        if not timestamps:
            print("Error: monitor file has no valid data")
            return
        
        # Create chart
        plt.figure(figsize=(12, 6))
        plt.plot(timestamps, disk_usages, 'b-', linewidth=2, marker='o', markersize=4)
        
        # Set title and labels
        plt.title('Disk usage change trend', fontsize=16, fontweight='bold')
        plt.xlabel('Time', fontsize=12)
        plt.ylabel('Disk usage (GB)', fontsize=12)
        
        # Format time axis
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
        plt.gca().xaxis.set_major_locator(mdates.MinuteLocator(interval=5))
        plt.xticks(rotation=45)
        
        # Add grid
        plt.grid(True, alpha=0.3)
        
        # Adjust layout
        plt.tight_layout()
        
        # Save PDF
        pdf_path = monitor_file.with_suffix('.pdf')
        plt.savefig(pdf_path, format='pdf', dpi=300, bbox_inches='tight')
        
        print(f"Chart generated: {pdf_path}")
        
        # Show statistics
        min_usage = min(disk_usages)
        max_usage = max(disk_usages)
        avg_usage = sum(disk_usages) / len(disk_usages)
        
        print(f"Statistics:")
        print(f"  Data points: {len(timestamps)}")
        print(f"  Time range: {timestamps[0].strftime('%H:%M:%S')} - {timestamps[-1].strftime('%H:%M:%S')}")
        print(f"  Minimum usage: {min_usage:.2f} GB")
        print(f"  Maximum usage: {max_usage:.2f} GB")
        print(f"  Average usage: {avg_usage:.2f} GB")
        
    except Exception as e:
        print(f"Error generating chart: {e}")


def create_argument_parser() -> argparse.ArgumentParser:
    """Create command line argument parser"""
    parser = argparse.ArgumentParser(
        description="Disk usage monitoring tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Start monitoring disk usage
  python -m ape.toolkits.execute.lean.disk_monitor

  # Generate chart from existing monitor file
  python -m ape.toolkits.execute.lean.disk_monitor --chart /path/to/disk_monitor/20231201_120000.txt
        """
    )
    
    parser.add_argument(
        "--chart",
        type=str,
        help="Specify monitor file path, generate PDF chart"
    )
    
    return parser


def main() -> int:
    """Main function"""
    parser = create_argument_parser()
    args = parser.parse_args()
    
    try:
        if args.chart:
            # Generate chart mode
            generate_disk_usage_chart(args.chart)
        else:
            # Monitor mode
            monitor_disk_usage()
        
        return 0
        
    except KeyboardInterrupt:
        return 0
    except Exception as e:
        print(f"Program running error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
