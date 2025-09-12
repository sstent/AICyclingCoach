import { useState } from 'react';
import { useRouter } from 'next/router';
import { useAuth } from '../src/context/AuthContext';
import GoalSelector from '../src/components/plans/GoalSelector';
import PlanParameters from '../src/components/plans/PlanParameters';
import { generatePlan } from '../src/services/planService';
import ProgressTracker from '../src/components/ui/ProgressTracker';

const PlanGeneration = () => {
  const { apiKey } = useAuth();
  const router = useRouter();
  const [step, setStep] = useState(1);
  const [goals, setGoals] = useState([]);
  const [rules, setRules] = useState([]);
  const [params, setParams] = useState({
    duration: 4,
    weeklyHours: 8,
    availableDays: []
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleGenerate = async () => {
    try {
      setLoading(true);
      const plan = await generatePlan(apiKey, {
        goals,
        ruleIds: rules,
        ...params
      });
      router.push(`/plans/${plan.id}/preview`);
    } catch (err) {
      setError('Failed to generate plan. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto p-6">
      <ProgressTracker currentStep={step} totalSteps={3} />
      
      {step === 1 && (
        <GoalSelector 
          goals={goals}
          onSelect={setGoals}
          onNext={() => setStep(2)}
        />
      )}
      
      {step === 2 && (
        <PlanParameters
          values={params}
          onChange={setParams}
          onBack={() => setStep(1)}
          onNext={() => setStep(3)}
        />
      )}
      
      {step === 3 && (
        <div className="bg-white p-6 rounded-lg shadow-md">
          <h2 className="text-2xl font-bold mb-4">Review and Generate</h2>
          <div className="mb-6">
            <h3 className="font-semibold mb-2">Selected Goals:</h3>
            <ul className="list-disc pl-5">
              {goals.map((goal, index) => (
                <li key={index}>{goal}</li>
              ))}
            </ul>
          </div>
          <button
            onClick={handleGenerate}
            disabled={loading}
            className="bg-blue-600 text-white px-6 py-2 rounded-md hover:bg-blue-700 disabled:bg-gray-400"
          >
            {loading ? 'Generating...' : 'Generate Plan'}
          </button>
          {error && <p className="text-red-500 mt-2">{error}</p>}
        </div>
      )}
    </div>
  );
};

export default PlanGeneration;