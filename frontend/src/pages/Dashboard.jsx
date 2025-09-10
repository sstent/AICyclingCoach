import { useEffect, useState } from 'react';
import GarminSync from '../components/garmin/GarminSync';
import WorkoutChart from '../components/analysis/WorkoutCharts';
import PlanTimeline from '../components/plans/PlanTimeline';
import { useAuth } from '../context/AuthContext';
import LoadingSpinner from '../components/LoadingSpinner';

const Dashboard = () => {
  const { apiKey, loading: apiLoading } = useAuth();
  const isBuildTime = typeof window === 'undefined';
  const [recentWorkouts, setRecentWorkouts] = useState([]);
  const [currentPlan, setCurrentPlan] = useState(null);
  const [stats, setStats] = useState({ totalWorkouts: 0, totalDistance: 0 });
  const [healthStatus, setHealthStatus] = useState(null);
  const [localLoading, setLocalLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        const [workoutsRes, planRes, statsRes, healthRes] = await Promise.all([
          fetch(`${process.env.REACT_APP_API_URL}/api/workouts?limit=3`, {
            headers: { 'X-API-Key': apiKey }
          }),
          fetch(`${process.env.REACT_APP_API_URL}/api/plans/active`, {
            headers: { 'X-API-Key': apiKey }
          }),
          fetch(`${process.env.REACT_APP_API_URL}/api/stats`, {
            headers: { 'X-API-Key': apiKey }
          }),
          fetch(`${process.env.REACT_APP_API_URL}/api/health`, {
            headers: { 'X-API-Key': apiKey }
          })
        ]);

        const errors = [];
        if (!workoutsRes.ok) errors.push('Failed to fetch workouts');
        if (!planRes.ok) errors.push('Failed to fetch plan');
        if (!statsRes.ok) errors.push('Failed to fetch stats');
        if (!healthRes.ok) errors.push('Failed to fetch health status');
        
        if (errors.length > 0) throw new Error(errors.join(', '));

        const [workoutsData, planData, statsData, healthData] = await Promise.all([
          workoutsRes.json(),
          planRes.json(),
          statsRes.json(),
          healthRes.json()
        ]);

        setRecentWorkouts(workoutsData.workouts || []);
        setCurrentPlan(planData);
        setStats(statsData.workouts || { totalWorkouts: 0, totalDistance: 0 });
        setHealthStatus(healthData);
      } catch (err) {
        setError(err.message);
      } finally {
        setLocalLoading(false);
      }
    };

    fetchDashboardData();
  }, [apiKey]);

  if (isBuildTime) {
    return (
      <div className="p-6 max-w-7xl mx-auto">
        <h1 className="text-3xl font-bold">Training Dashboard</h1>
        <div className="bg-white p-6 rounded-lg shadow-md">
          <p className="text-gray-600">Loading dashboard data...</p>
        </div>
      </div>
    );
  }

  if (localLoading || apiLoading) return <LoadingSpinner />;
  if (error) return <div className="p-6 text-red-500">{error}</div>;

  // Calculate total distance in km
  const totalDistanceKm = (stats.totalDistance / 1000).toFixed(0);

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-8">
      <h1 className="text-3xl font-bold">Training Dashboard</h1>
      
      <div className="mb-8">
        <GarminSync apiKey={apiKey} />
      </div>

      {/* Stats Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-white p-4 rounded-lg shadow-md">
          <h3 className="text-sm font-medium text-gray-600">Total Workouts</h3>
          <p className="text-2xl font-bold">{stats.totalWorkouts}</p>
        </div>
        <div className="bg-white p-4 rounded-lg shadow-md">
          <h3 className="text-sm font-medium text-gray-600">Total Distance</h3>
          <p className="text-2xl font-bold">{totalDistanceKm} km</p>
        </div>
        <div className="bg-white p-4 rounded-lg shadow-md">
          <h3 className="text-sm font-medium text-gray-600">Current Plan</h3>
          <p className="text-2xl font-bold">
            {currentPlan ? `v${currentPlan.version}` : 'None'}
          </p>
        </div>
        <div className="bg-white p-4 rounded-lg shadow-md">
          <h3 className="text-sm font-medium text-gray-600">System Status</h3>
          <div className="flex items-center">
            <div className={`w-3 h-3 rounded-full mr-2 ${
              healthStatus?.status === 'healthy' ? 'bg-green-500' : 'bg-red-500'
            }`}></div>
            <span className="text-xl font-bold capitalize">
              {healthStatus?.status || 'unknown'}
            </span>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 sm:gap-4 lg:gap-6">
        <div className="sm:col-span-2 space-y-3 sm:space-y-4 lg:space-y-6">
          <div className="bg-white p-4 sm:p-6 rounded-lg shadow-md">
            <h2 className="text-lg sm:text-xl font-semibold mb-3 sm:mb-4">Performance Metrics</h2>
            <WorkoutChart workouts={recentWorkouts} />
          </div>

          <div className="bg-white p-4 sm:p-6 rounded-lg shadow-md">
            <h2 className="text-lg sm:text-xl font-semibold mb-3 sm:mb-4">Recent Activities</h2>
            {recentWorkouts.length > 0 ? (
              <div className="space-y-4">
                {recentWorkouts.map(workout => (
                  <div key={workout.id} className="p-3 sm:p-4 border rounded-lg hover:bg-gray-50">
                    <div className="flex justify-between items-center gap-2">
                      <div>
                        <h3 className="text-sm sm:text-base font-medium">{new Date(workout.start_time).toLocaleDateString()}</h3>
                        <p className="text-xs sm:text-sm text-gray-600">{workout.activity_type}</p>
                      </div>
                      <div className="text-right">
                        <p className="text-sm sm:text-base font-medium">{(workout.distance_m / 1000).toFixed(1)} km</p>
                        <p className="text-xs sm:text-sm text-gray-600">{Math.round(workout.duration_seconds / 60)} mins</p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-gray-500 text-center py-4">No recent activities found</div>
            )}
          </div>
        </div>

        <div className="space-y-6">
          <div className="bg-white p-4 sm:p-6 rounded-lg shadow-md">
            <h2 className="text-lg sm:text-xl font-semibold mb-3 sm:mb-4">Current Plan</h2>
            {currentPlan ? (
              <PlanTimeline plan={currentPlan} />
            ) : (
              <div className="text-gray-500 text-center py-4">No active training plan</div>
            )}
          </div>

          <div className="bg-white p-4 sm:p-6 rounded-lg shadow-md">
            <h2 className="text-lg sm:text-xl font-semibold mb-3 sm:mb-4">Upcoming Workouts</h2>
            {currentPlan?.jsonb_plan.weeks[0]?.workouts.map((workout, index) => (
              <div key={index} className="p-2 sm:p-3 border-b last:border-b-0">
                <div className="flex justify-between items-center">
                  <span className="capitalize">{workout.day}</span>
                  <span className="text-xs sm:text-sm bg-blue-100 text-blue-800 px-2 py-1 rounded">
                    {workout.type.replace('_', ' ')}
                  </span>
                </div>
                <p className="text-xs sm:text-sm text-gray-600 mt-1">{workout.description}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;