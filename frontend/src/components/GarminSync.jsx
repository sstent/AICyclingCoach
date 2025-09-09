import { useState, useEffect } from 'react';

const GarminSync = () => {
  const [syncStatus, setSyncStatus] = useState(null);
  const [syncing, setSyncing] = useState(false);
  const [error, setError] = useState(null);

  const triggerSync = async () => {
    setSyncing(true);
    setError(null);
    try {
      // Check API key configuration
      if (!process.env.REACT_APP_API_KEY) {
        throw new Error('API key missing - check environment configuration');
      }

      const response = await fetch('/api/workouts/sync', {
        method: 'POST',
        headers: {
          'X-API-Key': process.env.REACT_APP_API_KEY,
          'Content-Type': 'application/json'
        }
      });
      
      if (!response.ok) {
        throw new Error(`Sync failed: ${response.statusText}`);
      }
      
      // Start polling for status updates
      pollSyncStatus();
    } catch (err) {
      console.error('Garmin sync failed:', err);
      setError(err.message);
      setSyncing(false);
    }
  };

  const pollSyncStatus = () => {
    const interval = setInterval(async () => {
      try {
        const response = await fetch('/api/workouts/sync-status');
        const status = await response.json();
        setSyncStatus(status);
        
        // Stop polling when sync is no longer in progress
        if (status.status !== 'in_progress') {
          setSyncing(false);
          clearInterval(interval);
        }
      } catch (err) {
        console.error('Error fetching sync status:', err);
        setError('Failed to get sync status');
        setSyncing(false);
        clearInterval(interval);
      }
    }, 2000);
  };

  return (
    <div className="garmin-sync bg-gray-50 p-4 rounded-lg shadow">
      <h3 className="text-lg font-medium text-gray-800 mb-3">Garmin Connect Sync</h3>
      
      <button 
        onClick={triggerSync} 
        disabled={syncing}
        className={`px-4 py-2 rounded-md font-medium ${
          syncing ? 'bg-gray-400 cursor-not-allowed' : 'bg-blue-600 hover:bg-blue-700'
        } text-white transition-colors`}
      >
        {syncing ? (
          <span className="flex items-center">
            <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            Syncing...
          </span>
        ) : 'Sync Recent Activities'}
      </button>
      
      {error && (
        <div className="mt-3 p-2 bg-red-50 text-red-700 rounded-md">
          Error: {error}
        </div>
      )}
      
      {syncStatus && (
        <div className="mt-4 p-3 bg-white rounded-md border border-gray-200">
          <h4 className="font-medium text-gray-700 mb-2">Sync Status</h4>
          
          <div className="grid grid-cols-2 gap-2 text-sm">
            <div className="text-gray-600">Last sync:</div>
            <div className="text-gray-800">
              {syncStatus.last_sync_time 
                ? new Date(syncStatus.last_sync_time).toLocaleString() 
                : 'Never'}
            </div>
            
            <div className="text-gray-600">Status:</div>
            <div className={`font-medium ${
              syncStatus.status === 'success' ? 'text-green-600' : 
              syncStatus.status === 'error' ? 'text-red-600' : 'text-blue-600'
            }`}>
              {syncStatus.status}
            </div>
            
            {syncStatus.activities_synced > 0 && (
              <>
                <div className="text-gray-600">Activities synced:</div>
                <div className="text-gray-800">{syncStatus.activities_synced}</div>
              </>
            )}
            
            <div className="text-gray-600">Last Updated:</div>
            <div className="text-gray-800">
              {syncStatus.last_sync_time
                ? new Date(syncStatus.last_sync_time).toLocaleTimeString([], {
                    hour: '2-digit', minute: '2-digit', hour12: true
                  })
                : 'Never'}
            </div>
            
            {syncStatus.activities_synced > 0 && (
              <>
                <div className="text-gray-600">New Activities:</div>
                <div className="text-green-600 font-medium">{syncStatus.activities_synced}</div>
              </>
            )}
            
            {syncStatus.warnings?.length > 0 && (
              <>
                <div className="text-gray-600">Warnings:</div>
                <div className="text-yellow-600 text-sm">
                  {syncStatus.warnings.join(', ')}
                </div>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default GarminSync;