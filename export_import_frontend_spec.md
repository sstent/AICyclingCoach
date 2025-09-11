# Export/Import Frontend Implementation

## File Structure
```
src/pages/
  ExportImport.jsx        # Main page

src/components/export/
  DataExporter.jsx        # Export functionality
  DataImporter.jsx        # Import functionality
  ConflictDialog.jsx      # Conflict resolution UI
  ImportSummary.jsx       # Post-import report
```

## Component Specifications

### ExportImport.jsx
```jsx
import { useState } from 'react';
import DataExporter from '../components/export/DataExporter';
import DataImporter from '../components/export/DataImporter';

export default function ExportImportPage() {
  const [activeTab, setActiveTab] = useState('export');

  return (
    <div className="export-import-page">
      <div className="tabs">
        <button onClick={() => setActiveTab('export')}>Export</button>
        <button onClick={() => setActiveTab('import')}>Import</button>
      </div>
      
      {activeTab === 'export' ? <DataExporter /> : <DataImporter />}
    </div>
  );
}
```

### DataExporter.jsx
```jsx
import { useState } from 'react';

const EXPORT_TYPES = [
  { id: 'routes', label: 'Routes' },
  { id: 'rules', label: 'Training Rules' },
  { id: 'plans', label: 'Training Plans' }
];

const EXPORT_FORMATS = [
  { id: 'json', label: 'JSON' },
  { id: 'zip', label: 'ZIP Archive' },
  { id: 'gpx', label: 'GPX Files' }
];

export default function DataExporter() {
  const [selectedTypes, setSelectedTypes] = useState([]);
  const [selectedFormat, setSelectedFormat] = useState('json');
  const [isExporting, setIsExporting] = useState(false);
  const [progress, setProgress] = useState(0);

  const handleExport = async () => {
    setIsExporting(true);
    // API call to /api/export?types=...&format=...
    // Track progress and trigger download
  };

  return (
    <div className="exporter">
      <h2>Export Data</h2>
      
      <div className="type-selection">
        <h3>Select Data to Export</h3>
        {EXPORT_TYPES.map(type => (
          <label key={type.id}>
            <input 
              type="checkbox"
              checked={selectedTypes.includes(type.id)}
              onChange={() => toggleType(type.id)} 
            />
            {type.label}
          </label>
        ))}
      </div>
      
      <div className="format-selection">
        <h3>Export Format</h3>
        <select value={selectedFormat} onChange={e => setSelectedFormat(e.target.value)}>
          {EXPORT_FORMATS.map(format => (
            <option key={format.id} value={format.id}>{format.label}</option>
          ))}
        </select>
      </div>
      
      <button 
        onClick={handleExport} 
        disabled={selectedTypes.length === 0 || isExporting}
      >
        {isExporting ? `Exporting... ${progress}%` : 'Export Data'}
      </button>
    </div>
  );
}
```

### DataImporter.jsx
```jsx
import { useState } from 'react';
import ConflictDialog from './ConflictDialog';

export default function DataImporter() {
  const [file, setFile] = useState(null);
  const [validation, setValidation] = useState(null);
  const [isImporting, setIsImporting] = useState(false);
  const [showConflictDialog, setShowConflictDialog] = useState(false);

  const handleFileUpload = (e) => {
    const file = e.target.files[0];
    setFile(file);
    // Call /api/import/validate
    // Set validation results
  };

  const handleImport = () => {
    if (validation?.conflicts?.length > 0) {
      setShowConflictDialog(true);
    } else {
      startImport();
    }
  };

  const startImport = (resolutions = []) => {
    setIsImporting(true);
    // Call /api/import with conflict resolutions
  };

  return (
    <div className="importer">
      <h2>Import Data</h2>
      
      <input type="file" onChange={handleFileUpload} />
      
      {validation && (
        <div className="validation-results">
          <h3>Validation Results</h3>
          <p>Found: {validation.summary.routes} routes, 
             {validation.summary.rules} rules, 
             {validation.summary.plans} plans</p>
          {validation.conflicts.length > 0 && (
            <p>⚠️ {validation.conflicts.length} conflicts detected</p>
          )}
        </div>
      )}
      
      <button 
        onClick={handleImport} 
        disabled={!file || isImporting}
      >
        {isImporting ? 'Importing...' : 'Import Data'}
      </button>
      
      {showConflictDialog && (
        <ConflictDialog 
          conflicts={validation.conflicts}
          onResolve={startImport}
          onCancel={() => setShowConflictDialog(false)}
        />
      )}
    </div>
  );
}
```

### ConflictDialog.jsx
```jsx
export default function ConflictDialog({ conflicts, onResolve, onCancel }) {
  const [resolutions, setResolutions] = useState({});
  
  const handleResolution = (id, action) => {
    setResolutions(prev => ({ ...prev, [id]: action }));
  };

  const applyResolutions = () => {
    const resolutionList = Object.entries(resolutions).map(([id, action]) => ({
      id,
      action
    }));
    onResolve(resolutionList);
  };

  return (
    <div className="conflict-dialog">
      <h3>Resolve Conflicts</h3>
      <div className="conflicts-list">
        {conflicts.map(conflict => (
          <div key={conflict.id} className="conflict-item">
            <h4>{conflict.name} ({conflict.type})</h4>
            <p>Existing version: {conflict.existing_version}</p>
            <p>Import version: {conflict.import_version}</p>
            <select 
              value={resolutions[conflict.id] || 'skip'} 
              onChange={e => handleResolution(conflict.id, e.target.value)}
            >
              <option value="overwrite">Overwrite</option>
              <option value="rename">Rename</option>
              <option value="skip">Skip</option>
            </select>
          </div>
        ))}
      </div>
      <div className="actions">
        <button onClick={onCancel}>Cancel</button>
        <button onClick={applyResolutions}>Apply Resolutions</button>
      </div>
    </div>
  );
}
```

## Dependencies to Install
```bash
npm install react-dropzone react-json-view file-saver