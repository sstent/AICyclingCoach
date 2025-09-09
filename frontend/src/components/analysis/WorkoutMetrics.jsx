const WorkoutMetrics = ({ workout }) => {
  const formatDuration = (seconds) => {
    const mins = Math.floor(seconds / 60);
    return `${mins} minutes`;
  };

  return (
    <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6">
      <div className="bg-gray-50 p-4 rounded-md">
        <p className="text-sm text-gray-600">Duration</p>
        <p className="text-lg font-medium">
          {formatDuration(workout.duration_seconds)}
        </p>
      </div>
      <div className="bg-gray-50 p-4 rounded-md">
        <p className="text-sm text-gray-600">Distance</p>
        <p className="text-lg font-medium">
          {(workout.distance_m / 1000).toFixed(1)} km
        </p>
      </div>
      <div className="bg-gray-50 p-4 rounded-md">
        <p className="text-sm text-gray-600">Avg Power</p>
        <p className="text-lg font-medium">
          {workout.avg_power?.toFixed(0) || '-'} W
        </p>
      </div>
      <div className="bg-gray-50 p-4 rounded-md">
        <p className="text-sm text-gray-600">Avg HR</p>
        <p className="text-lg font-medium">
          {workout.avg_hr?.toFixed(0) || '-'} bpm
        </p>
      </div>
      <div className="bg-gray-50 p-4 rounded-md">
        <p className="text-sm text-gray-600">Elevation</p>
        <p className="text-lg font-medium">
          {workout.elevation_gain_m?.toFixed(0) || '-'} m
        </p>
      </div>
    </div>
  );
};

export default WorkoutMetrics;