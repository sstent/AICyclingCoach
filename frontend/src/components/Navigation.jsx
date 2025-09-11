import Link from 'next/link';

const Navigation = () => {
  return (
    <nav className="bg-white shadow-sm">
      <div className="max-w-7xl mx-auto px-4 py-3">
        <div className="flex space-x-4">
          <Link
            href="/"
            className="text-gray-700 hover:text-blue-600 px-3 py-2 rounded-md"
          >
            Home
          </Link>
          <Link
            href="/dashboard"
            className="text-gray-700 hover:text-blue-600 px-3 py-2 rounded-md"
          >
            Dashboard
          </Link>
          <Link
            href="/workouts"
            className="text-gray-700 hover:text-blue-600 px-3 py-2 rounded-md"
          >
            Workouts
          </Link>
          <Link
            href="/plans"
            className="text-gray-700 hover:text-blue-600 px-3 py-2 rounded-md"
          >
            Plans
          </Link>
          <Link
            href="/rules"
            className="text-gray-700 hover:text-blue-600 px-3 py-2 rounded-md"
          >
            Rules
          </Link>
          <Link
            href="/routes"
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