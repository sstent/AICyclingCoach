import { render, screen, fireEvent } from '@testing-library/react';
import GoalSelector from '../GoalSelector';

describe('GoalSelector', () => {
  const mockOnSelect = jest.fn();
  const mockOnNext = jest.fn();

  beforeEach(() => {
    render(<GoalSelector goals={[]} onSelect={mockOnSelect} onNext={mockOnNext} />);
  });

  it('allows selection of predefined goals', () => {
    const enduranceButton = screen.getByText('Build Endurance');
    fireEvent.click(enduranceButton);
    expect(mockOnSelect).toHaveBeenCalledWith(['endurance']);
  });

  it('handles custom goal input', () => {
    const addButton = screen.getByText('Add Custom Goal');
    fireEvent.click(addButton);
    
    const input = screen.getByPlaceholderText('Enter custom goal');
    fireEvent.change(input, { target: { value: 'Custom Goal' } });
    
    const addCustomButton = screen.getByText('Add');
    fireEvent.click(addCustomButton);
    
    expect(mockOnSelect).toHaveBeenCalledWith(['Custom Goal']);
  });

  it('disables next button with no goals selected', () => {
    expect(screen.getByText('Next')).toBeDisabled();
  });
});