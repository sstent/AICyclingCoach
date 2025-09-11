import PropTypes from 'prop-types';

const RouteFilter = ({ filters, onFilterChange }) => {
  const handleChange = (field, value) => {
    onFilterChange({
      ...filters,
      [field]: value
    });
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6 p-4 bg-gray-50 rounded-lg">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Search
        </label>
        <input
          type="text"
          value={filters.searchQuery}
          onChange={(e) => handleChange('searchQuery', e.target.value)}
          placeholder="Search routes..."
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Min Distance (km)
        </label>
        <input
          type="number"
          value={filters.minDistance}
          onChange={(e) => handleChange('minDistance', Number(e.target.value))}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Max Distance (km)
        </label>
        <input
          type="number"
          value={filters.maxDistance}
          onChange={(e) => handleChange('maxDistance', Number(e.target.value))}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Difficulty
        </label>
        <select
          value={filters.difficulty}
          onChange={(e) => handleChange('difficulty', e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="all">All Difficulties</option>
          <option value="easy">Easy</option>
          <option value="moderate">Moderate</option>
          <option value="hard">Hard</option>
          <option value="extreme">Extreme</option>
        </select>
      </div>
    </div>
  );
};

RouteFilter.propTypes = {
  filters: PropTypes.shape({
    searchQuery: PropTypes.string,
    minDistance: PropTypes.number,
    maxDistance: PropTypes.number,
    difficulty: PropTypes.string
  }).isRequired,
  onFilterChange: PropTypes.func.isRequired
};

export default RouteFilter;