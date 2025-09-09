import { useState, useEffect } from 'react';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import PlanTimeline from '../components/plans/PlanTimeline';

const Plans = () => {
  const { apiKey } = useAuth();
  const [plans, setPlans] = useState([]);
  const [selectedPlan, setSelectedPlan] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchPlans = async () => {
      try {
        const response = await axios.get('/api/plans', {
          headers: { 'X-API-Key': apiKey }
        });
        setPlans(response.data);
        if (response.data.length > 0) {
          setSelectedPlan(response.data[0].id);
        }
      } catch (err) {
        setError('Failed to load training plans');
      } finally {
        setLoading(false);
      }
    };
    
    fetchPlans();
  }, [apiKey]);

  if (loading) return <div className="p-6 text-center">Loading plans...</div>;
  if (error) return <div className="p-6 text-red-600">{error}</div>;

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <h1 className="text-3xl font-bold mb-8">Training Plans</h1>
      
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="space-y-4">
          {plans.map(plan => (
            <div
              key={plan.id}
              onClick={() => setSelectedPlan(plan.id)}
              className={`p-4 bg-white rounded-lg shadow-md cursor-pointer ${
                selectedPlan === plan.id ? 'ring-2 ring-blue-500' : ''
              }`}
            >
              <h3 className="font-medium">Plan v{plan.version}</h3>
              <p className="text-sm text-gray-600">
                Created {new Date(plan.created_at).toLocaleDateString()}
              </p>
            </div>
          ))}
        </div>

        <div className="lg:col-span-2">
          {selectedPlan && <PlanTimeline planId={selectedPlan} />}
        </div>
      </div>
    </div>
  );
};

export default Plans;