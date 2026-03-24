"""
Highlight Service - Phase 6 Task 035
Search result highlighting and snippet generation
"""

import re
from typing import List, Optional
from html import escape
from django.utils.html import strip_tags


class HighlightService:
    """
    Service for highlighting search keywords in text.

    Features:
    - Configurable highlight tags (default <mark>)
    - Case-insensitive matching
    - HTML escaping for XSS protection
    - Multiple keyword support
    - Partial match support
    """

    DEFAULT_START_TAG = '<mark>'
    DEFAULT_END_TAG = '</mark>'

    def __init__(self):
        """Initialize highlight service."""
        pass

    def highlight(
        self,
        text: str,
        keywords: List[str],
        start_tag: Optional[str] = None,
        end_tag: Optional[str] = None
    ) -> str:
        """
        Highlight keywords in text.

        Args:
            text: Text to highlight
            keywords: List of keywords to highlight
            start_tag: Opening highlight tag (default <mark>)
            end_tag: Closing highlight tag (default </mark>)

        Returns:
            Text with highlighted keywords
        """
        if not text:
            return ''

        if not keywords:
            return escape(text)

        # Use default tags if not provided
        start = start_tag or self.DEFAULT_START_TAG
        end = end_tag or self.DEFAULT_END_TAG

        # Escape HTML to prevent XSS
        escaped_text = escape(text)

        # Sort keywords by length (longest first) to avoid partial replacements
        sorted_keywords = sorted(
            [k for k in keywords if k],
            key=len,
            reverse=True
        )

        if not sorted_keywords:
            return escaped_text

        # Build pattern for all keywords
        # Use word boundaries for better matching
        escaped_keywords = [re.escape(k) for k in sorted_keywords]
        pattern = '|'.join(escaped_keywords)

        # Find all matches first
        matches = list(re.finditer(pattern, escaped_text, re.IGNORECASE))

        if not matches:
            return escaped_text

        # Build result by interleaving text and highlighted matches
        result_parts = []
        last_end = 0

        for match in matches:
            # Add text before this match
            result_parts.append(escaped_text[last_end:match.start()])
            # Add highlighted match
            result_parts.append(start)
            result_parts.append(match.group(0))
            result_parts.append(end)
            last_end = match.end()

        # Add remaining text after last match
        result_parts.append(escaped_text[last_end:])

        return ''.join(result_parts)

    def highlight_positions(
        self,
        text: str,
        keywords: List[str]
    ) -> List[dict]:
        """
        Get highlight positions without modifying text.

        Args:
            text: Text to analyze
            keywords: List of keywords

        Returns:
            List of position dictionaries with start, end, keyword
        """
        if not text or not keywords:
            return []

        positions = []

        for keyword in keywords:
            if not keyword:
                continue

            # Find all occurrences
            pattern = re.escape(keyword)
            for match in re.finditer(pattern, text, re.IGNORECASE):
                positions.append({
                    'start': match.start(),
                    'end': match.end(),
                    'keyword': match.group(0),
                    'original': keyword
                })

        # Sort by position
        positions.sort(key=lambda x: x['start'])

        return positions


class SnippetService:
    """
    Service for generating text snippets with context.

    Features:
    - Context extraction around keywords
    - Max length enforcement
    - Ellipsis for truncated content
    - Multiple snippet extraction
    - Overlap prevention
    """

    DEFAULT_CONTEXT_SIZE = 30
    DEFAULT_MAX_LENGTH = 150
    DEFAULT_MAX_SNIPPETS = 3

    def __init__(self):
        """Initialize snippet service."""
        pass

    def generate(
        self,
        text: str,
        keywords: List[str],
        context_size: int = DEFAULT_CONTEXT_SIZE,
        max_length: int = DEFAULT_MAX_LENGTH,
        max_snippets: int = DEFAULT_MAX_SNIPPETS,
        ellipsis: str = '...'
    ) -> str:
        """
        Generate snippet from text with keyword context.

        Args:
            text: Source text
            keywords: Keywords to find
            context_size: Characters of context around keyword
            max_length: Maximum snippet length
            max_snippets: Maximum number of snippets to include
            ellipsis: String to indicate truncation

        Returns:
            Generated snippet
        """
        if not text:
            return ''

        if not keywords:
            # Return first max_length characters if no keywords
            if len(text) <= max_length:
                return text
            return text[:max_length - len(ellipsis)] + ellipsis

        # Find all keyword positions
        highlight_service = HighlightService()
        positions = highlight_service.highlight_positions(text, keywords)

        if not positions:
            # No keywords found, return beginning
            if len(text) <= max_length:
                return text
            return text[:max_length - len(ellipsis)] + ellipsis

        # Extract snippets around keyword positions
        snippets = []
        covered_range = set()
        keyword_count = 0

        for pos in positions:
            # Stop if we've included enough snippets/keywords
            if keyword_count >= max_snippets:
                break

            # Calculate snippet boundaries
            snippet_start = max(0, pos['start'] - context_size)
            snippet_end = min(len(text), pos['end'] + context_size)

            # Check for overlap with existing snippets
            overlap = False
            for i in range(snippet_start, snippet_end):
                if i in covered_range:
                    overlap = True
                    break

            if not overlap:
                snippet = text[snippet_start:snippet_end]
                snippets.append((snippet_start, snippet_end, snippet))
                keyword_count += 1

                # Mark as covered
                for i in range(snippet_start, snippet_end):
                    covered_range.add(i)

        if not snippets:
            # All positions overlapped, return first match with context
            first_pos = positions[0]
            start = max(0, first_pos['start'] - context_size)
            end = min(len(text), first_pos['end'] + context_size)
            return text[start:end]

        # Sort snippets by position
        snippets.sort(key=lambda x: x[0])

        # Combine snippets with ellipsis between
        result_parts = []
        for i, (start, end, snippet) in enumerate(snippets):
            if i > 0:
                result_parts.append(ellipsis)
            result_parts.append(snippet)

        result = ''.join(result_parts)

        # Add ellipsis if truncated
        if snippets[0][0] > 0:
            result = ellipsis + result
        if snippets[-1][1] < len(text):
            result = result + ellipsis

        # Enforce max length
        if len(result) > max_length:
            # Truncate intelligently
            result = self._truncate_intelligently(result, max_length, ellipsis)

        return result

    def generate_multiple(
        self,
        text: str,
        keywords: List[str],
        max_snippets: int = DEFAULT_MAX_SNIPPETS,
        context_size: int = DEFAULT_CONTEXT_SIZE
    ) -> List[str]:
        """
        Generate multiple snippets from text.

        Args:
            text: Source text
            keywords: Keywords to find
            max_snippets: Maximum number of snippets
            context_size: Characters of context

        Returns:
            List of snippet strings
        """
        if not text or not keywords:
            return []

        highlight_service = HighlightService()
        positions = highlight_service.highlight_positions(text, keywords)

        if not positions:
            return []

        snippets = []
        covered_range = set()

        for pos in positions[:max_snippets]:
            snippet_start = max(0, pos['start'] - context_size)
            snippet_end = min(len(text), pos['end'] + context_size)

            # Check for overlap
            overlap = False
            for i in range(snippet_start, snippet_end):
                if i in covered_range:
                    overlap = True
                    break

            if not overlap:
                snippet = text[snippet_start:snippet_end]
                snippets.append(snippet)

                for i in range(snippet_start, snippet_end):
                    covered_range.add(i)

        return snippets

    def _truncate_intelligently(
        self,
        text: str,
        max_length: int,
        ellipsis: str
    ) -> str:
        """
        Truncate text intelligently at word boundary.

        Args:
            text: Text to truncate
            max_length: Maximum length
            ellipsis: Ellipsis string

        Returns:
            Truncated text
        """
        if len(text) <= max_length:
            return text

        # Leave room for ellipsis
        target_length = max_length - len(ellipsis)

        # Find last space before target length
        truncated = text[:target_length]
        last_space = truncated.rfind(' ')

        if last_space > target_length * 0.8:
            # Truncate at word boundary
            return text[:last_space] + ellipsis
        else:
            # Just truncate at target length
            return truncated + ellipsis


class SearchResultFormatter:
    """
    Formatter for search results with highlighting.

    Combines highlighting and snippet generation for complete
    search result formatting.
    """

    def __init__(self):
        """Initialize formatter."""
        self.highlight_service = HighlightService()
        self.snippet_service = SnippetService()

    def format_result(
        self,
        result: dict,
        query: str,
        highlight_title: bool = True,
        highlight_description: bool = True,
        generate_snippet: bool = True
    ) -> dict:
        """
        Format search result with highlighting.

        Args:
            result: Search result dictionary
            query: Search query
            highlight_title: Whether to highlight title
            highlight_description: Whether to highlight description
            generate_snippet: Whether to generate snippet

        Returns:
            Formatted result with highlighting
        """
        keywords = query.split() if query else []

        formatted = result.copy()

        if highlight_title and 'title' in result:
            formatted['highlighted_title'] = self.highlight_service.highlight(
                result['title'],
                keywords
            )

        if 'description' in result:
            if generate_snippet:
                formatted['snippet'] = self.snippet_service.generate(
                    result['description'],
                    keywords
                )
                # Highlight the snippet too
                formatted['snippet'] = self.highlight_service.highlight(
                    formatted['snippet'],
                    keywords
                )

            if highlight_description:
                formatted['highlighted_description'] = self.highlight_service.highlight(
                    result['description'],
                    keywords
                )

        return formatted

    def format_results(
        self,
        results: List[dict],
        query: str,
        **kwargs
    ) -> List[dict]:
        """
        Format multiple search results.

        Args:
            results: List of result dictionaries
            query: Search query
            **kwargs: Additional options for format_result

        Returns:
            List of formatted results
        """
        return [
            self.format_result(result, query, **kwargs)
            for result in results
        ]

