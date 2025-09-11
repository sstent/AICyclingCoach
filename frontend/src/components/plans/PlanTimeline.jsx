import { useState } from 'react';
import PropTypes from 'prop-types';
import { useAuth } from '../../context/AuthContext';
import axios from 'axios';
import WorkoutCard from './WorkoutCard';
import EditWorkoutModal from './EditWorkoutModal';

const PlanTimeline = ({ plan, mode = 'view' }) => {
  const { apiKey } = useAuth();
  const [currentPlan, setCurrentPlan] = useState(plan?.jsonb_plan);
  const [showEditModal, setShowEditModal] = useState(false);
  const [selectedWorkout, setSelectedWorkout] = useState(null);
  const [selectedWeek, setSelectedWeek] = useState(0);

  const handleWorkoutUpdate = async (updatedWorkout) => {
    try {
      const newPlan = { ...currentPlan };
      newPlan.weeks[selectedWeek].workouts = newPlan.weeks[selectedWeek].workouts.map(w => 
        w.day === updatedWorkout.day ? updatedWorkout : w
      );
      
      if (mode === 'edit') {
        await axios.put(`/api/plans/${plan.id}`, newPlan, {
          headers: { 'X-API-Key': apiKey }
        });
      }
      
      setCurrentPlan(newPlan);
      setShowEditModal(false);
    } catch (error) {
      console.error('Error updating workout:', error);
    }
  };

  return (
    <div className="bg-white p-6 rounded-lg shadow-md">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-xl font-semibold">
          {currentPlan?.plan_overview?.focus} Training Plan
        </h3>
        <div className="text-gray-600">
          {currentPlan?.plan_overview?.duration_weeks} weeks • 
          {currentPlan?.plan_overview?.weekly_hours} hrs/week
        </div>
      </div>

      <div className="space-y-8">
        {currentPlan?.weeks?.map((week, weekIndex) => (
          <div key={weekIndex} className="border-l-2 border-blue-100 pl-4">
            <div className="flex items-center justify-between mb-4">
              <h4 className="font-medium">
                Week {weekIndex + 1}: {week.focus}
              </h4>
              <div className="flex items-center space-x-2">
                <div className="h-2 w-24 bg-gray-200 rounded-full">
                  <div 
                    className="h-full bg-blue-600 rounded-full"
                    style={{ width: `${(weekIndex + 1) / currentPlan.plan_overview.duration_weeks * 100}%` }}
                  />
                </div>
                <span className="text-sm text-gray-600">
                  {week.workouts.length} workouts
                </span>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {week.workouts.map((workout, workoutIndex) => (
                <WorkoutCard
                  key={`${weekIndex}-${workoutIndex}`}
                  workout={workout}
                  onEdit={() => {
                    setSelectedWeek(weekIndex);
                    setSelectedWorkout(workout);
                    setShowEditModal(true);
                  }}
                  editable={mode === 'edit'}
                />
              ))}
            </div>
          </div>
        ))}
      </div>

      {showEditModal && (
        <EditWorkoutModal
          workout={selectedWorkout}
          onClose={() => setShowEditModal(false)}
          onSave={handleWorkoutUpdate}
        />
      )}
    </div>
  );
};

PlanTimeline.propTypes = {
  plan: PropTypes.shape({
    id: PropTypes.number,
    jsonb_plan: PropTypes.object
  }),
  mode: PropTypes.oneOf(['view', 'edit'])
};

export default PlanTimeline;