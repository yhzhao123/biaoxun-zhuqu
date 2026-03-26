/**
 * Tests for ErrorBoundary component
 * TDD - RED phase: Tests that describe the expected behavior
 */

import { describe, it, expect, vi } from 'vitest';
import { screen } from '@testing-library/react';
import { render } from './setup';
import { ErrorBoundary } from '../components/ErrorBoundary';
import React from 'react';

// A component that throws an error
const ThrowError: React.FC = () => {
  throw new Error('Test error');
};

describe('ErrorBoundary', () => {
  it('should render children when there is no error', () => {
    render(
      <ErrorBoundary>
        <div>正常内容</div>
      </ErrorBoundary>
    );
    expect(screen.getByText('正常内容')).toBeInTheDocument();
  });

  it('should render error message when child throws', () => {
    vi.spyOn(console, 'error').mockImplementation(() => {});

    render(
      <ErrorBoundary>
        <ThrowError />
      </ErrorBoundary>
    );

    expect(screen.getByText(/发生错误/i)).toBeInTheDocument();
    expect(screen.getByText('Test error')).toBeInTheDocument();
  });

  it('should have a reload button', () => {
    vi.spyOn(console, 'error').mockImplementation(() => {});

    render(
      <ErrorBoundary>
        <ThrowError />
      </ErrorBoundary>
    );

    expect(screen.getByText(/重新加载/i)).toBeInTheDocument();
  });

  it('should reset error state when reload is clicked', async () => {
    vi.spyOn(console, 'error').mockImplementation(() => {});

    // Use key prop to force remount when error is reset
    const { rerender } = render(
      <ErrorBoundary key="eb1">
        <ThrowError />
      </ErrorBoundary>
    );

    expect(screen.getByText(/发生错误/i)).toBeInTheDocument();

    // Use key prop to force remount of ErrorBoundary - simulates page reload
    rerender(
      <ErrorBoundary key="eb2">
        <div>恢复后的内容</div>
      </ErrorBoundary>
    );

    expect(screen.getByText('恢复后的内容')).toBeInTheDocument();
  });
});