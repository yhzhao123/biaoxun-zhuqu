/**
 * ChatMessage component - Phase 4 Task 020-021
 * Memoized chat message component for AnalysisChatPage
 */

import React, { memo } from 'react';
import type { ChatMessage as ChatMessageType } from '../types/llm';

interface ChatMessageProps {
  message: ChatMessageType;
}

export const ChatMessage: React.FC<ChatMessageProps> = memo(({ message }) => {
  const isUser = message.role === 'user';

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div
        className={`max-w-3/4 rounded-lg px-4 py-2 ${
          isUser
            ? 'bg-blue-600 text-white'
            : 'bg-gray-100 text-gray-900'
        }`}
      >
        <div className="whitespace-pre-wrap text-sm">{message.content}</div>
        {message.metadata?.extracted_entities && !isUser && (
          <div className="mt-2 pt-2 border-t border-gray-200">
            <div className="text-xs font-medium text-gray-500 mb-1">提取的实体：</div>
            <div className="flex flex-wrap gap-1">
              {Object.entries(message.metadata.extracted_entities).map(([key, value]) => (
                <span
                  key={key}
                  className="inline-flex items-center px-2 py-0.5 rounded text-xs bg-blue-100 text-blue-800"
                >
                  {key}: {String(value)}
                </span>
              ))}
            </div>
          </div>
        )}
        {message.timestamp && (
          <div className={`text-xs mt-1 ${isUser ? 'text-blue-200' : 'text-gray-400'}`}>
            {new Date(message.timestamp).toLocaleTimeString()}
          </div>
        )}
      </div>
    </div>
  );
});

ChatMessage.displayName = 'ChatMessage';

export default ChatMessage;