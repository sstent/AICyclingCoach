import { useAuth } from '../context/AuthContext';

const RoutesPage = () => {
  const { apiKey } = useAuth();

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <h1 className="text-3xl font-bold mb-8">Routes</h1>
      <div className="bg-white p-6 rounded-lg shadow-md">
        <p className="text-gray-600">Route management will be displayed here</p>
      </div>
    </div>
  );
};

export default RoutesPage;