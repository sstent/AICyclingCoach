import { useRef, useEffect, useState } from 'react'
import { MapContainer, TileLayer, Polyline, Marker, Popup } from 'react-leaflet'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import { gpx } from '@tmcw/togeojson'

// Fix leaflet marker icons
delete L.Icon.Default.prototype._getIconUrl
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png'
})

const RouteVisualization = ({ gpxData }) => {
  const mapRef = useRef()
  const elevationChartRef = useRef(null)
  const [routePoints, setRoutePoints] = useState([])

  useEffect(() => {
    if (!gpxData) return

    try {
      const parser = new DOMParser()
      const gpxDoc = parser.parseFromString(gpxData, 'text/xml')
      const geoJson = gpx(gpxDoc)
      
      if (!geoJson.features[0]) return

      const coordinates = geoJson.features[0].geometry.coordinates
      const points = coordinates.map(coord => [coord[1], coord[0]]) // [lat, lon]
      const bounds = L.latLngBounds(points)
      
      setRoutePoints(points)
      
      if (mapRef.current) {
        mapRef.current.flyToBounds(bounds, { padding: [50, 50] })
      }

      // Plot elevation profile
      if (elevationChartRef.current) {
        const elevations = coordinates.map(coord => coord[2] || 0)
        const distances = []
        let distance = 0
        
        for (let i = 1; i < coordinates.length; i++) {
          const prevPoint = L.latLng(coordinates[i-1][1], coordinates[i-1][0])
          const currPoint = L.latLng(coordinates[i][1], coordinates[i][0])
          distance += prevPoint.distanceTo(currPoint)
          distances.push(distance)
        }

        // TODO: Integrate charting library
      }
    } catch (error) {
      console.error('Error parsing GPX data:', error)
    }
  }, [gpxData])

  return (
    <div className="h-full w-full relative">
      <MapContainer
        center={[51.505, -0.09]}
        zoom={13}
        scrollWheelZoom={false}
        className="h-full rounded-md"
        ref={mapRef}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <Polyline
          positions={routePoints}
          color="#3b82f6"
          weight={4}
        />
        <Marker position={[51.505, -0.09]}>
          <Popup>Start/End Point</Popup>
        </Marker>
      </MapContainer>
      
      <div 
        ref={elevationChartRef}
        className="absolute bottom-4 left-4 right-4 h-32 bg-white/90 backdrop-blur-sm rounded-md p-4 shadow-md"
      >
        {/* Elevation chart will be rendered here */}
      </div>
    </div>
  )
}

export default RouteVisualization