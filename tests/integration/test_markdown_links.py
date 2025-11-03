"""Integration test for validating links in markdown files."""

import re
import urllib.error
import urllib.request
from functools import reduce
from pathlib import Path

import pytest


class TestMarkdownLinks:
  """Integration tests for markdown link validation."""

  @pytest.fixture
  def project_root(self) -> Path:
    """Get the project root directory."""
    return Path(__file__).parents[2]

  @pytest.fixture
  def markdown_files(self, project_root: Path) -> list[Path]:
    """Get all markdown files in the project."""
    markdown_files: list[Path] = []

    # Add root markdown files
    for pattern in ['*.md']:
      markdown_files.extend(project_root.glob(pattern))

    # Add docs markdown files recursively
    docs_dir = project_root / 'docs'
    if docs_dir.exists():
      markdown_files.extend(docs_dir.rglob('*.md'))

    return sorted(markdown_files)

  def extract_links(self, content: str, file_path: Path) -> list[tuple[str, int, str]]:
    """
    Extract all links from markdown content.

    :param content: Markdown file content
    :param file_path: Path to the markdown file for context
    :return: List of (link_url, line_number, link_type) tuples
    """
    links = []
    lines = content.split('\n')

    # Regex patterns for different link types
    patterns = [
      # Standard markdown links: [text](url)
      (r'\[([^\]]*)\]\(([^)]+)\)', 'markdown_link'),
      # Reference links: [text]: url
      (r'^\s*\[([^\]]*)\]:\s*(.+)$', 'reference_link'),
      # Image links: ![alt](url)
      (r'!\[([^\]]*)\]\(([^)]+)\)', 'image_link'),
      # HTML links: <a href="url">
      (r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>', 'html_link'),
      # Plain URLs: http(s)://...
      (r'(?<!["\'\(])https?://[^\s<>\[\]]+(?!["\'\)])', 'plain_url'),
    ]

    exclude = [
      "https://httpbin.org"
    ]

    for line_num, line in enumerate(lines, 1):
      for pattern, link_type in patterns:
        matches = re.finditer(pattern, line, re.IGNORECASE)
        for match in matches:
          if link_type == 'plain_url':
            url = match.group(0)
          else:
            url = match.group(2) if len(match.groups()) > 1 else match.group(1)

          if [e for e in exclude if e in url]:
            continue

          # Skip empty links and anchors only
          if url and not url.startswith('#'):
            links.append((url.strip(), line_num, link_type))

    return links

  def is_external_url(self, url: str) -> bool:
    """Check if URL is external (http/https)."""
    return url.lower().startswith(('http://', 'https://'))

  def is_false_positive_url(self, url: str) -> bool:
    """Check if URL is a known false positive that shouldn't be tested."""
    false_positives = [
      # Git URLs with @ suffixes (not meant to be HTTP accessible)
      r'\.git@',
      # Malformed URLs from code snippets
      r'https?://["\')]',
      # URLs ending with quote characters (likely from code/examples)
      r'https?://[^"\']*["\')]$',
    ]

    import re

    for pattern in false_positives:
      if re.search(pattern, url):
        return True
    return False

  def is_valid_external_url(self, url: str) -> tuple[bool, str]:
    """
    Check if external URL is valid by making a HEAD request.

    :param url: URL to check
    :return: (is_valid, error_message)
    """
    if not self.is_external_url(url):
      return True, ''

    try:
      # Create request with User-Agent header to avoid blocking
      req = urllib.request.Request(url, method='HEAD')  # noqa: S310 # testing URLs
      req.add_header('User-Agent', 'Mozilla/5.0 (compatible; Freyja-LinkChecker/1.0)')

      with urllib.request.urlopen(req, timeout=10) as response:  # noqa: S310 # testing URLs
        # Accept any 2xx or 3xx status code
        return 200 <= response.status < 400, ''

    except urllib.error.HTTPError as e:
      # Some servers return 405 for HEAD requests, try GET with range
      if e.code == 405:
        try:
          req = urllib.request.Request(url)  # noqa: S310 # testing URLs
          req.add_header('User-Agent', 'Mozilla/5.0 (compatible; Freyja-LinkChecker/1.0)')
          req.add_header('Range', 'bytes=0-1023')  # Only get first 1KB

          with urllib.request.urlopen(  # noqa: S310 # testing URLs
            req, timeout=10
          ) as response:
            return 200 <= response.status < 400, ''
        except Exception as inner_e:
          return False, f'HTTP {e.code}: {e.reason} (fallback failed: {inner_e})'
      return False, f'HTTP {e.code}: {e.reason}'

    except urllib.error.URLError as e:
      return False, f'URL Error: {e.reason}'

    except Exception as e:
      return False, f'Unexpected error: {e}'

  def resolve_relative_path(self, base_path: Path, relative_url: str) -> Path:
    """
    Resolve relative path from base file location.

    :param base_path: Base file path
    :param relative_url: Relative URL to resolve
    :return: Resolved absolute path
    """
    # Remove query strings and fragments
    clean_url = relative_url.split('?')[0].split('#')[0]

    # Resolve relative to the directory containing the markdown file
    base_dir = base_path.parent
    resolved = (base_dir / clean_url).resolve()

    return resolved

  def is_valid_relative_path(self, base_path: Path, relative_url: str) -> tuple[bool, str]:
    """
    Check if relative path exists.

    :param base_path: Base file path
    :param relative_url: Relative URL to check
    :return: (is_valid, error_message)
    """
    if self.is_external_url(relative_url):
      return True, ''

    try:
      resolved_path = self.resolve_relative_path(base_path, relative_url)

      if not resolved_path.exists():
        return False, f'File not found: {resolved_path}'

      # Get project root - find the root that contains both freyja/ and docs/
      project_root = base_path
      while project_root.parent != project_root:
        if (project_root / 'freyja').exists() or (project_root / 'pyproject.toml').exists():
          break
        project_root = project_root.parent

      # Check if it's within the project (but allow docs navigation)
      try:
        resolved_path.relative_to(project_root)
        # Allow paths within the project structure
        return True, ''
      except ValueError:
        return False, f'Path outside project: {resolved_path}'

    except Exception as e:
      return False, f'Path resolution error: {e}'

  def test_markdown_files_exist(self, markdown_files: list[Path]) -> None:
    """Test that we found markdown files to validate."""
    assert len(markdown_files) > 0, 'No markdown files found to validate'

    # Verify key files exist
    file_names = {f.name for f in markdown_files}
    assert 'README.md' in file_names, 'Root README.md not found'
    assert 'CLAUDE.md' in file_names, 'CLAUDE.md not found'

  def test_all_relative_links_valid(self, markdown_files: list[Path]) -> None:
    """Test that all relative links in markdown files point to valid locations."""
    failed_links = []

    # Get project root for relative path calculation
    project_root = markdown_files[0] if markdown_files else Path.cwd()
    while project_root.parent != project_root:
      if (project_root / 'freyja').exists() or (project_root / 'pyproject.toml').exists():
        break
      project_root = project_root.parent

    for md_file in markdown_files:
      content = md_file.read_text(encoding='utf-8')
      links = self.extract_links(content, md_file)

      for url, line_num, link_type in links:
        if not self.is_external_url(url):
          is_valid, error_msg = self.is_valid_relative_path(md_file, url)
          if not is_valid:
            try:
              relative_file_path = md_file.relative_to(project_root)
            except ValueError:
              relative_file_path = md_file.name

            failed_links.append(
              {
                'file': str(relative_file_path),
                'line': line_num,
                'url': url,
                'type': link_type,
                'error': error_msg,
              }
            )

    if failed_links:
      error_msg = 'Invalid relative links found:\n'
      for link in failed_links:
        error_msg += (
          f'  {link["file"]}:{link["line"]} - {link["url"]} ({link["type"]}) - {link["error"]}\n'
        )

      pytest.fail(error_msg)

  @pytest.mark.slow
  def test_external_links_accessible(self, markdown_files: list[Path]) -> None:
    """Test that external links are accessible (marked as slow test)."""
    failed_links = []
    tested_urls = set()  # Avoid testing same URL multiple times

    for md_file in markdown_files:
      content = md_file.read_text(encoding='utf-8')
      links = self.extract_links(content, md_file)

      for url, line_num, link_type in links:
        if (
          self.is_external_url(url)
          and url not in tested_urls
          and not self.is_false_positive_url(url)
        ):
          tested_urls.add(url)
          is_valid, error_msg = self.is_valid_external_url(url)
          if not is_valid:
            failed_links.append(
              {
                'file': str(
                  md_file.relative_to(
                    md_file.parents[2] if 'tests' in str(md_file) else md_file.parents[0]
                  )
                ),
                'line': line_num,
                'url': url,
                'type': link_type,
                'error': error_msg,
              }
            )

    if failed_links:
      error_msg = 'Inaccessible external links found:\n'
      for link in failed_links:
        error_msg += (
          f'  {link["file"]}:{link["line"]} - {link["url"]} ({link["type"]}) - {link["error"]}\n'
        )

      # Make this a warning instead of failure for external links
      # since external services may be temporarily unavailable
      import warnings

      warnings.warn(f'External link validation issues:\n{error_msg}', stacklevel=2)

  def test_no_broken_internal_references(self, markdown_files: list[Path]) -> None:
    """Test that internal markdown references (anchors) are valid."""
    failed_refs = []

    # Get project root for relative path calculation
    project_root = markdown_files[0] if markdown_files else Path.cwd()
    while project_root.parent != project_root:
      if (project_root / 'freyja').exists() or (project_root / 'pyproject.toml').exists():
        break
      project_root = project_root.parent

    for md_file in markdown_files:
      content = md_file.read_text(encoding='utf-8')

      # Find all internal references (links with #)
      internal_links = re.findall(r'\[([^\]]*)\]\(([^)]*#[^)]+)\)', content)

      for _link_text, full_url in internal_links:
        if '#' in full_url:
          url_part, anchor = full_url.split('#', 1)

          # If url_part is empty, it's a same-file anchor
          if not url_part:
            target_file = md_file
          else:
            if self.is_external_url(url_part):
              continue  # Skip external anchors

            # Resolve relative path
            target_file = self.resolve_relative_path(md_file, url_part)
            if not target_file.exists():
              try:
                relative_file_path = md_file.relative_to(project_root)
              except ValueError:
                relative_file_path = md_file.name

              failed_refs.append(
                {
                  'file': str(relative_file_path),
                  'anchor': full_url,
                  'error': f'Target file not found: {target_file}',
                }
              )
              continue

          # Check if anchor exists in target file
          target_content = target_file.read_text(encoding='utf-8')

          # Generate possible anchor formats
          anchor_variants = [
            anchor.lower().replace(' ', '-').replace('_', '-'),
            anchor.lower().replace(' ', '').replace('_', ''),
            anchor.replace(' ', '-').replace('_', '-'),
          ]

          # Look for headers that could match this anchor
          headers = re.findall(r'^#+\s+(.+)$', target_content, re.MULTILINE)
          header_anchors = []
          for header in headers:
            # Strip markdown formatting and convert to anchor format
            clean_header = re.sub(r'[^\w\s-]', '', header).lower()
            header_anchors.extend(
              [
                clean_header.replace(' ', '-').replace('_', '-'),
                clean_header.replace(' ', '').replace('_', ''),
              ]
            )

          # Check if any variant matches
          if not any(
            variant in header_anchors or variant in target_content.lower()
            for variant in anchor_variants
          ):
            try:
              relative_file_path = md_file.relative_to(project_root)
            except ValueError:
              relative_file_path = md_file.name

            failed_refs.append(
              {
                'file': str(relative_file_path),
                'anchor': full_url,
                'error': f'Anchor #{anchor} not found in {target_file.name}',
              }
            )

    if failed_refs:
      error_msg = 'Broken internal references found:\n'
      for ref in failed_refs:
        error_msg += f'  {ref["file"]} - {ref["anchor"]} - {ref["error"]}\n'

      pytest.fail(error_msg)

  def test_link_extraction_accuracy(self, project_root: Path) -> None:
    """Test that link extraction works correctly with sample content."""
    sample_content = """
# Test Document

[Standard link](./docs/README.md)
[External link](https://github.com/terracoil/freyja)
![Image](./images/logo.png)
[Reference link][ref1]
<a href="./manual-link.html">HTML link</a>
Plain URL: https://pypi.org/project/freyja/

[ref1]: ./referenced.md
"""

    test_file = project_root / 'test.md'
    links = self.extract_links(sample_content, test_file)

    # Should extract all links
    assert len(links) >= 6, f'Expected at least 6 links, got {len(links)}'

    # Check specific link types are found
    link_urls = [url for url, _, _ in links]
    assert './docs/README.md' in link_urls
    assert 'https://github.com/terracoil/freyja' in link_urls
    assert './images/logo.png' in link_urls
    assert 'https://pypi.org/project/freyja/' in link_urls
