# Junior Developer Implementation Guide
## AI Cycling Coach - Critical Features Implementation

This guide provides step-by-step instructions to implement the missing core features identified in the codebase evaluation.

---

## 🎯 **Implementation Phases Overview**

| Phase | Focus | Duration | Difficulty |
|-------|-------|----------|------------|
| **Phase 1** | Backend Core APIs | 2-3 weeks | Medium |
| **Phase 2** | Frontend Core Features | 3-4 weeks | Medium |
| **Phase 3** | Integration & Testing | 1-2 weeks | Easy-Medium |
| **Phase 4** | Polish & Production | 1-2 weeks | Easy |

---

# Phase 1: Backend Core APIs Implementation

## Step 1.1: Plan Generation Endpoint

### **File:** `backend/app/routes/plan.py`

**Add this endpoint to the existing router:**

```python
from app.schemas.plan import PlanGenerationRequest, PlanGenerationResponse
from app.services.ai_service import AIService, AIServiceError

@router.post("/generate", response_model=PlanGenerationResponse)
async def generate_plan(
    request: PlanGenerationRequest,
    db: AsyncSession = Depends(get_db)
):
    """Generate a new training plan using AI based on rules and goals."""
    try:
        # Fetch rules from database
        rules_query = select(Rule).where(Rule.id.in_(request.rule_ids))
        result = await db.execute(rules_query)
        rules = result.scalars().all()
        
        if len(rules) != len(request.rule_ids):
            raise HTTPException(status_code=404, detail="One or more rules not found")
        
        # Get plaintext rules
        rule_texts = [rule.rule_text for rule in rules]
        
        # Initialize AI service
        ai_service = AIService(db)
        
        # Generate plan
        plan_data = await ai_service.generate_plan(rule_texts, request.goals.dict())
        
        # Create plan record
        db_plan = Plan(
            jsonb_plan=plan_data,
            version=1,
            parent_plan_id=None
        )
        db.add(db_plan)
        await db.commit()
        await db.refresh(db_plan)
        
        return PlanGenerationResponse(
            plan=db_plan,
            generation_metadata={
                "rules_used": len(rules),
                "goals": request.goals.dict(),
                "generated_at": datetime.utcnow().isoformat()
            }
        )
        
    except AIServiceError as e:
        raise HTTPException(status_code=503, detail=f"AI service error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Plan generation failed: {str(e)}")
```

### **File:** `backend/app/schemas/plan.py`

**Add these new schemas:**

```python
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from uuid import UUID

class TrainingGoals(BaseModel):
    """Training goals for plan generation."""
    primary_goal: str = Field(..., description="Primary training goal")
    target_weekly_hours: int = Field(..., ge=3, le=20, description="Target hours per week")
    fitness_level: str = Field(..., description="Current fitness level")
    event_date: Optional[str] = Field(None, description="Target event date (YYYY-MM-DD)")
    preferred_routes: List[int] = Field(default=[], description="Preferred route IDs")
    avoid_days: List[str] = Field(default=[], description="Days to avoid training")

class PlanGenerationRequest(BaseModel):
    """Request schema for plan generation."""
    rule_ids: List[UUID] = Field(..., description="Rule set IDs to apply")
    goals: TrainingGoals = Field(..., description="Training goals")
    duration_weeks: int = Field(4, ge=1, le=20, description="Plan duration in weeks")
    user_preferences: Optional[Dict[str, Any]] = Field(None, description="Additional preferences")

class PlanGenerationResponse(BaseModel):
    """Response schema for plan generation."""
    plan: Plan = Field(..., description="Generated training plan")
    generation_metadata: Dict[str, Any] = Field(..., description="Generation metadata")
    
    class Config:
        orm_mode = True
```

---

<REMOVED>

<REMOVED>

**Add these endpoints after the existing routes:**

```python
from app.schemas.rule import NaturalLanguageRuleRequest, ParsedRuleResponse

@router.post("/parse-natural-language", response_model=ParsedRuleResponse)
async def parse_natural_language_rules(
    request: NaturalLanguageRuleRequest,
    db: AsyncSession = Depends(get_db)
):
    """Parse natural language text into structured training rules."""
    try:
        # Initialize AI service
        ai_service = AIService(db)
        
        # Parse rules using AI
        parsed_data = await ai_service.parse_rules_from_natural_language(
            request.natural_language_text
        )
        
        # Validate parsed rules
        validation_result = _validate_parsed_rules(parsed_data)
        
        return ParsedRuleResponse(
            parsed_rules=parsed_data,
            confidence_score=parsed_data.get("confidence", 0.0),
            suggestions=validation_result.get("suggestions", []),
            validation_errors=validation_result.get("errors", []),
            rule_name=request.rule_name
        )
        
    except AIServiceError as e:
        raise HTTPException(status_code=503, detail=f"AI parsing failed: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Rule parsing failed: {str(e)}")

@router.post("/validate-rules")
async def validate_rule_consistency(
    rules_data: Dict[str, Any],
    db: AsyncSession = Depends(get_db)
):
    """Validate rule consistency and detect conflicts."""
    validation_result = _validate_parsed_rules(rules_data)
    return {
        "is_valid": len(validation_result.get("errors", [])) == 0,
        "errors": validation_result.get("errors", []),
        "warnings": validation_result.get("warnings", []),
        "suggestions": validation_result.get("suggestions", [])
    }

def _validate_parsed_rules(parsed_rules: Dict[str, Any]) -> Dict[str, List[str]]:
    """Validate parsed rules for consistency and completeness."""
    errors = []
    warnings = []
    suggestions = []
    
    # Check for required fields
    required_fields = ["max_rides_per_week", "min_rest_between_hard"]
    for field in required_fields:
        if field not in parsed_rules:
            errors.append(f"Missing required field: {field}")
    
    # Validate numeric ranges
    max_rides = parsed_rules.get("max_rides_per_week", 0)
    if max_rides > 7:
        errors.append("Maximum rides per week cannot exceed 7")
    elif max_rides < 1:
        errors.append("Must have at least 1 ride per week")
    
    # Check for conflicts
    max_hours = parsed_rules.get("max_duration_hours", 0)
    if max_rides and max_hours:
        avg_duration = max_hours / max_rides
        if avg_duration > 5:
            warnings.append("Very long average ride duration detected")
        elif avg_duration < 0.5:
            warnings.append("Very short average ride duration detected")
    
    # Provide suggestions
    if "weather_constraints" not in parsed_rules:
        suggestions.append("Consider adding weather constraints for outdoor rides")
    
    return {
        "errors": errors,
        "warnings": warnings,
        "suggestions": suggestions
    }
```

### **File:** `backend/app/schemas/rule.py`

**Replace the existing content with:**

```python
from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List

class NaturalLanguageRuleRequest(BaseModel):
    """Request schema for natural language rule parsing."""
    natural_language_text: str = Field(
        ..., 
        min_length=10, 
        max_length=5000,
        description="Natural language rule description"
    )
    rule_name: str = Field(..., min_length=1, max_length=100, description="Rule set name")
    
    @validator('natural_language_text')
    def validate_text_content(cls, v):
        # Check for required keywords
        required_keywords = ['ride', 'week', 'hour', 'day', 'rest', 'training']
        if not any(keyword in v.lower() for keyword in required_keywords):
            raise ValueError("Text must contain training-related keywords")
        return v

class ParsedRuleResponse(BaseModel):
    """Response schema for parsed rules."""
    parsed_rules: Dict[str, Any] = Field(..., description="Structured rule data")
    confidence_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Parsing confidence")
    suggestions: List[str] = Field(default=[], description="Improvement suggestions")
    validation_errors: List[str] = Field(default=[], description="Validation errors")
    rule_name: str = Field(..., description="Rule set name")

class RuleBase(BaseModel):
    """Base rule schema."""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    user_defined: bool = Field(True, description="Whether rule is user-defined")
    jsonb_rules: Dict[str, Any] = Field(..., description="Structured rule data")
    version: int = Field(1, ge=1, description="Rule version")
    parent_rule_id: Optional[int] = Field(None, description="Parent rule for versioning")

class RuleCreate(RuleBase):
    """Schema for creating new rules."""
    pass

class Rule(RuleBase):
    """Complete rule schema with database fields."""
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True
```

---

<REMOVED>

<REMOVED>

**Add these enhanced methods:**

```python
async def parse_rules_from_natural_language(self, natural_language: str) -> Dict[str, Any]:
    """Enhanced natural language rule parsing with better prompts."""
    prompt_template = await self.prompt_manager.get_active_prompt("rule_parsing")
    
    if not prompt_template:
        # Fallback prompt if none exists in database
        prompt_template = """
        Parse the following natural language training rules into structured JSON format.
        
        Input: "{user_rules}"
        
        Required output format:
        {{
            "max_rides_per_week": <number>,
            "min_rest_between_hard": <number>,
            "max_duration_hours": <number>,
            "intensity_limits": {{
                "max_zone_5_minutes_per_week": <number>,
                "max_consecutive_hard_days": <number>
            }},
            "weather_constraints": {{
                "min_temperature": <number>,
                "max_wind_speed": <number>,
                "no_rain": <boolean>
            }},
            "schedule_constraints": {{
                "preferred_days": [<day_names>],
                "avoid_days": [<day_names>]
            }},
            "confidence": <0.0-1.0>
        }}
        
        Extract specific numbers and constraints. If information is missing, omit the field.
        """
    
    prompt = prompt_template.format(user_rules=natural_language)
    response = await self._make_ai_request(prompt)
    parsed_data = self._parse_rules_response(response)
    
    # Add confidence scoring
    if "confidence" not in parsed_data:
        parsed_data["confidence"] = self._calculate_parsing_confidence(
            natural_language, parsed_data
        )
    
    return parsed_data

def _calculate_parsing_confidence(self, input_text: str, parsed_data: Dict) -> float:
    """Calculate confidence score for rule parsing."""
    confidence = 0.5  # Base confidence
    
    # Increase confidence for explicit numbers
    import re
    numbers = re.findall(r'\d+', input_text)
    if len(numbers) >= 2:
        confidence += 0.2
    
    # Increase confidence for key training terms
    training_terms = ['rides', 'hours', 'week', 'rest', 'recovery', 'training']
    found_terms = sum(1 for term in training_terms if term in input_text.lower())
    confidence += min(0.3, found_terms * 0.05)
    
    # Decrease confidence if parsed data is sparse
    if len(parsed_data) < 3:
        confidence -= 0.2
    
    return max(0.0, min(1.0, confidence))
```

---

# Phase 2: Frontend Core Features Implementation

## Step 2.1: Simplified Rules Management

### **File:** `frontend/src/pages/Rules.jsx`

**Replace with simplified plaintext rules interface:**

```jsx
import React, { useState, useEffect } from 'react';
import { toast } from 'react-toastify';
import RuleEditor from '../components/rules/RuleEditor';
import RulePreview from '../components/rules/RulePreview';
import RulesList from '../components/rules/RulesList';
import { useAuth } from '../context/AuthContext';
import * as ruleService from '../services/ruleService';

const Rules = () => {
  const { apiKey } = useAuth();
  const [activeTab, setActiveTab] = useState('list');
  const [rules, setRules] = useState([]);
  const [selectedRule, setSelectedRule] = useState(null);
  const [naturalLanguageText, setNaturalLanguageText] = useState('');
  const [parsedRules, setParsedRules] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    loadRules();
  }, []);

  const loadRules = async () => {
    try {
      const response = await ruleService.getRules();
      setRules(response.data);
    } catch (error) {
      console.error('Failed to load rules:', error);
      toast.error('Failed to load rules');
    }
  };

  const handleParseRules = async (parsedData) => {
    setParsedRules(parsedData);
    setActiveTab('preview');
  };

  const handleSaveRules = async (ruleName, finalRules) => {
    setIsLoading(true);
    try {
      const ruleData = {
        name: ruleName,
        jsonb_rules: finalRules,
        user_defined: true,
        version: 1
      };

      await ruleService.createRule(ruleData);
      toast.success('Rules saved successfully!');
      
      // Reset form and reload rules
      setNaturalLanguageText('');
      setParsedRules(null);
      setActiveTab('list');
      await loadRules();
    } catch (error) {
      console.error('Failed to save rules:', error);
      toast.error('Failed to save rules');
    } finally {
      setIsLoading(false);
    }
  };

  const handleEditRule = (rule) => {
    setSelectedRule(rule);
    setNaturalLanguageText(rule.description || '');
    setParsedRules(rule.jsonb_rules);
    setActiveTab('edit');
  };

  return (
    <div className="max-w-6xl mx-auto p-6">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Training Rules</h1>
          <p className="text-gray-600 mt-2">
            Define your training constraints and preferences using natural language
          </p>
        </div>
        
        <button
          onClick={() => setActiveTab('create')}
          className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
        >
          Create New Rules
        </button>
      </div>

      {/* Tab Navigation */}
      <div className="border-b border-gray-200 mb-6">
        <nav className="-mb-px flex space-x-8">
          {[
            { key: 'list', label: 'All Rules' },
            { key: 'create', label: 'Create Rules' },
            { key: 'preview', label: 'Preview' }
          ].map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === tab.key
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      {activeTab === 'list' && (
        <RulesList
          rules={rules}
          onEdit={handleEditRule}
          onDelete={async (ruleId) => {
            try {
              await ruleService.deleteRule(ruleId);
              toast.success('Rule deleted');
              await loadRules();
            } catch (error) {
              toast.error('Failed to delete rule');
            }
          }}
        />
      )}

      {isEditing ? (
        <div className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Rule Name
            </label>
            <input
              type="text"
              value={ruleName}
              onChange={(e) => setRuleName(e.target.value)}
              className="w-full p-3 border border-gray-300 rounded-lg"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Rule Text
            </label>
            <textarea
              value={ruleText}
              onChange={(e) => setRuleText(e.target.value)}
              rows={5}
              className="w-full p-3 border border-gray-300 rounded-lg"
              placeholder="Enter your training rules in plain text"
            />
          </div>
          
          <button
            onClick={handleSaveRule}
            className="bg-blue-600 text-white px-6 py-2 rounded-lg"
          >
            Save Rule
          </button>
        </div>
      ) : null}
    </div>
  );
};

export default Rules;
```

<REMOVED>

**Create the missing component:**

```jsx
import React, { useState } from 'react';
import PropTypes from 'prop-types';
import ReactJsonTree from 'react-json-tree';

const RulePreview = ({ naturalLanguageText, parsedRules, onSave, isLoading, onEdit }) => {
  const [ruleName, setRuleName] = useState('');
  const [editedRules, setEditedRules] = useState(parsedRules);
  const [showJsonEditor, setShowJsonEditor] = useState(false);

  const handleSave = () => {
    if (!ruleName.trim()) {
      alert('Please enter a rule name');
      return;
    }
    onSave(ruleName, editedRules);
  };

  const theme = {
    scheme: 'monokai',
    author: 'wimer hazenberg',
    base00: '#272822',
    base01: '#383830',
    base02: '#49483e',
    base03: '#75715e',
    base04: '#a59f85',
    base05: '#f8f8f2',
    base06: '#f5f4f1',
    base07: '#f9f8f5',
    base08: '#f92672',
    base09: '#fd971f',
    base0A: '#f4bf75',
    base0B: '#a6e22e',
    base0C: '#a1efe4',
    base0D: '#66d9ef',
    base0E: '#ae81ff',
    base0F: '#cc6633'
  };

  return (
    <div className="space-y-6">
      {/* Rule Name Input */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Rule Set Name
        </label>
        <input
          type="text"
          value={ruleName}
          onChange={(e) => setRuleName(e.target.value)}
          placeholder="e.g., Winter Training Rules"
          className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
        />
      </div>

      {/* Natural Language Summary */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h3 className="text-lg font-semibold text-blue-800 mb-2">
          Original Input
        </h3>
        <p className="text-blue-700">{naturalLanguageText}</p>
      </div>

      {/* Parsed Rules Display */}
      <div className="bg-white border rounded-lg">
        <div className="flex items-center justify-between p-4 border-b">
          <h3 className="text-lg font-semibold">Parsed Rules</h3>
          <div className="flex space-x-2">
            <button
              onClick={() => setShowJsonEditor(!showJsonEditor)}
              className="px-3 py-1 bg-gray-100 text-gray-700 rounded hover:bg-gray-200"
            >
              {showJsonEditor ? 'View Tree' : 'Edit JSON'}
            </button>
            <button
              onClick={onEdit}
              className="px-3 py-1 bg-blue-100 text-blue-700 rounded hover:bg-blue-200"
            >
              Edit Input
            </button>
          </div>
        </div>

        <div className="p-4">
          {showJsonEditor ? (
            <textarea
              value={JSON.stringify(editedRules, null, 2)}
              onChange={(e) => {
                try {
                  setEditedRules(JSON.parse(e.target.value));
                } catch (err) {
                  // Handle JSON parsing errors
                }
              }}
              className="w-full h-64 p-3 border rounded font-mono text-sm"
            />
          ) : (
            <div className="bg-gray-900 rounded p-4 overflow-auto max-h-64">
              <ReactJsonTree
                data={editedRules}
                theme={theme}
                invertTheme={false}
                shouldExpandNode={() => true}
              />
            </div>
          )}
        </div>
      </div>

      {/* Validation Summary */}
      {parsedRules.confidence && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <span className="text-green-800 font-medium">Parsing Confidence</span>
            <div className="flex items-center">
              <div className="w-32 h-2 bg-green-200 rounded-full mr-3">
                <div 
                  className="h-full bg-green-600 rounded-full"
                  style={{ width: `${parsedRules.confidence * 100}%` }}
                />
              </div>
              <span className="text-green-800 font-mono">
                {(parsedRules.confidence * 100).toFixed(1)}%
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Action Buttons */}
      <div className="flex space-x-4 pt-4 border-t">
        <button
          onClick={handleSave}
          disabled={isLoading || !ruleName.trim()}
          className={`px-6 py-2 rounded-lg font-medium ${
            isLoading || !ruleName.trim()
              ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
              : 'bg-green-600 text-white hover:bg-green-700'
          }`}
        >
          {isLoading ? 'Saving...' : 'Save Rules'}
        </button>
        
        <button
          onClick={onEdit}
          className="px-6 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200"
        >
          Back to Editor
        </button>
      </div>
    </div>
  );
};

RulePreview.propTypes = {
  naturalLanguageText: PropTypes.string.isRequired,
  parsedRules: PropTypes.object.isRequired,
  onSave: PropTypes.func.isRequired,
  isLoading: PropTypes.bool,
  onEdit: PropTypes.func.isRequired
};

export default RulePreview;
```

---

## Step 2.2: Plan Generation Workflow

### **File:** `frontend/src/pages/PlanGeneration.jsx`

**Create the complete plan generation interface:**

```jsx
import React, { useState, useEffect } from 'react';
import { toast } from 'react-toastify';
import { useAuth } from '../context/AuthContext';
import GoalSelector from '../components/plans/GoalSelector';
import PlanParameters from '../components/plans/PlanParameters';
import ProgressTracker from '../components/ui/ProgressTracker';
import PlanTimeline from '../components/plans/PlanTimeline';
import * as planService from '../services/planService';
import * as ruleService from '../services/ruleService';

const PlanGeneration = () => {
  const { apiKey } = useAuth();
  const [currentStep, setCurrentStep] = useState(0);
  const [isGenerating, setIsGenerating] = useState(false);
  const [generatedPlan, setGeneratedPlan] = useState(null);
  
  // Form data
  const [selectedRules, setSelectedRules] = useState([]);
  const [goals, setGoals] = useState({
    primary_goal: '',
    target_weekly_hours: 8,
    fitness_level: 'intermediate',
    event_date: '',
    preferred_routes: [],
    avoid_days: []
  });
  const [parameters, setParameters] = useState({
    duration_weeks: 4,
    user_preferences: {}
  });
  
  const [availableRules, setAvailableRules] = useState([]);

  useEffect(() => {
    loadAvailableRules();
  }, []);

  const loadAvailableRules = async () => {
    try {
      const response = await ruleService.getRules();
      setAvailableRules(response.data);
    } catch (error) {
      console.error('Failed to load rules:', error);
      toast.error('Failed to load available rules');
    }
  };

  const steps = [
    { name: 'Select Rules', component: 'rules' },
    { name: 'Set Goals', component: 'goals' },
    { name: 'Parameters', component: 'parameters' },
    { name: 'Generate', component: 'generate' },
    { name: 'Review', component: 'review' }
  ];

  const handleNext = () => {
    if (currentStep < steps.length - 1) {
      setCurrentStep(currentStep + 1);
    }
  };

  const handlePrev = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleGeneratePlan = async () => {
    setIsGenerating(true);
    try {
      const request = {
        rule_ids: selectedRules.map(rule => rule.id),
        goals: goals,
        duration_weeks: parameters.duration_weeks,
        user_preferences: parameters.user_preferences
      };

      const response = await planService.generatePlan(request);
      setGeneratedPlan(response.data);
      setCurrentStep(4); // Move to review step
      toast.success('Training plan generated successfully!');
    } catch (error) {
      console.error('Failed to generate plan:', error);
      toast.error('Failed to generate training plan');
    } finally {
      setIsGenerating(false);
    }
  };

  const renderStepContent = () => {
    switch (steps[currentStep].component) {
      case 'rules':
        return (
          <RulesSelection
            availableRules={availableRules}
            selectedRules={selectedRules}
            onSelectionChange={setSelectedRules}
          />
        );
      
      case 'goals':
        return (
          <GoalSelector
            goals={goals}
            onChange={setGoals}
          />
        );
      
      case 'parameters':
        return (
          <PlanParameters
            parameters={parameters}
            onChange={setParameters}
          />
        );
      
      case 'generate':
        return (
          <GenerationSummary
            selectedRules={selectedRules}
            goals={goals}
            parameters={parameters}
            onGenerate={handleGeneratePlan}
            isGenerating={isGenerating}
          />
        );
      
      case 'review':
        return generatedPlan ? (
          <PlanTimeline plan={generatedPlan.plan} mode="view" />
        ) : (
          <div>No plan generated</div>
        );
      
      default:
        return <div>Unknown step</div>;
    }
  };

  return (
    <div className="max-w-4xl mx-auto p-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          Generate Training Plan
        </h1>
        <p className="text-gray-600">
          Create a personalized training plan based on your rules and goals
        </p>
      </div>

      {/* Progress Tracker */}
      <ProgressTracker
        steps={steps.map(step => step.name)}
        currentStep={currentStep}
        completedSteps={currentStep}
      />

      {/* Step Content */}
      <div className="bg-white rounded-lg shadow-md p-6 mt-8">
        <h2 className="text-xl font-semibold mb-6">
          {steps[currentStep].name}
        </h2>
        
        {renderStepContent()}
      </div>

      {/* Navigation Buttons */}
      <div className="flex justify-between mt-8">
        <button
          onClick={handlePrev}
          disabled={currentStep === 0}
          className={`px-6 py-2 rounded-lg ${
            currentStep === 0
              ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
              : 'bg-gray-600 text-white hover:bg-gray-700'
          }`}
        >
          Previous
        </button>

        {currentStep < 3 ? (
          <button
            onClick={handleNext}
            disabled={!canProceed()}
            className={`px-6 py-2 rounded-lg ${
              !canProceed()
                ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                : 'bg-blue-600 text-white hover:bg-blue-700'
            }`}
          >
            Next
          </button>
        ) : currentStep === 4 ? (
          <button
            onClick={() => toast.info('Plan saved successfully!')}
            className="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
          >
            Save Plan
          </button>
        ) : null}
      </div>
    </div>
  );

  function canProceed() {
    switch (currentStep) {
      case 0: return selectedRules.length > 0;
      case 1: return goals.primary_goal && goals.target_weekly_hours > 0;
      case 2: return parameters.duration_weeks >= 1;
      default: return true;
    }
  }
};

// Supporting Components

const RulesSelection = ({ availableRules, selectedRules, onSelectionChange }) => {
  const handleRuleToggle = (rule) => {
    const isSelected = selectedRules.some(r => r.id === rule.id);
    if (isSelected) {
      onSelectionChange(selectedRules.filter(r => r.id !== rule.id));
    } else {
      onSelectionChange([...selectedRules, rule]);
    }
  };

  return (
    <div className="space-y-4">
      <p className="text-gray-600 mb-4">
        Select the rule sets that should apply to your training plan:
      </p>
      
      {availableRules.map(rule => (
        <div
          key={rule.id}
          className={`border rounded-lg p-4 cursor-pointer transition-all ${
            selectedRules.some(r => r.id === rule.id)
              ? 'border-blue-500 bg-blue-50'
              : 'border-gray-300 hover:border-gray-400'
          }`}
          onClick={() => handleRuleToggle(rule)}
        >
          <div className="flex items-center justify-between">
            <div>
              <h3 className="font-medium">{rule.name}</h3>
              <p className="text-sm text-gray-600 mt-1">
                {rule.description || 'No description'}
              </p>
            </div>
            <input
              type="checkbox"
              checked={selectedRules.some(r => r.id === rule.id)}
              onChange={() => {}} // Handled by div onClick
              className="w-5 h-5 text-blue-600"
            />
          </div>
        </div>
      ))}
    </div>
  );
};

const GenerationSummary = ({ selectedRules, goals, parameters, onGenerate, isGenerating }) => {
  return (
    <div className="space-y-6">
      <div className="bg-gray-50 rounded-lg p-4">
        <h3 className="font-medium mb-3">Plan Summary</h3>
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <span className="font-medium">Rules Applied:</span>
            <span className="ml-2">{selectedRules.length} rule sets</span>
          </div>
          <div>
            <span className="font-medium">Primary Goal:</span>
            <span className="ml-2">{goals.primary_goal}</span>
          </div>
          <div>
            <span className="font-medium">Weekly Hours:</span>
            <span className="ml-2">{goals.target_weekly_hours}h</span>
          </div>
          <div>
            <span className="font-medium">Duration:</span>
            <span className="ml-2">{parameters.duration_weeks} weeks</span>
          </div>
        </div>
      </div>

      <button
        onClick={onGenerate}
        disabled={isGenerating}
        className={`w-full py-3 rounded-lg font-medium ${
          isGenerating
            ? 'bg-gray-300 text-gray-500'
            : 'bg-blue-600 text-white hover:bg-blue-700'
        }`}
      >
        {isGenerating ? 'Generating Plan...' : 'Generate Training Plan'}
      </button>
    </div>
  );
};

export default PlanGeneration;
```

---

## Step 2.3: Service Layer Implementation

### **File:** `frontend/src/services/planService.js`

**Create the plan service for API communication:**

```javascript
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// Create axios instance with default config
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth interceptor
api.interceptors.request.use((config) => {
  const apiKey = localStorage.getItem('apiKey');
  if (apiKey) {
    config.headers['X-API-Key'] = apiKey;
  }
  return config;
});

// Add error handling interceptor
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('apiKey');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export const generatePlan = async (planRequest) => {
  try {
    const response = await api.post('/plans/generate', planRequest);
    return response;
  } catch (error) {
    console.error('Plan generation failed:', error);
    throw error;
  }
};

export const getPlans = async () => {
  return await api.get('/plans');
};

export const getPlan = async (planId) => {
  return await api.get(`/plans/${planId}`);
};

export const updatePlan = async (planId, planData) => {
  return await api.put(`/plans/${planId}`, planData);
};

export const deletePlan = async (planId) => {
  return await api.delete(`/plans/${planId}`);
};

export const getPlanEvolution = async (planId) => {
  return await api.get(`/workouts/plans/${planId}/evolution`);
};
```

<REMOVED>

**Update the rule service with new endpoints:**

```javascript
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth interceptor
api.interceptors.request.use((config) => {
  const apiKey = localStorage.getItem('apiKey');
  if (apiKey) {
    config.headers['X-API-Key'] = apiKey;
  }
  return config;
});

export const parseRule = async (naturalLanguageText, ruleName) => {
  try {
    const response = await api.post('/rules/parse-natural-language', {
      natural_language_text: naturalLanguageText,
      rule_name: ruleName
    });
    return response;
  } catch (error) {
    console.error('Rule parsing failed:', error);
    throw error;
  }
};

export const validateRules = async (rulesData) => {
  try {
    const response = await api.post('/rules/validate-rules', rulesData);
    return response;
  } catch (error) {
    console.error('Rule validation failed:', error);
    throw error;
  }
};

export const getRules = async () => {
  return await api.get('/rules');
};

export const getRule = async (ruleId) => {
  return await api.get(`/rules/${ruleId}`);
};

export const createRule = async (ruleData) => {
  return await api.post('/rules', ruleData);
};

export const updateRule = async (ruleId, ruleData) => {
  return await api.put(`/rules/${ruleId}`, ruleData);
};

export const deleteRule = async (ruleId) => {
  return await api.delete(`/rules/${ruleId}`);
};
```

---

# Phase 3: Integration & Testing

## Step 3.1: Component Testing

### **File:** `frontend/src/components/rules/__tests__/RuleEditor.test.jsx`

**Add comprehensive component tests:**

```jsx
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import RuleEditor from '../RuleEditor';
import * as ruleService from '../../../services/ruleService';

// Mock the service
jest.mock('../../../services/ruleService');

describe('RuleEditor', () => {
  const mockProps = {
    value: '',
    onChange: jest.fn(),
    onParse: jest.fn()
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders correctly', () => {
    render(<RuleEditor {...mockProps} />);
    
    expect(screen.getByText('Natural Language Editor')).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/Enter your training rules/)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Parse Rules/ })).toBeInTheDocument();
  });

  it('validates input correctly', () => {
    render(<RuleEditor {...mockProps} />);
    
    const textarea = screen.getByPlaceholderText(/Enter your training rules/);
    const parseButton = screen.getByRole('button', { name: /Parse Rules/ });
    
    // Should be disabled for invalid input
    expect(parseButton).toBeDisabled();
    
    // Enter valid training rule
    fireEvent.change(textarea, {
      target: { value: 'Maximum 4 rides per week with at least one rest day between hard workouts' }
    });
    
    // Should be enabled for valid input
    expect(parseButton).toBeEnabled();
  });

  it('calls parse function when button clicked', async () => {
    const mockParseResponse = {
      data: {
        jsonRules: {
          max_rides_per_week: 4,
          min_rest_between_hard: 1
        }
      }
    };
    
    ruleService.parseRule.mockResolvedValue(mockParseResponse);
    
    render(<RuleEditor {...mockProps} />);
    
    const textarea = screen.getByPlaceholderText(/Enter your training rules/);
    const parseButton = screen.getByRole('button', { name: /Parse Rules/ });
    
    fireEvent.change(textarea, {
      target: { value: 'Maximum 4 rides per week with recovery between sessions' }
    });
    
    fireEvent.click(parseButton);
    
    await waitFor(() => {
      expect(mockProps.onParse).toHaveBeenCalledWith(mockParseResponse.data.jsonRules);
    });
  });

  it('shows template suggestions', () => {
    render(<RuleEditor {...mockProps} />);
    
    const templatesButton = screen.getByText('Templates');
    fireEvent.click(templatesButton);
    
    // Should show template suggestions
    expect(screen.getByText(/Maximum 4 rides per week/)).toBeInTheDocument();
  });
});
```

## Step 3.2: Backend API Testing (Updated)

### **File:** `backend/tests/routes/test_plan.py`

**Add updated endpoint tests (removed rule parsing tests):**

```python
import pytest
from httpx import AsyncClient
from app.main import app
from app.models import Plan, Rule
from app.services.ai_service import AIService
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
class TestPlanGeneration:
    
    async def test_generate_plan_success(self, async_client: AsyncClient, db_session, api_headers):
        """Test successful plan generation."""
        # Create test rule
        test_rule = Rule(
            name="Test Rules",
            jsonb_rules={"max_rides_per_week": 4, "min_rest_between_hard": 1},
            version=1
        )
        db_session.add(test_rule)
        await db_session.commit()
        await db_session.refresh(test_rule)
        
        # Mock AI service response
        mock_plan_data = {
            "plan_overview": {
                "duration_weeks": 4,
                "weekly_hours": 8,
                "focus": "endurance"
            },
            "weeks": [
                {
                    "week_number": 1,
                    "focus": "base_building",
                    "workouts": [
                        {
                            "day": "tuesday",
                            "type": "easy_ride",
                            "duration_minutes": 90
                        }
                    ]
                }
            ]
        }
        
        with patch.object(AIService, 'generate_plan', return_value=mock_plan_data):
            response = await async_client.post(
                "/plans/generate",
                json={
                    "rule_ids": [str(test_rule.id)],
                    "goals": {
                        "primary_goal": "endurance",
                        "target_weekly_hours": 8,
                        "fitness_level": "intermediate"
                    },
                    "duration_weeks": 4
                },
                headers=api_headers
            )
        
        assert response.status_code == 200
        data = response.json()
        assert "plan" in data
        assert data["plan"]["jsonb_plan"]["plan_overview"]["focus"] == "endurance"
    
    async def test_generate_plan_missing_rules(self, async_client: AsyncClient, api_headers):
        """Test plan generation with non-existent rules."""
        response = await async_client.post(
            "/plans/generate",
            json={
                "rule_ids": ["non-existent-id"],
                "goals": {
                    "primary_goal": "endurance",
                    "target_weekly_hours": 8,
                    "fitness_level": "intermediate"
                }
            },
            headers=api_headers
        )
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    async def test_generate_plan_invalid_goals(self, async_client: AsyncClient, api_headers):
        """Test plan generation with invalid goals."""
        response = await async_client.post(
            "/plans/generate",
            json={
                "rule_ids": [],
                "goals": {
                    "target_weekly_hours": -1  # Invalid value
                }
            },
            headers=api_headers
        )
        
        assert response.status_code == 422  # Validation error

<REMOVED>
```

---

# Phase 4: Production Polish

## Step 4.1: Error Handling & User Experience

### **File:** `frontend/src/components/GlobalErrorHandler.jsx`

**Create comprehensive error handling:**

```jsx
import React from 'react';
import { toast } from 'react-toastify';

class GlobalErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('Global error caught:', error, errorInfo);
    
    // Log to monitoring service in production
    if (process.env.NODE_ENV === 'production') {
      // logErrorToService(error, errorInfo);
    }
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen flex items-center justify-center bg-gray-50">
          <div className="max-w-md w-full bg-white shadow-lg rounded-lg p-6">
            <div className="text-center">
              <div className="text-red-500 text-6xl mb-4">⚠️</div>
              <h1 className="text-2xl font-bold text-gray-900 mb-2">
                Something went wrong
              </h1>
              <p className="text-gray-600 mb-6">
                An unexpected error occurred. Please try refreshing the page.
              </p>
              <button
                onClick={() => window.location.reload()}
                className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700"
              >
                Refresh Page
              </button>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

// Hook for handling API errors
export const useErrorHandler = () => {
  const handleError = (error) => {
    console.error('API Error:', error);
    
    if (error.response) {
      const status = error.response.status;
      const message = error.response.data?.detail || error.message;
      
      switch (status) {
        case 400:
          toast.error(`Invalid request: ${message}`);
          break;
        case 401:
          toast.error('Authentication failed. Please log in again.');
          localStorage.removeItem('apiKey');
          window.location.href = '/login';
          break;
        case 403:
          toast.error('Access denied. You do not have permission.');
          break;
        case 404:
          toast.error('Resource not found.');
          break;
        case 422:
          toast.error(`Validation error: ${message}`);
          break;
        case 500:
          toast.error('Server error. Please try again later.');
          break;
        case 503:
          toast.error('Service temporarily unavailable.');
          break;
        default:
          toast.error(`Error: ${message}`);
      }
    } else if (error.request) {
      toast.error('Network error. Please check your connection.');
    } else {
      toast.error('An unexpected error occurred.');
    }
  };

  return { handleError };
};

export default GlobalErrorBoundary;
```

## Step 4.2: Performance Optimization

### **File:** `frontend/src/hooks/useDebounce.js`

**Add debouncing for better performance:**

```javascript
import { useState, useEffect } from 'react';

export function useDebounce(value, delay) {
  const [debouncedValue, setDebouncedValue] = useState(value);

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => {
      clearTimeout(handler);
    };
  }, [value, delay]);

  return debouncedValue;
}

// Usage in RuleEditor component
export function useDebouncedValidation(input, validationFn, delay = 500) {
  const debouncedInput = useDebounce(input, delay);
  const [isValidating, setIsValidating] = useState(false);
  const [validationResult, setValidationResult] = useState(null);

  useEffect(() => {
    if (debouncedInput) {
      setIsValidating(true);
      validationFn(debouncedInput)
        .then(result => {
          setValidationResult(result);
          setIsValidating(false);
        })
        .catch(error => {
          console.error('Validation error:', error);
          setIsValidating(false);
        });
    }
  }, [debouncedInput, validationFn]);

  return { isValidating, validationResult };
}
```

---

## 🚀 **Implementation Timeline & Checkpoints**

### **Week 1-2: Backend Foundation**
- [ ] Implement plan generation endpoint
- [ ] Add natural language rule parsing
- [ ] Create comprehensive test suite
- [ ] **Checkpoint:** Can generate plans via API

### **Week 3-4: Frontend Core**
- [ ] Build rules management interface
- [ ] Create plan generation workflow
- [ ] Add error handling and loading states
- [ ] **Checkpoint:** Complete user workflows working

### **Week 5-6: Integration & Testing**
- [ ] Connect frontend to backend APIs
- [ ] Add comprehensive error handling
- [ ] Performance optimization
- [ ] **Checkpoint:** Full feature integration

### **Week 7: Production Polish**
- [ ] UI/UX improvements
- [ ] Performance monitoring
- [ ] Documentation updates
- [ ] **Checkpoint:** Production-ready application

---

## 📝 **Junior Developer Tips**

### **Common Pitfalls to Avoid:**
1. **API Integration**: Always handle loading states and errors
2. **State Management**: Use React hooks properly, avoid stale closures
3. **Async/Await**: Always wrap async operations in try-catch blocks
4. **Type Safety**: Use PropTypes or TypeScript for better debugging
5. **Performance**: Debounce user input for API calls

### **Testing Strategy:**
1. **Start Small**: Test individual components before integration
2. **Mock Services**: Use jest mocks for external API calls
3. **Error Cases**: Test both success and failure scenarios
4. **User Flows**: Test complete user workflows end-to-end

### **Debugging Approach:**
1. **Console Logging**: Add structured logging for API calls
2. **React DevTools**: Use for inspecting component state
3. **Network Tab**: Monitor API requests and responses
4. **Error Boundaries**: Implement proper error catching

This implementation guide provides a clear, step-by-step approach for a junior developer to successfully implement the missing core features while maintaining code quality and following best practices.