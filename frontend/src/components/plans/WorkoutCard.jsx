import PropTypes from 'prop-types';

const WorkoutCard = ({ workout, onEdit, editable }) => {
  return (
    <div className="border rounded-lg p-4 bg-white shadow-sm">
      <div className="flex justify-between items-start mb-2">
        <h5 className="font-medium capitalize">{workout?.type?.replace('_', ' ') || 'Workout'}</h5>
        {editable && (
          <button 
            onClick={onEdit}
            className="text-blue-600 hover:text-blue-800 text-sm"
          >
            Edit
          </button>
        )}
      </div>
      <div className="text-sm text-gray-600 space-y-1">
        <div>Duration: {workout?.duration_minutes || 0} minutes</div>
        <div>Intensity: {workout?.intensity || 'N/A'}</div>
        {workout?.description && (
          <div className="mt-2 text-gray-700">{workout.description}</div>
        )}
      </div>
    </div>
  );
};

WorkoutCard.propTypes = {
  workout: PropTypes.shape({
    type: PropTypes.string,
    duration_minutes: PropTypes.number,
    intensity: PropTypes.string,
    description: PropTypes.string
  }),
  onEdit: PropTypes.func,
  editable: PropTypes.bool
};

WorkoutCard.defaultProps = {
  workout: {},
  onEdit: () => {},
  editable: false
};

export default WorkoutCard;