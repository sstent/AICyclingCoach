import { useState, useEffect } from 'react';
import PropTypes from 'prop-types';

const daysOfWeek = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];

const PlanParameters = ({ values, onChange, onBack, onNext }) => {
  const [localValues, setLocalValues] = useState(values);
  
  useEffect(() => {
    setLocalValues(values);
  }, [values]);

  const handleChange = (field, value) => {
    const newValues = { ...localValues, [field]: value };
    setLocalValues(newValues);
    onChange(newValues);
  };

  const toggleDay = (day) => {
    const days = localValues.availableDays.includes(day)
      ? localValues.availableDays.filter(d => d !== day)
      : [...localValues.availableDays, day];
    handleChange('availableDays', days);
  };

  return (
    <div className="bg-white p-6 rounded-lg shadow-md">
      <h2 className="text-2xl font-bold mb-6">Set Plan Parameters</h2>
      
      <div className="space-y-6">
        <div>
          <label className="block text-sm font-medium mb-2">
            Duration: {localValues.duration} weeks
          </label>
          <input
            type="range"
            min="4"
            max="20"
            value={localValues.duration}
            onChange={(e) => handleChange('duration', parseInt(e.target.value))}
            className="w-full range-slider"
          />
          <div className="flex justify-between text-sm text-gray-600">
            <span>4</span>
            <span>20</span>
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium mb-2">
            Weekly Hours: {localValues.weeklyHours}h
          </label>
          <input
            type="range"
            min="5"
            max="15"
            value={localValues.weeklyHours}
            onChange={(e) => handleChange('weeklyHours', parseInt(e.target.value))}
            className="w-full range-slider"
          />
          <div className="flex justify-between text-sm text-gray-600">
            <span>5</span>
            <span>15</span>
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium mb-2">Difficulty Level</label>
          <select
            value={localValues.difficulty || 'intermediate'}
            onChange={(e) => handleChange('difficulty', e.target.value)}
            className="w-full p-2 border rounded-md"
          >
            <option value="beginner">Beginner</option>
            <option value="intermediate">Intermediate</option>
            <option value="advanced">Advanced</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium mb-2">Available Days</label>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
            {daysOfWeek.map(day => (
              <label key={day} className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  checked={localValues.availableDays.includes(day)}
                  onChange={() => toggleDay(day)}
                  className="form-checkbox h-4 w-4 text-blue-600"
                />
                <span className="text-sm">{day}</span>
              </label>
            ))}
          </div>
        </div>
      </div>

      <div className="flex justify-between mt-8">
        <button
          onClick={onBack}
          className="bg-gray-200 text-gray-700 px-6 py-2 rounded-md hover:bg-gray-300"
        >
          Back
        </button>
        <button
          onClick={onNext}
          disabled={localValues.availableDays.length === 0}
          className="bg-blue-600 text-white px-6 py-2 rounded-md hover:bg-blue-700 disabled:bg-gray-400"
        >
          Next
        </button>
      </div>
    </div>
  );
};

PlanParameters.propTypes = {
  values: PropTypes.shape({
    duration: PropTypes.number,
    weeklyHours: PropTypes.number,
    difficulty: PropTypes.string,
    availableDays: PropTypes.arrayOf(PropTypes.string)
  }).isRequired,
  onChange: PropTypes.func.isRequired,
  onBack: PropTypes.func.isRequired,
  onNext: PropTypes.func.isRequired
};

export default PlanParameters;