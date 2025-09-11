import { useState, useEffect } from 'react';
import RuleEditor from '../components/rules/RuleEditor';
import RulePreview from '../components/rules/RulePreview';
import RulesList from '../components/rules/RulesList';
import { getRuleSets, createRuleSet, parseRule } from '../services/ruleService';

const RulesPage = () => {
  const [ruleText, setRuleText] = useState('');
  const [parsedRules, setParsedRules] = useState(null);
  const [ruleSets, setRuleSets] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  // Load initial rule sets
  useEffect(() => {
    const loadRuleSets = async () => {
      try {
        const { data } = await getRuleSets();
        setRuleSets(data);
      } catch (err) {
        setError('Failed to load rule sets');
      }
    };
    loadRuleSets();
  }, []);

  const handleSave = async () => {
    setIsLoading(true);
    try {
      await createRuleSet({
        naturalLanguage: ruleText,
        jsonRules: parsedRules
      });
      setRuleText('');
      setParsedRules(null);
      // Refresh rule sets list
      const { data } = await getRuleSets();
      setRuleSets(data);
    } catch (err) {
      setError('Failed to save rule set');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <h1 className="text-3xl font-bold mb-6">Training Rules Management</h1>
      
      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
          {error}
        </div>
      )}

      <div className="flex gap-6 mb-8">
        <div className="flex-1">
          <RuleEditor 
            value={ruleText}
            onChange={setRuleText}
            onParse={setParsedRules}
          />
        </div>
        
        <div className="flex-1">
          <RulePreview 
            rules={parsedRules} 
            onSave={handleSave}
            isSaving={isLoading}
          />
        </div>
      </div>

      <RulesList 
        ruleSets={ruleSets}
        onSelect={(set) => {
          setRuleText(set.naturalLanguage);
          setParsedRules(set.jsonRules);
        }}
      />
    </div>
  );
};

export default RulesPage;