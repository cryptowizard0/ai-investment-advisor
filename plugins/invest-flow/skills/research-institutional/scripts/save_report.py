#!/usr/bin/env python3
"""
Save institutional accumulation/distribution analysis report to project directory.

Usage:
    save_report.py <report-file.md> <ticker>
    save_report.py --content "<markdown-content>" <ticker>
    cat report.md | save_report.py - <ticker>

Examples:
    save_report.py analysis_TSLA.md TSLA
    save_report.py --content "# Report..." AAPL
    python save_report.py - TSLA < report.md

Output:
    ./output/research-institutional/research-institutional-{YYYYMMDD}-{TICKER}.md
"""

import sys
import os
from pathlib import Path
from datetime import datetime
import argparse


def get_output_directory():
    """Get the output directory path.
    
    Returns:
        Path: Output directory at ./output/research-institutional/
    """
    # Standard output path: ./output/research-institutional/
    # This aligns with SKILL.md documentation
    output_dir = Path.cwd() / "output" / "research-institutional"
    
    # Also check if we're being run from the skill's scripts directory
    if "scripts" in Path.cwd().name or ".agents" in str(Path.cwd()) or ".claude" in str(Path.cwd()):
        # Navigate to project root by looking for project markers
        project_root = Path.cwd()
        found_root = False

        # Traverse up to find project root markers
        for parent in [project_root] + list(project_root.parents):
            if (parent / "CLAUDE.md").exists() or (parent / "AGENTS.md").exists():
                project_root = parent
                found_root = True
                break

        if found_root:
            output_dir = project_root / "output" / "research-institutional"
    
    return output_dir


def generate_filename(ticker):
    """Generate report filename with date and ticker."""
    date_str = datetime.now().strftime("%Y%m%d")
    return f"research-institutional-{date_str}-{ticker.upper()}.md"


def get_unique_filepath(output_dir, filename):
    """
    Generate a unique file path. If file exists, append (1), (2), etc.

    Args:
        output_dir: Output directory path
        filename: Desired filename

    Returns:
        Unique Path object
    """
    filepath = output_dir / filename

    # If file doesn't exist, return as-is
    if not filepath.exists():
        return filepath

    # Split filename into stem and suffix
    stem = Path(filename).stem
    suffix = Path(filename).suffix

    # Find next available number
    counter = 1
    while True:
        new_filename = f"{stem}({counter}){suffix}"
        new_filepath = output_dir / new_filename
        if not new_filepath.exists():
            return new_filepath
        counter += 1


def save_report(content, ticker, output_dir=None):
    """
    Save the report to the specified directory.

    Args:
        content: Report content as string
        ticker: Stock ticker symbol
        output_dir: Optional custom output directory

    Returns:
        Path to saved file
    """
    if output_dir is None:
        output_dir = get_output_directory()

    # Create directory if it doesn't exist
    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate filename
    filename = generate_filename(ticker)

    # Get unique filepath (avoid overwriting)
    filepath = get_unique_filepath(output_dir, filename)

    # Write report to file
    filepath.write_text(content, encoding='utf-8')

    return filepath


def read_report_file(filepath):
    """Read report content from file."""
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Report file not found: {filepath}")
    return path.read_text(encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(
        description='Save institutional accumulation analysis report'
    )
    parser.add_argument('input', help='Input file path, "-" for stdin, or "--content" for direct string')
    parser.add_argument('ticker', help='Stock ticker symbol (e.g., TSLA, AAPL)')
    parser.add_argument('--content', action='store_true', help='Treat input as content string instead of file path')
    parser.add_argument('--stdin', action='store_true', help='Read content from stdin')
    parser.add_argument('--output-dir', '-o', help='Custom output directory (default: ./output/research-institutional/)')

    args = parser.parse_args()

    # Get report content
    if args.stdin or args.input == '-':
        content = sys.stdin.read()
    elif args.content:
        content = args.input
    else:
        content = read_report_file(args.input)

    # Determine output directory
    output_dir = Path(args.output_dir) if args.output_dir else None

    try:
        # Save report
        saved_path = save_report(content, args.ticker, output_dir)
        print(f"✅ Report saved to: {saved_path}")
        print(f"   Ticker: {args.ticker.upper()}")
        print(f"   Date: {datetime.now().strftime('%Y-%m-%d')}")
        return 0
    except Exception as e:
        print(f"❌ Error saving report: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
