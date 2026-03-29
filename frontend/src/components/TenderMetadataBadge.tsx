/**
 * TenderMetadataBadge - Display extraction method and confidence badges
 */

import React from 'react';

interface TenderMetadataBadgeProps {
  extraction_method?: string;
  extraction_confidence?: number;
}

export const TenderMetadataBadge: React.FC<TenderMetadataBadgeProps> = ({
  extraction_method,
  extraction_confidence,
}) => {
  if (!extraction_method && !extraction_confidence) {
    return null;
  }

  const getConfidenceColor = (confidence?: number) => {
    if (confidence === undefined || confidence === null) return 'bg-gray-100 text-gray-800';
    if (confidence >= 0.9) return 'bg-green-100 text-green-800';
    if (confidence >= 0.7) return 'bg-yellow-100 text-yellow-800';
    return 'bg-red-100 text-red-800';
  };

  const getConfidenceText = (confidence?: number) => {
    if (confidence === undefined || confidence === null) return '未知';
    return `${Math.round(confidence * 100)}%`;
  };

  const getMethodText = (method?: string) => {
    const methodMap: Record<string, string> = {
      'llm': 'LLM智能提取',
      'rule': '规则提取',
      'hybrid': '混合提取',
      'manual': '人工标注',
    };
    return method ? methodMap[method] || method : '未知';
  };

  return (
    <div className="flex items-center space-x-2">
      {extraction_method && (
        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
          {getMethodText(extraction_method)}
        </span>
      )}

      {extraction_confidence !== undefined && extraction_confidence !== null && (
        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getConfidenceColor(extraction_confidence)}`}>
          置信度: {getConfidenceText(extraction_confidence)}
        </span>
      )}
    </div>
  );
};

export default TenderMetadataBadge;