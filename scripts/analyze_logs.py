#!/usr/bin/env python3
"""
Log analyzer script for VeritasLoop.

Analyzes log files to extract performance metrics, error patterns,
and usage statistics.

Usage:
    python scripts/analyze_logs.py [log_file]
    python scripts/analyze_logs.py --date 20241207
    python scripts/analyze_logs.py --all
"""

import argparse
import re
import sys
from pathlib import Path
from typing import Dict, List, Any
from collections import defaultdict, Counter
from datetime import datetime
import json


class LogAnalyzer:
    """Analyzes VeritasLoop log files."""

    def __init__(self, log_file: Path):
        """
        Initialize log analyzer.

        Args:
            log_file: Path to the log file to analyze
        """
        self.log_file = log_file
        self.entries: List[Dict[str, Any]] = []
        self.stats = {
            "total_entries": 0,
            "by_level": Counter(),
            "by_module": Counter(),
            "errors": [],
            "performance": defaultdict(list),
            "cache_stats": {"hits": 0, "misses": 0},
            "api_calls": Counter(),
            "claims_processed": set(),
            "requests": set(),
        }

    def parse_log_line(self, line: str) -> Dict[str, Any]:
        """
        Parse a single log line.

        Args:
            line: Raw log line

        Returns:
            Parsed log entry as dictionary
        """
        # Log format: YYYY-MM-DD HH:MM:SS | LEVEL | module | req:id | claim:id | message
        pattern = r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) \| (\w+)\s+\| (.+?) \| req:(.+?) \| claim:(.+?) \| (.+)"
        match = re.match(pattern, line)

        if not match:
            return {}

        timestamp, level, module, request_id, claim_id, message = match.groups()

        return {
            "timestamp": timestamp,
            "level": level,
            "module": module.strip(),
            "request_id": request_id,
            "claim_id": claim_id,
            "message": message,
        }

    def parse_performance_message(self, message: str) -> Dict[str, Any]:
        """
        Extract performance metrics from log message.

        Args:
            message: Log message

        Returns:
            Performance data if found
        """
        # Pattern: "Completed: operation_name (duration: X.XXs)"
        pattern = r"Completed: (.+?) \(duration: ([\d.]+)s\)"
        match = re.search(pattern, message)

        if match:
            operation, duration = match.groups()
            return {"operation": operation, "duration": float(duration)}

        return {}

    def analyze_file(self):
        """Analyze the log file and extract statistics."""
        if not self.log_file.exists():
            print(f"Error: Log file not found: {self.log_file}")
            sys.exit(1)

        print(f"Analyzing log file: {self.log_file}")
        print("=" * 60)

        with open(self.log_file, "r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue

                entry = self.parse_log_line(line)
                if not entry:
                    continue

                self.stats["total_entries"] += 1
                self.stats["by_level"][entry["level"]] += 1
                self.stats["by_module"][entry["module"]] += 1

                # Track claims and requests
                if entry["claim_id"] != "-":
                    self.stats["claims_processed"].add(entry["claim_id"])
                if entry["request_id"] != "-":
                    self.stats["requests"].add(entry["request_id"])

                # Track errors
                if entry["level"] in ["ERROR", "CRITICAL"]:
                    self.stats["errors"].append({
                        "line": line_num,
                        "timestamp": entry["timestamp"],
                        "module": entry["module"],
                        "message": entry["message"],
                    })

                # Track performance metrics
                perf_data = self.parse_performance_message(entry["message"])
                if perf_data:
                    self.stats["performance"][perf_data["operation"]].append(
                        perf_data["duration"]
                    )

                # Track cache stats
                if "Cache hit" in entry["message"]:
                    self.stats["cache_stats"]["hits"] += 1
                elif "Cache miss" in entry["message"]:
                    self.stats["cache_stats"]["misses"] += 1

                # Track API calls
                if "Search completed successfully" in entry["message"]:
                    # Extract tool name from message
                    tool_match = re.search(r"tool: (\w+)", entry["message"])
                    if tool_match:
                        self.stats["api_calls"][tool_match.group(1)] += 1

                self.entries.append(entry)

    def print_summary(self):
        """Print analysis summary to console."""
        print("\n" + "=" * 60)
        print("LOG ANALYSIS SUMMARY")
        print("=" * 60)

        # Basic stats
        print(f"\nTotal log entries: {self.stats['total_entries']}")
        print(f"Unique claims processed: {len(self.stats['claims_processed'])}")
        print(f"Unique requests: {len(self.stats['requests'])}")

        # Log levels
        print("\nLog Levels:")
        for level, count in self.stats["by_level"].most_common():
            percentage = (count / self.stats["total_entries"]) * 100
            print(f"  {level:8s}: {count:5d} ({percentage:5.1f}%)")

        # Top modules
        print("\nTop Modules (by log entries):")
        for module, count in self.stats["by_module"].most_common(10):
            print(f"  {module:40s}: {count}")

        # Performance metrics
        if self.stats["performance"]:
            print("\nPerformance Metrics:")
            for operation, durations in sorted(self.stats["performance"].items()):
                avg_duration = sum(durations) / len(durations)
                min_duration = min(durations)
                max_duration = max(durations)
                print(f"  {operation}:")
                print(f"    Count: {len(durations)}")
                print(f"    Avg:   {avg_duration:.2f}s")
                print(f"    Min:   {min_duration:.2f}s")
                print(f"    Max:   {max_duration:.2f}s")

        # Cache statistics
        total_cache = self.stats["cache_stats"]["hits"] + self.stats["cache_stats"]["misses"]
        if total_cache > 0:
            hit_rate = (self.stats["cache_stats"]["hits"] / total_cache) * 100
            print(f"\nCache Performance:")
            print(f"  Hits:     {self.stats['cache_stats']['hits']}")
            print(f"  Misses:   {self.stats['cache_stats']['misses']}")
            print(f"  Hit Rate: {hit_rate:.1f}%")

        # API calls
        if self.stats["api_calls"]:
            print("\nAPI Calls by Tool:")
            for tool, count in self.stats["api_calls"].most_common():
                print(f"  {tool:20s}: {count}")

        # Errors
        if self.stats["errors"]:
            print(f"\nErrors Found: {len(self.stats['errors'])}")
            print("\nRecent Errors:")
            for error in self.stats["errors"][-5:]:  # Show last 5 errors
                print(f"\n  Line {error['line']} [{error['timestamp']}]")
                print(f"  Module: {error['module']}")
                print(f"  Message: {error['message'][:100]}")
        else:
            print("\n✓ No errors found!")

        print("\n" + "=" * 60)

    def export_json(self, output_path: Path):
        """
        Export analysis results to JSON.

        Args:
            output_path: Path to output JSON file
        """
        export_data = {
            "analyzed_file": str(self.log_file),
            "analysis_time": datetime.now().isoformat(),
            "summary": {
                "total_entries": self.stats["total_entries"],
                "claims_processed": len(self.stats["claims_processed"]),
                "requests": len(self.stats["requests"]),
                "errors": len(self.stats["errors"]),
            },
            "log_levels": dict(self.stats["by_level"]),
            "top_modules": dict(self.stats["by_module"].most_common(20)),
            "performance": {
                op: {
                    "count": len(durations),
                    "avg": sum(durations) / len(durations),
                    "min": min(durations),
                    "max": max(durations),
                }
                for op, durations in self.stats["performance"].items()
            },
            "cache_stats": self.stats["cache_stats"],
            "api_calls": dict(self.stats["api_calls"]),
            "errors": self.stats["errors"],
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)

        print(f"\n✓ Analysis exported to: {output_path}")


def find_log_files(log_dir: Path, date_filter: str = None) -> List[Path]:
    """
    Find log files in the logs directory.

    Args:
        log_dir: Directory containing log files
        date_filter: Date string to filter (YYYYMMDD format)

    Returns:
        List of log file paths
    """
    if not log_dir.exists():
        return []

    pattern = f"veritasloop_{date_filter}.log" if date_filter else "veritasloop_*.log"
    return sorted(log_dir.glob(pattern))


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Analyze VeritasLoop log files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "log_file",
        nargs="?",
        type=str,
        help="Path to specific log file to analyze",
    )

    parser.add_argument(
        "--date",
        "-d",
        type=str,
        help="Analyze logs for specific date (YYYYMMDD format)",
    )

    parser.add_argument(
        "--all",
        "-a",
        action="store_true",
        help="Analyze all log files",
    )

    parser.add_argument(
        "--export",
        "-e",
        type=str,
        help="Export analysis to JSON file",
    )

    args = parser.parse_args()

    # Determine project root and logs directory
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    logs_dir = project_root / "logs"

    # Determine which log files to analyze
    log_files = []

    if args.log_file:
        # Specific log file provided
        log_files = [Path(args.log_file)]
    elif args.date:
        # Filter by date
        log_files = find_log_files(logs_dir, args.date)
    elif args.all:
        # All log files
        log_files = find_log_files(logs_dir)
    else:
        # Default: today's log
        today = datetime.now().strftime("%Y%m%d")
        log_files = find_log_files(logs_dir, today)

    if not log_files:
        print("No log files found!")
        sys.exit(1)

    # Analyze each log file
    for log_file in log_files:
        analyzer = LogAnalyzer(log_file)
        analyzer.analyze_file()
        analyzer.print_summary()

        # Export if requested
        if args.export:
            export_path = Path(args.export)
            if len(log_files) > 1:
                # Multiple files: add date to filename
                date_str = log_file.stem.split("_")[-1]
                export_path = export_path.with_stem(f"{export_path.stem}_{date_str}")

            analyzer.export_json(export_path)

        # Add separator if analyzing multiple files
        if len(log_files) > 1:
            print("\n" + "=" * 60 + "\n")


if __name__ == "__main__":
    main()
