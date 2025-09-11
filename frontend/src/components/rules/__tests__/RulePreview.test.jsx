import { render, screen } from '@testing-library/react';
import RulePreview from '../RulePreview';

describe('RulePreview', () => {
  const mockRules = {
    maxRides: 4,
    minRestDays: 1
  };

  test('renders preview with rules', () => {
    render(<RulePreview rules={mockRules} />);
    expect(screen.getByText('Rule Configuration Preview')).toBeInTheDocument();
    expect(screen.getByText('maxRides')).toBeInTheDocument();
  });

  test('shows placeholder when no rules', () => {
    render(<RulePreview rules={null} />);
    expect(screen.getByText('Parsed rules will appear here...')).toBeInTheDocument();
  });
});