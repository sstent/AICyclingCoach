import { useState } from 'react';
import PropTypes from 'prop-types';

const SectionList = ({ sections, onSplit, onUpdate }) => {
  const [editing, setEditing] = useState(null);
  const [localSections, setLocalSections] = useState(sections);

  const surfaceTypes = ['road', 'gravel', 'mixed', 'trail'];
  const gearOptions = {
    road: ['Standard (39x25)', 'Mid-compact (36x30)', 'Compact (34x28)'],
    gravel: ['1x System', '2x Gravel', 'Adventure'],
    trail: ['MTB Wide-range', 'Fat Bike']
  };

  const handleEdit = (sectionId) => {
    setEditing(sectionId);
    setLocalSections(sections);
  };

  const handleSave = () => {
    onUpdate(localSections);
    setEditing(null);
  };

  const handleChange = (sectionId, field, value) => {
    setLocalSections(prev => prev.map(section => 
      section.id === sectionId ? { ...section, [field]: value } : section
    ));
  };

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold">Route Sections</h3>
        <div className="space-x-2">
          <button
            onClick={() => onSplit([Math.floor(sections.length/2)])}
            className="bg-green-600 text-white px-3 py-1 rounded-md hover:bg-green-700"
          >
            Split Route
          </button>
          {editing && (
            <button
              onClick={handleSave}
              className="bg-blue-600 text-white px-3 py-1 rounded-md hover:bg-blue-700"
            >
              Save All
            </button>
          )}
        </div>
      </div>

      {localSections.map((section) => (
        <div key={section.id} className="bg-white p-4 rounded-lg shadow-md">
          <div className="flex justify-between items-start mb-2">
            <h4 className="font-medium">Section {section.id}</h4>
            <button
              onClick={() => editing === section.id ? handleSave() : handleEdit(section.id)}
              className={`text-sm ${editing === section.id ? 'text-blue-600' : 'text-gray-600 hover:text-gray-800'}`}
            >
              {editing === section.id ? 'Save' : 'Edit'}
            </button>
          </div>

          <div className="grid grid-cols-2 gap-2 text-sm">
            <div className="space-y-1">
              <p>Distance: {section.distance} km</p>
              <p>Elevation: {section.elevationGain} m</p>
            </div>
            <div className="space-y-1">
              <p>Max Grade: {section.maxGrade}%</p>
              <p>Surface: 
                {editing === section.id ? (
                  <select
                    value={section.surfaceType}
                    onChange={(e) => handleChange(section.id, 'surfaceType', e.target.value)}
                    className="ml-2 p-1 border rounded"
                  >
                    {surfaceTypes.map(type => (
                      <option key={type} value={type}>{type.charAt(0).toUpperCase() + type.slice(1)}</option>
                    ))}
                  </select>
                ) : (
                  <span className="ml-2 capitalize">{section.surfaceType}</span>
                )}
              </p>
            </div>
          </div>

          {editing === section.id && (
            <div className="mt-3 pt-2 border-t">
              <label className="block text-sm font-medium mb-1">Gear Recommendation</label>
              <select
                value={section.gearRecommendation}
                onChange={(e) => handleChange(section.id, 'gearRecommendation', e.target.value)}
                className="w-full p-1 border rounded"
              >
                {gearOptions[section.surfaceType]?.map(gear => (
                  <option key={gear} value={gear}>{gear}</option>
                ))}
              </select>
            </div>
          )}
        </div>
      ))}
    </div>
  );
};

SectionList.propTypes = {
  sections: PropTypes.arrayOf(PropTypes.object).isRequired,
  onSplit: PropTypes.func.isRequired,
  onUpdate: PropTypes.func.isRequired
};

export default SectionList;