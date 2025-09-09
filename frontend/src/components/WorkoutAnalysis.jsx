import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

const WorkoutAnalysis = ({ workout, analysis }) => {
  const [approving, setApproving] = useState(false);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  const approveAnalysis = async () => {
    setApproving(true);
    setError(null);
    try {
      const response = await fetch(`/api/analyses/${analysis.id}/approve`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-API-Key': process.env.REACT_APP_API_KEY
        }
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.message || 'Approval failed');
      }
      
      const result = await response.json();
      
      if (result.new_plan_id) {
        // Navigate to the new plan
        navigate(`/plans/${result.new_plan_id}`);
      } else {
        // Show success message
        setApproving(false);
        alert('Analysis approved successfully!');
      }
    } catch (err) {
      console.error('Approval failed:', err);
      setError(err.message);
      setApproving(false);
    }
  };

  return (
    <div className="workout-analysis bg-white rounded-lg shadow-md p-5">
      <div className="workout-summary border-b border-gray-200 pb-4 mb-4">
        <h3 className="text-xl font-semibold text-gray-800">
          {workout.activity_type || 'Cycling'} - {new Date(workout.start_time).toLocaleDateString()}
        </h3>
        
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mt-3 text-sm">
          <div className="metric-card">
            <span className="text-gray-500">Duration</span>
            <span className="font-medium">
              {Math.round(workout.duration_seconds / 60)} min
            </span>
          </div>
          
          <div className="metric-card">
            <span className="text-gray-500">Distance</span>
            <span className="font-medium">
              {(workout.distance_m / 1000).toFixed(1)} km
            </span>
          </div>
          
          {workout.avg_power && (
            <div className="metric-card">
              <span className="text-gray-500">Avg Power</span>
              <span className="font-medium">
                {Math.round(workout.avg_power)}W
              </span>
            </div>
          )}
          
          {workout.avg_hr && (
            <div className="metric-card">
              <span className="text-gray-500">Avg HR</span>
              <span className="font-medium">
                {Math.round(workout.avg_hr)} bpm
              </span>
            </div>
          )}
        </div>
      </div>

      {analysis && (
        <div className="analysis-content">
          <h4 className="text-lg font-medium text-gray-800 mb-3">AI Analysis</h4>
          
          <div className="feedback-box bg-blue-50 p-4 rounded-md mb-5">
            <p className="text-gray-700">{analysis.jsonb_feedback.summary}</p>
          </div>
          
          <div className="strengths-improvement grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
            <div className="strengths">
              <h5 className="font-medium text-green-700 mb-2">Strengths</h5>
              <ul className="list-disc pl-5 space-y-1">
                {analysis.jsonb_feedback.strengths.map((strength, index) => (
                  <li key={index} className="text-gray-700">{strength}</li>
                ))}
              </ul>
            </div>
            
            <div className="improvements">
              <h5 className="font-medium text-orange-600 mb-2">Areas for Improvement</h5>
              <ul className="list-disc pl-5 space-y-1">
                {analysis.jsonb_feedback.areas_for_improvement.map((area, index) => (
                  <li key={index} className="text-gray-700">{area}</li>
                ))}
              </ul>
            </div>
          </div>
          
          {analysis.suggestions && analysis.suggestions.length > 0 && (
            <div className="suggestions bg-yellow-50 p-4 rounded-md mb-5">
              <h5 className="font-medium text-gray-800 mb-3">Training Suggestions</h5>
              <ul className="space-y-2">
                {analysis.suggestions.map((suggestion, index) => (
                  <li key={index} className="flex items-start">
                    <span className="inline-block w-6 h-6 bg-yellow-100 text-yellow-800 rounded-full text-center mr-2 flex-shrink-0">
                      {index + 1}
                    </span>
                    <span className="text-gray-700">{suggestion}</span>
                  </li>
                ))}
              </ul>
              
              {!analysis.approved && (
                <div className="mt-4">
                  <button 
                    onClick={approveAnalysis}
                    disabled={approving}
                    className={`px-4 py-2 rounded-md font-medium ${
                      approving ? 'bg-gray-400 cursor-not-allowed' : 'bg-green-600 hover:bg-green-700'
                    } text-white transition-colors flex items-center`}
                  >
                    {approving ? (
                      <>
                        <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                        Applying suggestions...
                      </>
                    ) : 'Approve & Update Training Plan'}
                  </button>
                  
                  {error && (
                    <div className="mt-2 text-red-600 text-sm">
                      Error: {error}
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );

  useEffect(() => {
    const fetchMetrics = async () => {
      try {
        const response = await fetch(`/api/workouts/${workout.id}/metrics`);
        const data = await response.json();
        setMetrics(data);
      } catch (err) {
        console.error('Error fetching workout metrics:', err);
      } finally {
        setLoadingMetrics(false);
      }
    };

    if (workout?.id) {
      fetchMetrics();
    }
  }, [workout]);

  return (
    <div className="workout-analysis bg-white rounded-lg shadow-md p-5 space-y-6">
      {/* Workout Summary */}
      <div className="workout-summary border-b border-gray-200 pb-4 mb-4">
        <h3 className="text-xl font-semibold text-gray-800">
          {workout.activity_type || 'Cycling'} - {new Date(workout.start_time).toLocaleDateString()}
        </h3>
        
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mt-3 text-sm">
          {/* Existing metric cards */}
        </div>
      </div>

      {/* Metrics Charts */}
      {/* Existing chart implementation */}

      {/* Analysis Content */}
      {/* Existing analysis content */}
    </div>
  );
};

export default WorkoutAnalysis;