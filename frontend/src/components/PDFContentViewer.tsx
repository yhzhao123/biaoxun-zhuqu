/**
 * PDFContentViewer - Display extracted PDF content with search functionality
 */

import React, { useState, useMemo } from 'react';

interface PDFContentViewerProps {
  content?: string;
  maxHeight?: string;
}

export const PDFContentViewer: React.FC<PDFContentViewerProps> = ({
  content,
  maxHeight = '500px',
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [isExpanded, setIsExpanded] = useState(true);

  if (!content || content.trim() === '') {
    return (
      <div className="text-gray-500 text-center py-8">
        暂无PDF内容
      </div>
    );
  }

  const wordCount = content.length;

  // Highlight search matches
  const highlightedContent = useMemo(() => {
    if (!searchTerm.trim()) {
      return content;
    }

    const regex = new RegExp(`(${searchTerm})`, 'gi');
    return content.split(regex).map((part, index) =>
      regex.test(part) ? (
        <mark key={index} className="bg-yellow-200 px-0.5 rounded">
          {part}
        </mark>
      ) : (
        part
      )
    );
  }, [content, searchTerm]);

  const matchCount = useMemo(() => {
    if (!searchTerm.trim()) return 0;
    const regex = new RegExp(searchTerm, 'gi');
    return (content.match(regex) || []).length;
  }, [content, searchTerm]);

  return (
    <div className="border border-gray-200 rounded-lg overflow-hidden">
      {/* Header with search */}
      <div className="px-4 py-3 bg-gray-50 border-b border-gray-200 flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <span className="text-sm text-gray-600">
            字数: {wordCount.toLocaleString()}
          </span>
          {searchTerm && (
            <span className="text-sm text-gray-500">
              找到 {matchCount} 处匹配
            </span>
          )}
        </div>

        <div className="flex items-center space-x-2">
          <div className="relative">
            <input
              type="text"
              placeholder="搜索内容..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-48 px-3 py-1.5 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
            {searchTerm && (
              <button
                onClick={() => setSearchTerm('')}
                className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            )}
          </div>

          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="px-3 py-1.5 text-sm text-gray-600 hover:text-gray-900 flex items-center space-x-1"
          >
            <span>{isExpanded ? '收起' : '展开'}</span>
            <svg
              className={`w-4 h-4 transition-transform ${isExpanded ? 'rotate-180' : ''}`}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>
        </div>
      </div>

      {/* Content */}
      <div
        className="p-4 overflow-auto bg-white"
        style={{ maxHeight: isExpanded ? maxHeight : 'none' }}
      >
        <pre className="whitespace-pre-wrap text-sm text-gray-700 font-mono leading-relaxed">
          {highlightedContent}
        </pre>
      </div>
    </div>
  );
};

export default PDFContentViewer;