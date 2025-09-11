import PropTypes from 'prop-types';

const ProgressTracker = ({ currentStep, totalSteps }) => {
  return (
    <div className="mb-8">
      <div className="flex justify-between items-center mb-2">
        {[...Array(totalSteps)].map((_, index) => (
          <div key={index} className="flex items-center">
            <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
              index + 1 <= currentStep 
                ? 'bg-blue-600 text-white' 
                : 'bg-gray-200 text-gray-600'
            }`}>
              {index + 1}
            </div>
            {index < totalSteps - 1 && (
              <div className={`w-16 h-1 ${
                index + 1 < currentStep 
                  ? 'bg-blue-600' 
                  : 'bg-gray-200'
              }`} />
            )}
          </div>
        ))}
      </div>
      <div className="text-sm text-gray-600 text-center">
        Step {currentStep} of {totalSteps}
      </div>
    </div>
  );
};

ProgressTracker.propTypes = {
  currentStep: PropTypes.number.isRequired,
  totalSteps: PropTypes.number.isRequired
};

export default ProgressTracker;