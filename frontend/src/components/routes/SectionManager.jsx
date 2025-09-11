import { useState, useEffect } from 'react'
import { Button, Input, Select } from '../ui'
import { FaPlus, FaTrash } from 'react-icons/fa'

const SectionManager = ({ route, onSectionsUpdate }) => {
  const [sections, setSections] = useState(route.sections || [])
  const [newSection, setNewSection] = useState({
    name: '',
    start: 0,
    end: 0,
    difficulty: 3,
    recommended_gear: 'road'
  })

  useEffect(() => {
    onSectionsUpdate(sections)
  }, [sections, onSectionsUpdate])

  const addSection = () => {
    if (newSection.name && newSection.start < newSection.end) {
      setSections([...sections, {
        ...newSection,
        id: Date.now().toString(),
        distance: newSection.end - newSection.start
      }])
      setNewSection({
        name: '',
        start: 0,
        end: 0,
        difficulty: 3,
        recommended_gear: 'road'
      })
    }
  }

  const removeSection = (sectionId) => {
    setSections(sections.filter(s => s.id !== sectionId))
  }

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4 items-end">
        <Input
          label="Section Name"
          value={newSection.name}
          onChange={(e) => setNewSection({...newSection, name: e.target.value})}
        />
        <Input
          type="number"
          label="Start (km)"
          value={newSection.start}
          onChange={(e) => setNewSection({...newSection, start: +e.target.value})}
        />
        <Input
          type="number"
          label="End (km)"
          value={newSection.end}
          onChange={(e) => setNewSection({...newSection, end: +e.target.value})}
        />
        <Select
          label="Difficulty"
          value={newSection.difficulty}
          options={[1,2,3,4,5].map(n => ({value: n, label: `${n}/5`}))}
          onChange={(e) => setNewSection({...newSection, difficulty: +e.target.value})}
        />
        <Select
          label="Gear"
          value={newSection.recommended_gear}
          options={[
            {value: 'road', label: 'Road Bike'},
            {value: 'gravel', label: 'Gravel Bike'},
            {value: 'tt', label: 'Time Trial'},
            {value: 'climbing', label: 'Climbing Bike'}
          ]}
          onChange={(e) => setNewSection({...newSection, recommended_gear: e.target.value})}
        />
        <Button onClick={addSection} className="h-[42px]">
          <FaPlus className="mr-2" /> Add Section
        </Button>
      </div>

      <div className="space-y-4">
        {sections.map(section => (
          <div key={section.id} className="flex items-center gap-4 p-4 bg-gray-50 rounded-lg">
            <div className="flex-1 grid grid-cols-4 gap-4">
              <p className="font-medium">{section.name}</p>
              <p>{section.start}km - {section.end}km</p>
              <p>Difficulty: {section.difficulty}/5</p>
              <p className="capitalize">{section.recommended_gear.replace('_', ' ')}</p>
            </div>
            <button 
              onClick={() => removeSection(section.id)}
              className="text-red-600 hover:text-red-700 p-2"
            >
              <FaTrash />
            </button>
          </div>
        ))}
      </div>
    </div>
  )
}

export default SectionManager