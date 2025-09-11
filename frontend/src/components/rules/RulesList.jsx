import { useState } from 'react';
import PropTypes from 'prop-types';
import { format } from 'date-fns';

const RulesList = ({ ruleSets, onSelect }) => {
  const [selectedSet, setSelectedSet] = useState(null);

  return (
    <div className="border rounded-lg p-4 bg-white shadow-sm">
      <h2 className="text-xl font-semibold mb-4">Saved Rule Sets</h2>
      
      {ruleSets.length === 0 ? (
        <div className="text-gray-500 text-center py-4">
          No rule sets saved yet. Create one using the editor above.
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="text-left border-b">
                <th className="pb-2">Name</th>
                <th className="pb-2">Version</th>
                <th className="pb-2">Status</th>
                <th className="pb-2">Created</th>
                <th className="pb-2">Actions</th>
              </tr>
            </thead>
            <tbody>
              {ruleSets.map((set) => (
                <tr key={set.id} className="border-b hover:bg-gray-50">
                  <td className="py-3">{set.name || 'Untitled Rules'}</td>
                  <td className="py-3">v{set.version}</td>
                  <td className="py-3">
                    <span className={`px-2 py-1 rounded-full text-sm ${
                      set.active 
                        ? 'bg-green-100 text-green-800' 
                        : 'bg-gray-100 text-gray-600'
                    }`}>
                      {set.active ? 'Active' : 'Inactive'}
                    </span>
                  </td>
                  <td className="py-3">
                    {format(new Date(set.created_at), 'MMM dd, yyyy')}
                  </td>
                  <td className="py-3">
                    <button
                      onClick={() => {
                        setSelectedSet(set);
                        onSelect(set);
                      }}
                      className="text-blue-600 hover:text-blue-800"
                    >
                      View/Edit
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Version History Modal */}
      {selectedSet && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center">
          <div className="bg-white rounded-lg p-6 max-w-2xl w-full">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-semibold">
                {selectedSet.name} Version History
              </h3>
              <button
                onClick={() => setSelectedSet(null)}
                className="text-gray-500 hover:text-gray-700"
              >
                ✕
              </button>
            </div>
            <div className="space-y-2">
              {selectedSet.history?.map((version) => (
                <div 
                  key={version.version}
                  className="p-3 border rounded-lg hover:bg-gray-50"
                >
                  <div className="flex justify-between items-center">
                    <div>
                      <span className="font-medium">v{version.version}</span>
                      <span className="text-sm text-gray-500 ml-2">
                        {format(new Date(version.created_at), 'MMM dd, yyyy HH:mm')}
                      </span>
                    </div>
                    <button
                      onClick={() => onSelect(version)}
                      className="text-sm text-blue-600 hover:text-blue-800"
                    >
                      Restore
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

RulesList.propTypes = {
  ruleSets: PropTypes.array.isRequired,
  onSelect: PropTypes.func.isRequired
};

export default RulesList;