/**
 * Tests for TenderMetadataBadge component
 * TDD - RED phase: Tests that describe the expected behavior
 */

import { describe, it, expect } from 'vitest';
import { screen, render } from '@testing-library/react';
import { TenderMetadataBadge } from '../components/TenderMetadataBadge';
import React from 'react';

describe('TenderMetadataBadge', () => {
  it('should render nothing when no props provided', () => {
    const { container } = render(<TenderMetadataBadge />);
    expect(container.firstChild).toBeNull();
  });

  it('should render extraction method badge', () => {
    render(<TenderMetadataBadge extraction_method="llm" />);

    expect(screen.getByText('LLM智能提取')).toBeInTheDocument();
  });

  it('should render confidence badge', () => {
    render(<TenderMetadataBadge extraction_confidence={0.85} />);

    expect(screen.getByText('置信度: 85%')).toBeInTheDocument();
  });

  it('should render high confidence in green', () => {
    render(<TenderMetadataBadge extraction_confidence={0.95} />);

    expect(screen.getByText('置信度: 95%')).toBeInTheDocument();
    expect(screen.getByText('置信度: 95%').className).toContain('bg-green-100');
  });

  it('should render medium confidence in yellow', () => {
    render(<TenderMetadataBadge extraction_confidence={0.75} />);

    expect(screen.getByText('置信度: 75%')).toBeInTheDocument();
    expect(screen.getByText('置信度: 75%').className).toContain('bg-yellow-100');
  });

  it('should render low confidence in red', () => {
    render(<TenderMetadataBadge extraction_confidence={0.5} />);

    expect(screen.getByText('置信度: 50%')).toBeInTheDocument();
    expect(screen.getByText('置信度: 50%').className).toContain('bg-red-100');
  });

  it('should render both method and confidence', () => {
    render(<TenderMetadataBadge
      extraction_method="rule"
      extraction_confidence={0.9}
    />);

    expect(screen.getByText('规则提取')).toBeInTheDocument();
    expect(screen.getByText('置信度: 90%')).toBeInTheDocument();
  });
});