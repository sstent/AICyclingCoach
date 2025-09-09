import { useState, useEffect } from 'react';
import axios from 'axios';
import { useAuth } from '../../context/AuthContext';
import WorkoutMetrics from './WorkoutMetrics';

const WorkoutAnalysis = ({ workoutId }) => {
  const { apiKey } = useAuth();
  const [analysis, setAnalysis] = useState(null);
  const [isApproving, setIsApproving] = useState(false);

  useEffect(() => {
    const fetchAnalysis = async () => {
      try {
        const response = await axios.get(`/api/analyses/${workoutId}`, {
          headers: { 'X-API-Key': apiKey }
        });
        setAnalysis(response.data);
      } catch (error) {
        console.error('Error fetching analysis:', error);
      }
    };
    
    if (workoutId) {
      fetchAnalysis();
    }
  }, [workoutId, apiKey]);

  const handleApprove = async () => {
    setIsApproving(true);
    try {
      await axios.post(`/api/analyses/${analysis.id}/approve`, {}, {
        headers: { 'X-API-Key': apiKey }
      });
      // Refresh analysis data
      const response = await axios.get(`/api/analyses/${analysis.id}`, {
        headers: { 'X-API-Key': apiKey }
      });
      setAnalysis(response.data);
    } catch (error) {
      console.error('Approval failed:', error);
    }
    setIsApproving(false);
  };

  if (!analysis) return <div>Loading analysis...</div>;

  return (
    <div className="bg-white p-6 rounded-lg shadow-md">
      <h3 className="text-xl font-semibold mb-4">
        {analysis.workout.activity_type} Analysis
      </h3>
      
      <WorkoutMetrics workout={analysis.workout} />
      
      <div className="mt-6">
        <h4 className="font-medium mb-2">AI Feedback</h4>
        <div className="bg-gray-50 p-4 rounded-md">
          <p className="mb-3">{analysis.jsonb_feedback.summary}</p>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <h5 className="font-medium">Strengths</h5>
              <ul className="list-disc pl-5">
                {analysis.jsonb_feedback.strengths.map((s, i) => (
                  <li key={i} className="text-green-700">{s}</li>
                ))}
              </ul>
            </div>
            <div>
              <h5 className="font-medium">Improvements</h5>
              <ul className="list-disc pl-5">
                {analysis.jsonb_feedback.areas_for_improvement.map((s, i) => (
                  <li key={i} className="text-orange-700">{s}</li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      </div>

      {analysis.suggestions?.length > 0 && !analysis.approved && (
        <div className="mt-6">
          <button
            onClick={handleApprove}
            disabled={isApproving}
            className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 disabled:bg-gray-400"
          >
            {isApproving ? 'Approving...' : 'Approve Suggestions'}
          </button>
        </div>
      )}

      <WorkoutCharts metrics={analysis.workout.metrics} />
    </div>
  );
};

export default WorkoutAnalysis;