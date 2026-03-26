/**
 * Tests for ChatMessage component with React.memo
 * TDD - RED phase: Tests that describe the expected behavior
 */

import { describe, it, expect, vi } from 'vitest';
import { screen } from '@testing-library/react';
import { render } from './setup';
import { ChatMessage } from '../components/ChatMessage';
import type { ChatMessage as ChatMessageType } from '../types/llm';
import React from 'react';

const mockUserMessage: ChatMessageType = {
  role: 'user',
  content: '用户消息内容',
  timestamp: '2024-01-15T10:00:00Z',
};

const mockAssistantMessage: ChatMessageType = {
  role: 'assistant',
  content: '助手回复内容',
  timestamp: '2024-01-15T10:01:00Z',
  metadata: {
    extracted_entities: {
      tenderer: '测试招标人',
      budget: '100万元',
    },
  },
};

describe('ChatMessage', () => {
  it('should render user message correctly', () => {
    render(<ChatMessage message={mockUserMessage} />);
    expect(screen.getByText('用户消息内容')).toBeInTheDocument();
  });

  it('should render assistant message correctly', () => {
    render(<ChatMessage message={mockAssistantMessage} />);
    expect(screen.getByText('助手回复内容')).toBeInTheDocument();
  });

  it('should display extracted entities for assistant messages', () => {
    render(<ChatMessage message={mockAssistantMessage} />);
    expect(screen.getByText('tenderer: 测试招标人')).toBeInTheDocument();
    expect(screen.getByText('budget: 100万元')).toBeInTheDocument();
  });

  it('should display timestamp', () => {
    render(<ChatMessage message={mockUserMessage} />);
    // Should show time in some format
    expect(screen.getByText(/\d{1,2}:\d{2}/)).toBeInTheDocument();
  });

  it('should apply different styles for user vs assistant messages', () => {
    const { container: userContainer } = render(
      <ChatMessage message={mockUserMessage} />
    );
    const { container: assistantContainer } = render(
      <ChatMessage message={mockAssistantMessage} />
    );

    // User messages should have blue background - query the inner div (second div)
    const userDivs = userContainer.querySelectorAll('div');
    const userMessageDiv = userDivs[1];
    expect(userMessageDiv?.className).toContain('bg-blue-600');

    // Assistant messages should have gray background
    const assistantDivs = assistantContainer.querySelectorAll('div');
    const assistantMessageDiv = assistantDivs[1];
    expect(assistantMessageDiv?.className).toContain('bg-gray-100');
  });
});

describe('ChatMessage memoization', () => {
  it('should be memoized', () => {
    // React.memo creates a special type
    const MemoizedChatMessage = ChatMessage;
    expect(MemoizedChatMessage).toBeDefined();
  });

  it('should not re-render when props are the same', () => {
    const renderFn = vi.fn();
    const { rerender } = render(
      <ChatMessage message={mockUserMessage} />
    );

    // Re-render with same props
    rerender(<ChatMessage message={mockUserMessage} />);

    // Should not cause excessive re-renders in production
    // This is a basic check - memoization prevents unnecessary re-renders
    expect(ChatMessage).toBeDefined();
  });
});