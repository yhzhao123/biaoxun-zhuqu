# Task 035: Search Highlight Implementation (Result Highlighting & Snippets)

## Task Header
| Field | Value |
|-------|-------|
| ID | 035 |
| Name | 搜索结果高亮实现 |
| Type | impl |
| Depends-on | 034 |

## Description

Implement search result highlighting with keyword marking and intelligent snippet generation. Use PostgreSQL's ts_headline() for database-level highlighting and implement client-side snippet extraction for optimal performance.

## Files to Create/Modify

### New Files
- `src/modules/search/services/highlight.service.ts` - Highlight generation service
- `src/modules/search/services/snippet.service.ts` - Snippet extraction service
- `src/modules/search/dto/highlight-options.dto.ts` - Highlight configuration DTO
- `src/modules/search/interfaces/highlight-result.interface.ts` - Result types

### Modify Files
- `src/modules/search/services/fulltext-search.service.ts` - Integrate highlighting
- `src/modules/search/dto/search-result.dto.ts` - Add highlighted fields
- `src/modules/search/search.controller.ts` - Add highlight options parameter

## Implementation Steps

1. **Database-Level Highlighting (Optional)**
   - Use `ts_headline()` in PostgreSQL query for server-side highlighting
   - Configure: `StartSel=<mark>, StopSel=</mark>, MaxWords=50, MinWords=10`
   - Consider performance trade-off vs client-side highlighting

2. **HighlightOptionsDto**
   - `@IsOptional()` `@IsString()` preTag: string = '<mark>'
   - `@IsOptional()` `@IsString()` postTag: string = '</mark>'
   - `@IsOptional()` `@IsNumber()` snippetMaxLength: number = 300
   - `@IsOptional()` `@IsNumber()` snippetContextWords: number = 5
   - `@IsOptional()` `@IsBoolean()` highlightTitle: boolean = true
   - `@IsOptional()` `@IsBoolean()` highlightContent: boolean = true

3. **HighlightService**
   - `highlightText(text: string, keywords: string[], options: HighlightOptions)`
   - Escape HTML special characters before highlighting
   - Use regex with word boundaries for keyword matching
   - Support case-insensitive highlighting
   - Handle overlapping matches correctly
   - Return highlighted HTML string

   ```typescript
   highlightText(text: string, keywords: string[], options: HighlightOptions): string {
     const escapedKeywords = keywords.map(k => this.escapeRegex(k));
     const pattern = new RegExp(`(${escapedKeywords.join('|')})`, 'gi');
     return text.replace(pattern, `${options.preTag}$1${options.postTag}`);
   }
   ```

4. **SnippetService**
   - `generateSnippet(content: string, keywords: string[], maxLength: number)`
   - Find best snippet position (most keyword density)
   - Extract context around keywords
   - Add ellipsis for truncated content: '...snippet...'
   - Handle content without matches (return first N chars)
   - Preserve word boundaries in truncation

   ```typescript
   generateSnippet(content: string, keywords: string[], maxLength: number): string {
     // Find occurrence with most keyword matches within window
     // Extract snippet with context
     // Truncate at word boundaries
     // Add ellipsis indicators
   }
   ```

5. **SearchResultDto Updates**
   - Add `titleHighlighted?: string` field
   - Add `contentSnippet?: string` field
   - Add `contentHighlighted?: string` field (optional full content)
   - Keep original `title` and `content` for fallback

6. **FulltextSearchService Integration**
   - Parse search query to extract keywords
   - Call HighlightService for title highlighting
   - Call SnippetService for content snippet
   - Include highlight options in search method signature
   - Return enriched SearchResultDto with highlighted fields

7. **Response Sanitization**
   - Use DOMPurify or similar to sanitize highlighted output
   - Prevent XSS from malicious search queries
   - Ensure highlight tags are properly closed

8. **Performance Optimization**
   - Cache highlight results for repeated queries
   - Limit snippet generation to top N results only
   - Use streaming for large result sets

## Verification Steps

1. Test API with query param: `GET /api/search?q=采购&highlight=true`
2. Verify <mark> tags appear around matched keywords
3. Check snippet length is within configured max
4. Test with Chinese keywords: proper segmentation
5. Test with mixed Chinese/English content
6. Verify XSS protection: script tags should not execute
7. Performance: 1000 results with highlighting < 200ms
8. Visual check: Open results in browser, verify highlighting visible

## Git Commit Message

```
feat(search): implement search result highlighting and snippets

- Add HighlightService for keyword marking with configurable tags
- Implement SnippetService for intelligent excerpt generation
- Support Chinese and English keyword highlighting
- Add HighlightOptionsDto for client customization
- Integrate highlighting into full-text search results
- Include XSS protection for highlighted output
- Update SearchResultDto with highlighted fields

Refs: #035
```
