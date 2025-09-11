import { useState } from 'react'
import { useAuth } from '../../context/AuthContext'
import LoadingSpinner from '../LoadingSpinner'
import { format } from 'date-fns'
import { FaStar } from 'react-icons/fa'

const RouteList = ({ routes, onRouteSelect }) => {
  const { apiKey } = useAuth()
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedCategory, setSelectedCategory] = useState('all')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState(null)

  const categories = ['all', 'climbing', 'flat', 'mixed', 'intervals']

  const filteredRoutes = routes.filter(route => {
    const matchesSearch = route.name.toLowerCase().includes(searchQuery.toLowerCase())
    const matchesCategory = selectedCategory === 'all' || route.category === selectedCategory
    return matchesSearch && matchesCategory
  })

  return (
    <div className="bg-white p-6 rounded-lg shadow-md">
      <div className="mb-6 space-y-4">
        <input
          type="text"
          placeholder="Search routes..."
          className="w-full p-2 border rounded-md"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
        />
        
        <div className="flex flex-wrap gap-2">
          {categories.map(category => (
            <button
              key={category}
              onClick={() => setSelectedCategory(category)}
              className={`px-4 py-2 rounded-full text-sm font-medium ${
                selectedCategory === category
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              {category.charAt(0).toUpperCase() + category.slice(1)}
            </button>
          ))}
        </div>
      </div>

      {isLoading ? (
        <LoadingSpinner />
      ) : error ? (
        <div className="text-red-600">{error}</div>
      ) : (
        <div className="space-y-4">
          {filteredRoutes.map(route => (
            <div
              key={route.id}
              className="p-4 border rounded-md hover:bg-gray-50 cursor-pointer"
              onClick={() => onRouteSelect(route)}
            >
              <div className="flex justify-between items-start">
                <h3 className="font-medium text-lg">{route.name}</h3>
                <span className="text-sm text-gray-500">
                  {format(new Date(route.created_at), 'MMM d, yyyy')}
                </span>
              </div>
              <div className="grid grid-cols-4 gap-4 mt-2 text-gray-600">
                <div>
                  <span className="font-medium">Distance: </span>
                  {(route.distance / 1000).toFixed(1)}km
                </div>
                <div>
                  <span className="font-medium">Elevation: </span>
                  {route.elevation_gain}m
                </div>
                <div>
                  <span className="font-medium">Category: </span>
                  {route.category}
                </div>
                <div>
                  <span className="font-medium">Grade: </span>
                  {route.grade_avg}%
                </div>
                <div className="flex items-center gap-1">
                  <span className="font-medium">Difficulty: </span>
                  {[...Array(5)].map((_, index) => (
                    <FaStar
                      key={index}
                      className={`w-4 h-4 ${
                        index < Math.round(route.difficulty_rating / 2)
                          ? 'text-yellow-400'
                          : 'text-gray-300'
                      }`}
                    />
                  ))}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default RouteList