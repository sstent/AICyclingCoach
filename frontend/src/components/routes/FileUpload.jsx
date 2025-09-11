import { useState, useCallback } from 'react'
import { useAuth } from '../../context/AuthContext'
import LoadingSpinner from '../LoadingSpinner'
import dynamic from 'next/dynamic'
import { gpx } from '@tmcw/togeojson'

const RouteVisualization = dynamic(() => import('./RouteVisualization'), {
  ssr: false,
  loading: () => <div className="h-64 bg-gray-100 rounded-md flex items-center justify-center">Loading map...</div>
})

const FileUpload = ({ onUploadSuccess }) => {
  const { apiKey } = useAuth()
  const [isDragging, setIsDragging] = useState(false)
  const [previewData, setPreviewData] = useState(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState(null)

  const handleFile = async (file) => {
    if (file.type !== 'application/gpx+xml') {
      setError('Please upload a valid GPX file')
      return
    }

    try {
      // Preview parsing
      const reader = new FileReader()
      reader.onload = (e) => {
        try {
          const parser = new DOMParser()
          const gpxDoc = parser.parseFromString(e.target.result, 'text/xml')
          const geoJson = gpx(gpxDoc)
          
          // Extract basic info from GeoJSON
          const name = geoJson.features[0]?.properties?.name || 'Unnamed Route'
          
          // Calculate distance and elevation (simplified)
          let totalDistance = 0
          let elevationGain = 0
          let elevationLoss = 0
          let maxElevation = 0
          
          // Simple calculation - in a real app you'd want more accurate distance calculation
          const coordinates = geoJson.features[0]?.geometry?.coordinates || []
          for (let i = 1; i < coordinates.length; i++) {
            const [prevLon, prevLat, prevEle] = coordinates[i-1]
            const [currLon, currLat, currEle] = coordinates[i]
            // Simple distance calculation (you might want to use a more accurate method)
            const distance = Math.sqrt(Math.pow(currLon - prevLon, 2) + Math.pow(currLat - prevLat, 2)) * 111000 // rough meters
            totalDistance += distance
            
            if (prevEle && currEle) {
              const eleDiff = currEle - prevEle
              if (eleDiff > 0) {
                elevationGain += eleDiff
              } else {
                elevationLoss += Math.abs(eleDiff)
              }
              maxElevation = Math.max(maxElevation, currEle)
            }
          }
          
          const avgGrade = totalDistance > 0 ? ((elevationGain / totalDistance) * 100).toFixed(1) : '0.0'

          setPreviewData({
            name,
            distance: (totalDistance / 1000).toFixed(1) + 'km',
            elevationGain: elevationGain.toFixed(0) + 'm',
            elevationLoss: elevationLoss.toFixed(0) + 'm',
            maxElevation: maxElevation.toFixed(0) + 'm',
            avgGrade: avgGrade + '%',
            category: 'mixed',
            gpxContent: e.target.result
          })
        } catch (parseError) {
          setError('Error parsing GPX file: ' + parseError.message)
        }
      }
      reader.readAsText(file)
    } catch (err) {
      setError('Error parsing GPX file')
    }
  }

  const handleUpload = async () => {
    if (!previewData) return
    
    setIsLoading(true)
    try {
      const formData = new FormData()
      const blob = new Blob([previewData.gpxContent], { type: 'application/gpx+xml' })
      formData.append('file', blob, previewData.name + '.gpx')

      const response = await fetch('/api/routes/upload', {
        method: 'POST',
        headers: {
          'X-API-Key': apiKey
        },
        body: formData
      })

      if (!response.ok) throw new Error('Upload failed')
      
      const result = await response.json()
      onUploadSuccess(result)
      setPreviewData(null)
      setError(null)
    } catch (err) {
      setError(err.message || 'Upload failed')
    } finally {
      setIsLoading(false)
    }
  }

  const onDragOver = useCallback((e) => {
    e.preventDefault()
    setIsDragging(true)
  }, [])

  const onDragLeave = useCallback((e) => {
    e.preventDefault()
    setIsDragging(false)
  }, [])

  const onDrop = useCallback((e) => {
    e.preventDefault()
    setIsDragging(false)
    const file = e.dataTransfer.files[0]
    if (file) handleFile(file)
  }, [])

  return (
    <div className="mb-8">
      <div 
        className={`border-2 border-dashed rounded-lg p-6 text-center ${
          isDragging ? 'border-blue-500 bg-blue-50' : 'border-gray-300'
        }`}
        onDragOver={onDragOver}
        onDragLeave={onDragLeave}
        onDrop={onDrop}
      >
        <input
          type="file"
          id="gpx-upload"
          className="hidden"
          accept=".gpx,application/gpx+xml"
          onChange={(e) => e.target.files[0] && handleFile(e.target.files[0])}
        />
        <label htmlFor="gpx-upload" className="cursor-pointer">
          <p className="text-gray-600">
            Drag and drop GPX file here or{' '}
            <span className="text-blue-600 font-medium">browse files</span>
          </p>
        </label>
      </div>

      {previewData && (
        <div className="mt-6 bg-white p-6 rounded-lg shadow-md">
          <h3 className="text-lg font-medium mb-4">Route Preview</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Route Name</label>
                <input
                  type="text"
                  value={previewData.name}
                  onChange={(e) => setPreviewData(prev => ({...prev, name: e.target.value}))}
                  className="w-full p-2 border rounded-md"
                />
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Category</label>
                  <select
                    value={previewData.category}
                    onChange={(e) => setPreviewData(prev => ({...prev, category: e.target.value}))}
                    className="w-full p-2 border rounded-md"
                  >
                    <option value="climbing">Climbing</option>
                    <option value="flat">Flat</option>
                    <option value="mixed">Mixed</option>
                    <option value="intervals">Intervals</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Distance</label>
                  <p className="p-2 bg-gray-50 rounded-md">{previewData.distance}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Elevation Gain</label>
                  <p className="p-2 bg-gray-50 rounded-md">{previewData.elevationGain}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Avg Grade</label>
                  <p className="p-2 bg-gray-50 rounded-md">{previewData.avgGrade}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Max Elevation</label>
                  <p className="p-2 bg-gray-50 rounded-md">{previewData.maxElevation}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Elevation Loss</label>
                  <p className="p-2 bg-gray-50 rounded-md">{previewData.elevationLoss}</p>
                </div>
              </div>
              <button
                onClick={handleUpload}
                disabled={isLoading}
                className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 disabled:bg-gray-400"
              >
                {isLoading ? 'Uploading...' : 'Confirm Upload'}
              </button>
            </div>
            <div className="h-64">
              <RouteVisualization gpxData={previewData.gpxContent} />
            </div>
          </div>
        </div>
      )}

      {error && (
        <div className="mt-4 text-red-600 bg-red-50 p-3 rounded-md">
          {error}
        </div>
      )}
    </div>
  )
}

export default FileUpload