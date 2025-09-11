import { render, screen, fireEvent } from '@testing-library/react';
import RuleEditor from '../RuleEditor';

describe('RuleEditor', () => {
  const mockOnChange = jest.fn();
  const mockOnParse = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('renders editor with basic functionality', () => {
    render(<RuleEditor value="" onChange={mockOnChange} onParse={mockOnParse} />);
    
    expect(screen.getByText('Natural Language Editor')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Enter your training rules in natural language...')).toBeInTheDocument();
    expect(screen.getByText('Parse Rules')).toBeInTheDocument();
  });

  test('shows character count and validation status', () => {
    const { rerender } = render(
      <RuleEditor value="Valid rule text" onChange={mockOnChange} onParse={mockOnParse} />
    );
    
    expect(screen.getByText(/0\/5000 characters/)).toBeInTheDocument();
    expect(screen.getByText('Valid')).toBeInTheDocument();

    rerender(<RuleEditor value="Short" onChange={mockOnChange} onParse={mockOnParse} />);
    expect(screen.getByText('Invalid input')).toBeInTheDocument();
  });

  test('shows template suggestions when clicked', async () => {
    render(<RuleEditor value="" onChange={mockOnChange} onParse={mockOnParse} />);
    
    fireEvent.click(screen.getByText('Templates'));
    expect(screen.getByText('Maximum 4 rides per week with at least one rest day between hard workouts')).toBeInTheDocument();
  });

  test('triggers parse on button click', () => {
    render(<RuleEditor value="Valid rule text" onChange={mockOnChange} onParse={mockOnParse} />);
    
    fireEvent.click(screen.getByText('Parse Rules'));
    expect(mockOnParse).toHaveBeenCalled();
  });
});