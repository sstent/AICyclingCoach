import { Link } from 'react-router-dom';

const Navigation = () => {
  return (
    <nav className="bg-white shadow-sm">
      <div className="max-w-7xl mx-auto px-4 py-3">
        <div className="flex space-x-4">
          <Link 
            to="/" 
            className="text-gray-700 hover:text-blue-600 px-3 py-2 rounded-md"
          >
            Dashboard
          </Link>
          <Link
            to="/workouts"
            className="text-gray-700 hover:text-blue-600 px-3 py-2 rounded-md"
          >
            Workouts
          </Link>
          <Link
            to="/plans"
            className="text-gray-700 hover:text-blue-600 px-3 py-2 rounded-md"
          >
            Plans
          </Link>
          <Link
            to="/rules"
            className="text-gray-700 hover:text-blue-600 px-3 py-2 rounded-md"
          >
            Rules
          </Link>
          <Link
            to="/routes"
            className="text-gray-700 hover:text-blue-600 px-3 py-2 rounded-md"
          >
            Routes
          </Link>
        </div>
      </div>
    </nav>
  );
};

export default Navigation;