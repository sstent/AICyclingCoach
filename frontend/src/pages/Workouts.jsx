import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import axios from 'axios';
import WorkoutAnalysis from '../components/analysis/WorkoutAnalysis';

const Workouts = () => {
  const { apiKey } = useAuth();
  const [workouts, setWorkouts] = useState([]);
  const [selectedWorkout, setSelectedWorkout] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  
  const isBuildTime = typeof window === 'undefined';
  
  useEffect(() => {
    if (isBuildTime) return;
    const fetchWorkouts = async () => {
      try {
        const response = await axios.get('/api/workouts', {
          headers: { 'X-API-Key': apiKey }
        });
        setWorkouts(response.data.workouts);
      } catch (err) {
        setError('Failed to load workouts');
      } finally {
        setLoading(false);
      }
    };
    
    fetchWorkouts();
  }, [apiKey]);

  if (isBuildTime) {
    return (
      <div className="p-6 max-w-7xl mx-auto">
        <h1 className="text-3xl font-bold mb-8">Workouts</h1>
        <div className="bg-white p-6 rounded-lg shadow-md">
          <p className="text-gray-600">Loading workout data...</p>
        </div>
      </div>
    );
  }

  if (loading) return <div className="p-6 text-center">Loading workouts...</div>;
  if (error) return <div className="p-6 text-red-600">{error}</div>;

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <h1 className="text-3xl font-bold mb-8">Workouts</h1>
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="space-y-4">
          {workouts.map(workout => (
            <div
              key={workout.id}
              onClick={() => setSelectedWorkout(workout)}
              className={`p-4 bg-white rounded-lg shadow-md cursor-pointer ${
                selectedWorkout?.id === workout.id ? 'ring-2 ring-blue-500' : ''
              }`}
            >
              <h3 className="font-medium">
                {new Date(workout.start_time).toLocaleDateString()} - {workout.activity_type}
              </h3>
              <p className="text-sm text-gray-600">
                Duration: {Math.round(workout.duration_seconds / 60)}min
              </p>
            </div>
          ))}
        </div>

        {selectedWorkout && (
          <div className="bg-white p-6 rounded-lg shadow-md">
            <WorkoutAnalysis workoutId={selectedWorkout.id} />
          </div>
        )}
      </div>
    </div>
  );
};

export default Workouts;