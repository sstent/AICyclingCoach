import { useEffect, useState } from 'react';

export default function Home() {
  const [healthStatus, setHealthStatus] = useState<string>('checking...');

  useEffect(() => {
    const checkBackendHealth = async () => {
      try {
        // Use the API URL from environment variables
        const apiUrl = process.env.REACT_APP_API_URL || 'http://localhost:8000';
        const response = await fetch(`${apiUrl}/health`);
        const data = await response.json();
        setHealthStatus(data.status);
      } catch (error) {
        setHealthStatus('unavailable');
        console.error('Error checking backend health:', error);
      }
    };

    checkBackendHealth();
  }, []);

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-gray-50">
      <div className="max-w-2xl w-full p-8 bg-white rounded-lg shadow-md">
        <h1 className="text-3xl font-bold text-center text-gray-800 mb-6">
          Welcome to AI Cycling Coach
        </h1>
        <p className="text-lg text-gray-600 mb-8 text-center">
          Your AI-powered training companion for cyclists
        </p>
        
        <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
          <h2 className="text-lg font-semibold text-blue-800 mb-2">
            System Status
          </h2>
          <div className="flex items-center">
            <div className={`h-3 w-3 rounded-full mr-2 ${healthStatus === 'healthy' ? 'bg-green-500' : 'bg-red-500'}`}></div>
            <span className="text-gray-700">
              Backend service: {healthStatus}
            </span>
          </div>
        </div>
        
        <p className="mt-8 text-center text-gray-500">
          Development in progress - more features coming soon!
        </p>
      </div>
    </div>
  );
}