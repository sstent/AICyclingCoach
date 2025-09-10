import { render, screen } from '@testing-library/react';
import LoadingSpinner from '../LoadingSpinner';

describe('LoadingSpinner Component', () => {
  test('renders spinner with animation', () => {
    render(<LoadingSpinner />);
    
    // Check for the spinner container
    const spinnerContainer = screen.getByRole('status');
    expect(spinnerContainer).toBeInTheDocument();
    
    // Verify animation classes
    const spinnerElement = screen.getByTestId('loading-spinner');
    expect(spinnerElement).toHaveClass('animate-spin');
    expect(spinnerElement).toHaveClass('rounded-full');
    
    // Check accessibility attributes
    expect(spinnerElement).toHaveAttribute('aria-live', 'polite');
    expect(spinnerElement).toHaveAttribute('aria-busy', 'true');
  });

  test('matches snapshot', () => {
    const { asFragment } = render(<LoadingSpinner />);
    expect(asFragment()).toMatchSnapshot();
  });
});