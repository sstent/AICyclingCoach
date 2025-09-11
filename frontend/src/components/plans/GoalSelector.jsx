import { useState } from 'react';
import PropTypes from 'prop-types';

const predefinedGoals = [
  { id: 'endurance', label: 'Build Endurance', description: 'Focus on longer rides at moderate intensity' },
  { id: 'power', label: 'Increase Power', description: 'High-intensity intervals and strength training' },
  { id: 'weight-loss', label: 'Weight Management', description: 'Calorie-burning rides with nutrition planning' },
  { id: 'event-prep', label: 'Event Preparation', description: 'Targeted training for specific competitions' }
];

const GoalSelector = ({ goals, onSelect, onNext }) => {
  const [customGoal, setCustomGoal] = useState('');
  const [showCustom, setShowCustom] = useState(false);

  const toggleGoal = (goalId) => {
    const newGoals = goals.includes(goalId)
      ? goals.filter(g => g !== goalId)
      : [...goals, goalId];
    onSelect(newGoals);
  };

  const addCustomGoal = () => {
    if (customGoal.trim()) {
      onSelect([...goals, customGoal.trim()]);
      setCustomGoal('');
      setShowCustom(false);
    }
  };

  return (
    <div className="bg-white p-6 rounded-lg shadow-md">
      <h2 className="text-2xl font-bold mb-6">Select Training Goals</h2>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8">
        {predefinedGoals.map((goal) => (
          <button
            key={goal.id}
            onClick={() => toggleGoal(goal.id)}
            className={`p-4 text-left rounded-lg border-2 transition-colors ${
              goals.includes(goal.id)
                ? 'border-blue-500 bg-blue-50'
                : 'border-gray-200 hover:border-blue-200'
            }`}
          >
            <h3 className="font-semibold mb-2">{goal.label}</h3>
            <p className="text-sm text-gray-600">{goal.description}</p>
          </button>
        ))}
      </div>

      <div className="mb-6">
        {!showCustom ? (
          <button
            onClick={() => setShowCustom(true)}
            className="text-blue-600 hover:text-blue-700 flex items-center"
          >
            <span className="mr-2">+</span> Add Custom Goal
          </button>
        ) : (
          <div className="flex gap-2">
            <input
              type="text"
              value={customGoal}
              onChange={(e) => setCustomGoal(e.target.value)}
              placeholder="Enter custom goal"
              className="flex-1 p-2 border rounded-md"
            />
            <button
              onClick={addCustomGoal}
              className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700"
            >
              Add
            </button>
          </div>
        )}
      </div>

      <div className="flex justify-end">
        <button
          onClick={onNext}
          disabled={goals.length === 0}
          className="bg-blue-600 text-white px-6 py-2 rounded-md hover:bg-blue-700 disabled:bg-gray-400"
        >
          Next
        </button>
      </div>
    </div>
  );
};

GoalSelector.propTypes = {
  goals: PropTypes.arrayOf(PropTypes.string).isRequired,
  onSelect: PropTypes.func.isRequired,
  onNext: PropTypes.func.isRequired
};

export default GoalSelector;