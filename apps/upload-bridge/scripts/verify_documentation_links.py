#!/usr/bin/env python3
"""
Verify All Documentation Links Work

Script to check all markdown links in documentation files.
Task 4.3 from remaining tasks plan.
"""

import re
import sys
from pathlib import Path
from typing import List, Dict, Tuple
from urllib.parse import urlparse


class DocumentationLinkChecker:
    """Check documentation links."""
    
    def __init__(self, docs_dir: Path):
        """Initialize checker."""
        self.docs_dir = docs_dir
        self.broken_links: List[Dict[str, str]] = []
        self.checked_files: List[str] = []
        self.all_files: List[Path] = []
    
    def find_markdown_files(self) -> List[Path]:
        """Find all markdown files in docs directory."""
        markdown_files = list(self.docs_dir.rglob("*.md"))
        return markdown_files
    
    def extract_links(self, file_path: Path) -> List[Tuple[str, str, int]]:
        """Extract all links from a markdown file.
        
        Returns: List of (link_text, link_url, line_number) tuples
        """
        links = []
        try:
            content = file_path.read_text(encoding='utf-8')
            lines = content.split('\n')
            
            # Pattern for markdown links: [text](url) or [text][ref]
            link_pattern = r'\[([^\]]+)\]\(([^\)]+)\)'
            
            for line_num, line in enumerate(lines, 1):
                matches = re.finditer(link_pattern, line)
                for match in matches:
                    link_text = match.group(1)
                    link_url = match.group(2)
                    links.append((link_text, link_url, line_num))
            
            # Also check for reference-style links: [text][ref]
            # This is more complex, so we'll focus on inline links for now
            
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
        
        return links
    
    def check_link(self, link_url: str, base_file: Path) -> Tuple[bool, str]:
        """Check if a link is valid.
        
        Returns: (is_valid, error_message)
        """
        # Skip anchor-only links
        if link_url.startswith('#'):
            return True, None
        
        # Skip external URLs (http/https)
        parsed = urlparse(link_url)
        if parsed.scheme in ('http', 'https', 'mailto'):
            return True, None  # External links - assume valid
        
        # Handle relative paths
        if link_url.startswith('/'):
            # Absolute path from docs root
            target_path = self.docs_dir / link_url[1:]
        else:
            # Relative path from current file
            target_path = base_file.parent / link_url
        
        # Handle anchor links (file#anchor)
        if '#' in str(target_path):
            file_part, anchor = str(target_path).split('#', 1)
            target_path = Path(file_part)
            # We don't check anchors for now, just file existence
        
        # Resolve path
        target_path = target_path.resolve()
        
        # Check if file exists
        if target_path.exists():
            return True, None
        else:
            return False, f"File not found: {target_path.relative_to(self.docs_dir)}"
    
    def check_file(self, file_path: Path):
        """Check all links in a file."""
        self.checked_files.append(str(file_path.relative_to(self.docs_dir)))
        links = self.extract_links(file_path)
        
        for link_text, link_url, line_num in links:
            is_valid, error = self.check_link(link_url, file_path)
            if not is_valid:
                self.broken_links.append({
                    'file': str(file_path.relative_to(self.docs_dir)),
                    'line': line_num,
                    'text': link_text,
                    'url': link_url,
                    'error': error
                })
    
    def check_all(self):
        """Check all documentation files."""
        print(f"Finding markdown files in {self.docs_dir}...")
        self.all_files = self.find_markdown_files()
        print(f"Found {len(self.all_files)} markdown files")
        
        print("\nChecking links...")
        for file_path in self.all_files:
            self.check_file(file_path)
        
        print(f"\nChecked {len(self.checked_files)} files")
        print(f"Found {len(self.broken_links)} broken links")
    
    def print_report(self):
        """Print report of broken links."""
        if not self.broken_links:
            print("\n✅ All links are valid!")
            return
        
        print("\n" + "=" * 80)
        print("BROKEN LINKS REPORT")
        print("=" * 80)
        
        # Group by file
        by_file = {}
        for link in self.broken_links:
            file = link['file']
            if file not in by_file:
                by_file[file] = []
            by_file[file].append(link)
        
        for file, links in sorted(by_file.items()):
            print(f"\n{file}:")
            for link in links:
                print(f"  Line {link['line']}: [{link['text']}]({link['url']})")
                print(f"    Error: {link['error']}")


def main():
    """Main entry point."""
    # Find docs directory (could be docs/ or apps/upload-bridge/docs/)
    script_dir = Path(__file__).parent.parent.parent
    docs_dir = script_dir / "docs"
    
    if not docs_dir.exists():
        # Try apps/upload-bridge/docs
        docs_dir = script_dir / "apps" / "upload-bridge" / "docs"
    
    if not docs_dir.exists():
        print(f"Error: Could not find docs directory")
        print(f"Tried: {script_dir / 'docs'}")
        print(f"Tried: {script_dir / 'apps' / 'upload-bridge' / 'docs'}")
        sys.exit(1)
    
    print(f"Checking documentation in: {docs_dir}")
    
    checker = DocumentationLinkChecker(docs_dir)
    checker.check_all()
    checker.print_report()
    
    # Exit with error code if broken links found
    sys.exit(0 if not checker.broken_links else 1)


if __name__ == "__main__":
    main()

