import { useState, useEffect } from 'react';
import axios from 'axios';
import { useAuth } from '../../context/AuthContext';
import { formatDistanceToNow } from 'date-fns';

const PlanTimeline = ({ planId }) => {
  const { apiKey } = useAuth();
  const [evolution, setEvolution] = useState([]);
  const [selectedVersion, setSelectedVersion] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchEvolution = async () => {
      try {
        const response = await axios.get(`/api/plans/${planId}/evolution`, {
          headers: { 'X-API-Key': apiKey }
        });
        setEvolution(response.data.evolution_history);
        setSelectedVersion(response.data.current_version);
      } catch (error) {
        console.error('Error fetching plan evolution:', error);
      } finally {
        setLoading(false);
      }
    };

    if (planId) {
      fetchEvolution();
    }
  }, [planId, apiKey]);

  if (loading) return <div>Loading plan history...</div>;

  return (
    <div className="bg-white p-6 rounded-lg shadow-md">
      <h3 className="text-xl font-semibold mb-4">Plan Evolution</h3>
      
      <div className="flex flex-col md:flex-row gap-6">
        <div className="md:w-1/3 space-y-4">
          {evolution.map((version, idx) => (
            <div
              key={version.version}
              onClick={() => setSelectedVersion(version)}
              className={`p-4 border-l-4 cursor-pointer transition-colors ${
                selectedVersion?.version === version.version
                  ? 'border-blue-500 bg-blue-50'
                  : 'border-gray-200 hover:bg-gray-50'
              }`}
            >
              <div className="flex justify-between items-center">
                <span className="font-medium">v{version.version}</span>
                <span className="text-sm text-gray-500">
                  {formatDistanceToNow(new Date(version.created_at))} ago
                </span>
              </div>
              <p className="text-sm text-gray-600 mt-1">
                {version.trigger || 'Initial version'}
              </p>
            </div>
          ))}
        </div>

        {selectedVersion && (
          <div className="md:w-2/3 p-4 bg-gray-50 rounded-md">
            <h4 className="font-medium mb-4">
              Version {selectedVersion.version} Details
            </h4>
            <div className="space-y-3">
              <p>
                <span className="font-medium">Created:</span>{' '}
                {new Date(selectedVersion.created_at).toLocaleString()}
              </p>
              {selectedVersion.changes_summary && (
                <p>
                  <span className="font-medium">Changes:</span>{' '}
                  {selectedVersion.changes_summary}
                </p>
              )}
              {selectedVersion.parent_plan_id && (
                <p>
                  <span className="font-medium">Parent Version:</span>{' '}
                  v{selectedVersion.parent_plan_id}
                </p>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default PlanTimeline;