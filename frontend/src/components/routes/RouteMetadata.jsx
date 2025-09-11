import { FaRoute, FaMountain, FaTachometerAlt, FaStar } from 'react-icons/fa'

const RouteMetadata = ({ route }) => {
  return (
    <div className="bg-white p-6 rounded-lg shadow-md">
      <h3 className="text-xl font-semibold mb-4 flex items-center gap-2">
        <FaRoute className="text-blue-600" /> Route Details
      </h3>
      
      <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
        <div className="flex items-center gap-2 p-3 bg-gray-50 rounded-lg">
          <FaMountain className="text-gray-600" />
          <div>
            <p className="text-sm text-gray-500">Elevation Gain</p>
            <p className="font-medium">{route.elevation_gain}m</p>
          </div>
        </div>
        
        <div className="flex items-center gap-2 p-3 bg-gray-50 rounded-lg">
          <FaTachometerAlt className="text-gray-600" />
          <div>
            <p className="text-sm text-gray-500">Avg Grade</p>
            <p className="font-medium">{route.grade_avg}%</p>
          </div>
        </div>
        
        <div className="flex items-center gap-2 p-3 bg-gray-50 rounded-lg">
          <FaStar className="text-gray-600" />
          <div>
            <p className="text-sm text-gray-500">Difficulty</p>
            <div className="flex gap-1 text-yellow-400">
              {[...Array(5)].map((_, index) => (
                <FaStar
                  key={index}
                  className={`w-4 h-4 ${
                    index < Math.round(route.difficulty_rating / 2)
                      ? 'fill-current'
                      : 'text-gray-300'
                  }`}
                />
              ))}
            </div>
          </div>
        </div>
        
        <div className="col-span-2 md:col-span-3 grid grid-cols-2 gap-4 mt-4">
          <div className="p-3 bg-gray-50 rounded-lg">
            <p className="text-sm text-gray-500">Distance</p>
            <p className="font-medium">{(route.distance / 1000).toFixed(1)}km</p>
          </div>
          <div className="p-3 bg-gray-50 rounded-lg">
            <p className="text-sm text-gray-500">Category</p>
            <p className="font-medium capitalize">{route.category}</p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default RouteMetadata