import { render, screen } from '@testing-library/react'
import RouteVisualization from '../RouteVisualization'

const mockGPX = `
  <gpx>
    <trk>
      <trkseg>
        <trkpt lat="37.7749" lon="-122.4194"><ele>50</ele></trkpt>
        <trkpt lat="37.7859" lon="-122.4294"><ele>60</ele></trkpt>
      </trkseg>
    </trk>
  </gpx>
`

describe('RouteVisualization', () => {
  it('renders map with GPX track', () => {
    render(<RouteVisualization gpxData={mockGPX} />)
    
    // Check map container is rendered
    expect(screen.getByRole('presentation')).toBeInTheDocument()
    
    // Check if polyline is created with coordinates
    const path = document.querySelector('.leaflet-overlay-pane path')
    expect(path).toHaveAttribute('d', expect.stringContaining('M37.7749 -122.4194L37.7859 -122.4294'))
  })
})