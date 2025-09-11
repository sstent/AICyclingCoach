import { render, screen, fireEvent } from '@testing-library/react'
import RouteList from '../RouteList'

const mockRoutes = [
  {
    id: 1,
    name: 'Mountain Loop',
    distance: 45000,
    elevation_gain: 800,
    category: 'climbing'
  },
  {
    id: 2,
    name: 'Lakeside Ride',
    distance: 25000,
    elevation_gain: 200,
    category: 'flat'
  }
]

describe('RouteList', () => {
  it('displays routes and handles filtering', () => {
    render(<RouteList routes={mockRoutes} />)
    
    // Check initial render
    expect(screen.getByText('Mountain Loop')).toBeInTheDocument()
    expect(screen.getByText('Lakeside Ride')).toBeInTheDocument()
    
    // Test search
    fireEvent.change(screen.getByPlaceholderText('Search routes...'), {
      target: { value: 'mountain' }
    })
    expect(screen.getByText('Mountain Loop')).toBeInTheDocument()
    expect(screen.queryByText('Lakeside Ride')).not.toBeInTheDocument()
    
    // Test category filter
    fireEvent.click(screen.getByText('Flat'))
    expect(screen.queryByText('Mountain Loop')).not.toBeInTheDocument()
    expect(screen.getByText('Lakeside Ride')).toBeInTheDocument()
  })
})