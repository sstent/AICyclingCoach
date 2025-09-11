import { render, screen, fireEvent } from '@testing-library/react';
import RulesList from '../RulesList';

const mockRuleSets = [{
  id: 1,
  name: 'Winter Rules',
  version: 2,
  active: true,
  created_at: '2024-01-15T11:00:00Z',
  history: [
    { version: 1, created_at: '2024-01-01T09:00:00Z' },
    { version: 2, created_at: '2024-01-15T11:00:00Z' }
  ]
}];

describe('RulesList', () => {
  test('renders rule sets table', () => {
    render(<RulesList ruleSets={mockRuleSets} />);
    
    expect(screen.getByText('Winter Rules')).toBeInTheDocument();
    expect(screen.getByText('v2')).toBeInTheDocument();
    expect(screen.getByText('Active')).toBeInTheDocument();
  });

  test('shows version history modal', () => {
    render(<RulesList ruleSets={mockRuleSets} />);
    
    fireEvent.click(screen.getByText('View/Edit'));
    expect(screen.getByText('Winter Rules Version History')).toBeInTheDocument();
    expect(screen.getAllByText(/v\d/)).toHaveLength(2);
  });
});