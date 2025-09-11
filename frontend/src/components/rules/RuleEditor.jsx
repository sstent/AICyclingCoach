import { useState, useEffect } from 'react';
import PropTypes from 'prop-types';
import { parseRule } from '../../services/ruleService';

const RuleEditor = ({ value, onChange, onParse }) => {
  const [charCount, setCharCount] = useState(0);
  const [isValid, setIsValid] = useState(true);
  const [showTemplates, setShowTemplates] = useState(false);
  
  // Auto-resize textarea
  useEffect(() => {
    const textarea = document.getElementById('ruleEditor');
    textarea.style.height = 'auto';
    textarea.style.height = `${textarea.scrollHeight}px`;
  }, [value]);

  // Enhanced validation
  useEffect(() => {
    const count = value.length;
    setCharCount(count);
    
    const hasRequiredKeywords = /(maximum|minimum|at least|no more than)/i.test(value);
    const hasNumbersWithUnits = /\d+\s+(rides?|hours?|days?|weeks?)/i.test(value);
    const hasConstraints = /(between|recovery|interval|duration)/i.test(value);
    
    setIsValid(
      count <= 5000 &&
      count >= 10 &&
      hasRequiredKeywords &&
      hasNumbersWithUnits &&
      hasConstraints
    );
  }, [value]);

  const handleParse = async () => {
    try {
      const { data } = await parseRule(value);
      onParse(data.jsonRules);
    } catch (err) {
      console.error('Parsing failed:', err);
    }
  };

  const templateSuggestions = [
    'Maximum 4 rides per week with at least one rest day between hard workouts',
    'Long rides limited to 3 hours maximum during weekdays',
    'No outdoor rides when temperature drops below 0°C',
    'Interval sessions limited to twice weekly with 48h recovery'
  ];

  return (
    <div className="border rounded-lg p-4 bg-white shadow-sm">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-semibold">Natural Language Editor</h2>
        <div className="relative">
          <button
            onClick={() => setShowTemplates(!showTemplates)}
            className="px-3 py-1 bg-blue-100 text-blue-800 rounded-lg hover:bg-blue-200"
          >
            Templates
          </button>
          {showTemplates && (
            <div className="absolute right-0 mt-2 w-64 bg-white border rounded-lg shadow-lg z-10">
              {templateSuggestions.map((template, index) => (
                <div
                  key={index}
                  className="p-3 hover:bg-gray-50 cursor-pointer border-b"
                  onClick={() => {
                    onChange(template);
                    setShowTemplates(false);
                  }}
                >
                  {template}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      <textarea
        id="ruleEditor"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className={`w-full p-3 border rounded-lg focus:ring-2 ${
          isValid ? 'focus:ring-blue-500' : 'focus:ring-red-500'
        }`}
        placeholder="Enter your training rules in natural language..."
        rows="5"
      />

      <div className="flex justify-between items-center mt-4">
        <div className="text-sm text-gray-600">
          {charCount}/5000 characters •{' '}
          <span className={isValid ? 'text-green-600' : 'text-red-600'}>
            {isValid ? 'Valid' : 'Invalid input'}
          </span>
        </div>
        <button
          onClick={handleParse}
          disabled={!isValid}
          className={`px-4 py-2 rounded-lg ${
            isValid
              ? 'bg-blue-600 text-white hover:bg-blue-700'
              : 'bg-gray-300 text-gray-500 cursor-not-allowed'
          }`}
        >
          Parse Rules
        </button>
      </div>
    </div>
  );
};

RuleEditor.propTypes = {
  value: PropTypes.string.isRequired,
  onChange: PropTypes.func.isRequired,
  onParse: PropTypes.func.isRequired
};

export default RuleEditor;