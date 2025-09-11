import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import FileUpload from '../components/routes/FileUpload';
import RouteList from '../components/routes/RouteList';
import RouteFilter from '../components/routes/RouteFilter';
import LoadingSpinner from '../components/LoadingSpinner';

const RoutesPage = () => {
  const { apiKey } = useAuth();
  const [routes, setRoutes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filters, setFilters] = useState({
    searchQuery: '',
    minDistance: 0,
    maxDistance: 500,
    difficulty: 'all',
  });

  useEffect(() => {
    const fetchRoutes = async () => {
      try {
        const response = await fetch('/api/routes', {
          headers: { 'X-API-Key': apiKey }
        });
        
        if (!response.ok) throw new Error('Failed to fetch routes');
        
        const data = await response.json();
        setRoutes(data.routes);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };
    
    fetchRoutes();
  }, [apiKey]);

  const filteredRoutes = routes.filter(route => {
    const matchesSearch = route.name.toLowerCase().includes(filters.searchQuery.toLowerCase());
    const matchesDistance = route.distance >= filters.minDistance && 
                          route.distance <= filters.maxDistance;
    const matchesDifficulty = filters.difficulty === 'all' || 
                            route.difficulty === filters.difficulty;
    return matchesSearch && matchesDistance && matchesDifficulty;
  });

  const handleUploadSuccess = (newRoute) => {
    setRoutes(prev => [...prev, newRoute]);
  };

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <h1 className="text-3xl font-bold mb-8">Routes</h1>
      <div className="space-y-8">
        <div className="bg-white p-6 rounded-lg shadow-md">
          <RouteFilter filters={filters} onFilterChange={setFilters} />
          <FileUpload onUploadSuccess={handleUploadSuccess} />
        </div>
        
        {loading ? (
          <LoadingSpinner />
        ) : error ? (
          <div className="text-red-600 bg-red-50 p-4 rounded-md">{error}</div>
        ) : (
          <RouteList routes={filteredRoutes} />
        )}
      </div>
    </div>
  );
};

export default RoutesPage;