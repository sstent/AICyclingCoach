import { JSONTree } from 'react-json-tree';
import PropTypes from 'prop-types';

const RulePreview = ({ rules, onSave, isSaving }) => {
  return (
    <div className="border rounded-lg p-4 bg-white shadow-sm">
      <h2 className="text-xl font-semibold mb-4">Rule Configuration Preview</h2>
      
      <div className="border rounded-lg overflow-hidden mb-4">
        {rules ? (
          <JSONTree
            data={rules}
            theme="harmonic"
            hideRoot={false}
            shouldExpandNodeInitially={() => true}
            style={{ padding: '1rem' }}
          />
        ) : (
          <div className="p-4 text-gray-500">
            Parsed rules will appear here...
          </div>
        )}
      </div>

      <button
        onClick={onSave}
        disabled={!rules || isSaving}
        className={`w-full py-2 rounded-lg font-medium ${
          rules && !isSaving
            ? 'bg-green-600 text-white hover:bg-green-700'
            : 'bg-gray-200 text-gray-500 cursor-not-allowed'
        }`}
      >
        {isSaving ? 'Saving...' : 'Save Rule Set'}
      </button>
    </div>
  );
};

RulePreview.propTypes = {
  rules: PropTypes.object,
  onSave: PropTypes.func.isRequired,
  isSaving: PropTypes.bool.isRequired
};

export default RulePreview;