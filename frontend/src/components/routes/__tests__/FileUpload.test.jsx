import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import FileUpload from '../FileUpload'

describe('FileUpload', () => {
  const mockFile = new File(['<gpx><trk><name>Test Route</name></trk></gpx>'], 'test.gpx', {
    type: 'application/gpx+xml'
  })

  it('handles file upload and preview', async () => {
    const mockSuccess = jest.fn()
    render(<FileUpload onUploadSuccess={mockSuccess} />)
    
    // Simulate file drop
    const dropZone = screen.getByText('Drag and drop GPX file here')
    fireEvent.dragOver(dropZone)
    fireEvent.drop(dropZone, {
      dataTransfer: { files: [mockFile] }
    })

    // Check preview
    await waitFor(() => {
      expect(screen.getByText('Test Route')).toBeInTheDocument()
      expect(screen.getByText('Confirm Upload')).toBeInTheDocument()
    })
  })
})