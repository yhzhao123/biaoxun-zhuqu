# Task 034: Search Highlight Tests (Result Highlighting Test)

## Task Header
| Field | Value |
|-------|-------|
| ID | 034 |
| Name | 搜索结果高亮测试 |
| Type | test |
| Depends-on | 031 |

## Description

Write comprehensive tests for search result highlighting and snippet generation functionality. Tests should verify correct highlighting of matched keywords, snippet extraction, and handling of various content lengths and edge cases.

## Files to Create/Modify

### New Files
- `src/modules/search/__tests__/highlight.service.spec.ts` - Unit tests for highlight service
- `src/modules/search/__tests__/snippet.service.spec.ts` - Unit tests for snippet generation
- `test/fixtures/search/highlight.fixtures.ts` - Test content with known matches

### Modify Files
- `src/modules/search/__tests__/fulltext-search.service.spec.ts` - Add highlight integration tests

## Implementation Steps

1. **Test Fixtures Setup**
   - Create bidding records with descriptive content:
     - Short titles (10-30 chars) with keywords
     - Long descriptions (500+ chars) with multiple keyword occurrences
     - Content with special characters, HTML, markdown
     - Unicode content (Chinese, English mixed)
   - Define expected highlights for each fixture

2. **Unit Tests - Highlight Generation**
   - `should wrap matched keywords in <mark> tags`
   - `should highlight multiple occurrences of same keyword`
   - `should highlight multiple different keywords`
   - `should be case-insensitive for highlighting`
   - `should highlight Chinese keywords correctly`
   - `should highlight English keywords correctly`
   - `should not highlight partial word matches (configurable)`

3. **Unit Tests - Snippet Generation**
   - `should extract snippet around first keyword occurrence`
   - `should extract snippet with multiple keywords in range`
   - `should handle content shorter than snippet length`
   - `should add ellipsis for truncated content`
   - `should prefer snippet with most keyword matches`
   - `should handle content with no keyword matches`
   - `should limit snippet to specified max length`
   - `should maintain word boundaries in snippet truncation`

4. **Unit Tests - Edge Cases**
   - `should handle empty content gracefully`
   - `should handle null content`
   - `should escape HTML in original content`
   - `should handle very long words`
   - `should handle keywords at content boundaries`
   - `should handle overlapping highlight regions`
   - `should handle special regex characters in keywords`

5. **Integration Tests**
   - `should return highlighted results from full search`
   - `should include snippet in search response`
   - `should highlight in both title and content`
   - `should verify highlight positions match search ranking`

6. **Performance Tests**
   - `should highlight 1000 results in < 100ms`
   - `should generate snippets for large content efficiently`

## Verification Steps

1. Run unit tests: `npm test -- highlight.service`
2. Run snippet tests: `npm test -- snippet.service`
3. Verify coverage: `npm run test:cov -- --collectCoverageFrom='src/modules/search/**/*highlight*'`
4. Target coverage: 90%+ lines for highlighting logic
5. Manual verification: Check actual HTML output for visual correctness
6. Test with real bidding content samples

## Git Commit Message

```
test(search): add search highlighting and snippet tests

- Create highlight fixtures with varied content types
- Add unit tests for keyword highlighting with <mark> tags
- Test Chinese and English keyword highlighting
- Add snippet generation tests with boundary handling
- Include edge cases: HTML, special chars, empty content
- Add performance tests for bulk highlighting
- Verify highlight positions match search results

Refs: #034
```
