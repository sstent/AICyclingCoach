import { render, screen, fireEvent } from '@testing-library/react'
import RouteMetadata from '../RouteMetadata'
import { AuthProvider } from '../../../context/AuthContext'

const mockRoute = {
  id: 1,
  name: 'Test Route',
  description: 'Initial description',
  category: 'mixed'
}

const Wrapper = ({ children }) => (
  <AuthProvider>
    {children}
  </AuthProvider>
)

describe('RouteMetadata', () => {
  it('handles editing and updating route details', async () => {
    const mockUpdate = jest.fn()
    render(<RouteMetadata route={mockRoute} onUpdate={mockUpdate} />, { wrapper: Wrapper })

    // Test initial view mode
    expect(screen.getByText('Test Route')).toBeInTheDocument()
    expect(screen.getByText('Initial description')).toBeInTheDocument()

    // Enter edit mode
    fireEvent.click(screen.getByText('Edit'))
    
    // Verify form fields
    const nameInput = screen.getByDisplayValue('Test Route')
    const descInput = screen.getByDisplayValue('Initial description')
    const categorySelect = screen.getByDisplayValue('Mixed')

    // Make changes
    fireEvent.change(nameInput, { target: { value: 'Updated Route' } })
    fireEvent.change(descInput, { target: { value: 'New description' } })
    fireEvent.change(categorySelect, { target: { value: 'climbing' } })

    // Save changes
    fireEvent.click(screen.getByText('Save'))

    // Verify update was called
    await waitFor(() => {
      expect(mockUpdate).toHaveBeenCalledWith(expect.objectContaining({
        name: 'Updated Route',
        description: 'New description',
        category: 'climbing'
      }))
    })
  })
})