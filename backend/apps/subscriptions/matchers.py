"""
Matcher Classes - Phase 8 Tasks 044-045
Pattern matching utilities for keyword matching
"""

import re
import unicodedata
from abc import ABC, abstractmethod
from typing import Optional
from functools import lru_cache


class Matcher(ABC):
    """Abstract base class for matchers."""

    @abstractmethod
    def match(self, text: str, pattern: str, case_sensitive: bool = False) -> bool:
        """Check if text matches pattern."""
        pass

    def validate_pattern(self, pattern: str) -> bool:
        """Validate pattern is valid for this matcher type."""
        return True

    def _normalize_text(self, text: str) -> str:
        """Normalize unicode text."""
        return unicodedata.normalize('NFKC', text)


class ExactMatcher(Matcher):
    """Exact string equality matching."""

    def match(self, text: str, pattern: str, case_sensitive: bool = False) -> bool:
        """Match exact string equality."""
        text = self._normalize_text(text)
        pattern = self._normalize_text(pattern)

        if not case_sensitive:
            text = text.lower()
            pattern = pattern.lower()

        return text == pattern


class ContainsMatcher(Matcher):
    """Substring containment matching."""

    def match(self, text: str, pattern: str, case_sensitive: bool = False) -> bool:
        """Match if pattern is contained in text."""
        text = self._normalize_text(text)
        pattern = self._normalize_text(pattern)

        if not case_sensitive:
            text = text.lower()
            pattern = pattern.lower()

        return pattern in text


class StartsWithMatcher(Matcher):
    """Prefix matching."""

    def match(self, text: str, pattern: str, case_sensitive: bool = False) -> bool:
        """Match if text starts with pattern."""
        text = self._normalize_text(text)
        pattern = self._normalize_text(pattern)

        if not case_sensitive:
            text = text.lower()
            pattern = pattern.lower()

        return text.startswith(pattern)


class EndsWithMatcher(Matcher):
    """Suffix matching."""

    def match(self, text: str, pattern: str, case_sensitive: bool = False) -> bool:
        """Match if text ends with pattern."""
        text = self._normalize_text(text)
        pattern = self._normalize_text(pattern)

        if not case_sensitive:
            text = text.lower()
            pattern = pattern.lower()

        return text.endswith(pattern)


class RegexMatcher(Matcher):
    """Regular expression matching with pattern caching."""

    def __init__(self, cache_size: int = 1000):
        self.cache_size = cache_size

    @lru_cache(maxsize=1000)
    def _compile_pattern(self, pattern: str, flags: int = 0) -> re.Pattern:
        """Compile and cache regex pattern."""
        return re.compile(pattern, flags)

    def match(self, text: str, pattern: str, case_sensitive: bool = False) -> bool:
        """Match using regex pattern."""
        text = self._normalize_text(text)
        pattern = self._normalize_text(pattern)

        flags = 0 if case_sensitive else re.IGNORECASE

        try:
            compiled = self._compile_pattern(pattern, flags)
            return bool(compiled.search(text))
        except re.error:
            return False

    def validate_pattern(self, pattern: str) -> bool:
        """Validate regex pattern syntax."""
        try:
            re.compile(pattern)
            return True
        except re.error:
            return False

    def find_matches(self, text: str, pattern: str, case_sensitive: bool = False) -> list:
        """Find all regex matches and return match details."""
        text = self._normalize_text(text)
        pattern = self._normalize_text(pattern)

        flags = 0 if case_sensitive else re.IGNORECASE

        try:
            compiled = self._compile_pattern(pattern, flags)
            matches = []
            for match in compiled.finditer(text):
                matches.append({
                    'start': match.start(),
                    'end': match.end(),
                    'matched_text': match.group(),
                    'groups': match.groups()
                })
            return matches
        except re.error:
            return []


class MatcherFactory:
    """Factory for creating matcher instances."""

    _matchers = {
        'exact': ExactMatcher(),
        'contains': ContainsMatcher(),
        'starts_with': StartsWithMatcher(),
        'ends_with': EndsWithMatcher(),
        'regex': RegexMatcher(),
    }

    @classmethod
    def get_matcher(cls, match_type: str) -> Matcher:
        """Get matcher instance by type."""
        matcher = cls._matchers.get(match_type)
        if not matcher:
            raise ValueError(f'Unknown match type: {match_type}')
        return matcher

    @classmethod
    def register_matcher(cls, match_type: str, matcher: Matcher):
        """Register a custom matcher."""
        cls._matchers[match_type] = matcher

    @classmethod
    def get_available_types(cls) -> list:
        """Get list of available match types."""
        return list(cls._matchers.keys())
