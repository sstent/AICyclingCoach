import { useState, useEffect } from 'react';
import axios from 'axios';
import { formatDistanceToNow } from 'date-fns';

const GarminSync = ({ apiKey }) => {
  const [syncStatus, setSyncStatus] = useState(null);
  const [isSyncing, setIsSyncing] = useState(false);
  const [error, setError] = useState('');

  const fetchSyncStatus = async () => {
    try {
      const response = await axios.get('/api/workouts/sync-status', {
        headers: { 'X-API-Key': apiKey }
      });
      setSyncStatus(response.data);
    } catch (err) {
      setError('Failed to fetch sync status');
    }
  };

  const triggerSync = async () => {
    setIsSyncing(true);
    setError('');
    try {
      await axios.post('/api/workouts/sync', {}, {
        headers: { 'X-API-Key': apiKey }
      });
      // Poll status every 2 seconds
      const interval = setInterval(fetchSyncStatus, 2000);
      setTimeout(() => {
        clearInterval(interval);
        setIsSyncing(false);
      }, 30000);
    } catch (err) {
      setError('Failed to start sync');
      setIsSyncing(false);
    }
  };

  useEffect(() => {
    fetchSyncStatus();
  }, []);

  return (
    <div className="bg-white p-6 rounded-lg shadow-md">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-semibold">Garmin Connect Sync</h2>
        <button
          onClick={triggerSync}
          disabled={isSyncing}
          className={`px-4 py-2 rounded-md ${
            isSyncing ? 'bg-gray-300' : 'bg-blue-600 hover:bg-blue-700'
          } text-white transition-colors`}
        >
          {isSyncing ? 'Syncing...' : 'Sync Now'}
        </button>
      </div>

      {error && (
        <div className="mb-4 p-3 bg-red-100 text-red-700 rounded-md">{error}</div>
      )}

      {syncStatus && (
        <div className="space-y-2">
          <p className="text-sm">
            Last sync: {syncStatus.last_sync_time ? 
              formatDistanceToNow(new Date(syncStatus.last_sync_time)) + ' ago' : 'Never'}
          </p>
          <p className="text-sm">
            Status: <span className="font-medium">{syncStatus.status}</span>
          </p>
          {syncStatus.activities_synced > 0 && (
            <p className="text-sm">
              Activities synced: {syncStatus.activities_synced}
            </p>
          )}
          {syncStatus.error_message && (
            <p className="text-sm text-red-600">{syncStatus.error_message}</p>
          )}
        </div>
      )}
    </div>
  );
};

export default GarminSync;