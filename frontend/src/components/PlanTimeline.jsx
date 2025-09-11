import { useEffect, useState } from 'react'
import Link from 'next/link'

const PlanTimeline = ({ planId }) => {
  const [planData, setPlanData] = useState(null)
  const [versionHistory, setVersionHistory] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    const fetchPlanData = async () => {
      try {
        const [planRes, historyRes] = await Promise.all([
          fetch(`/api/plans/${planId}`),
          fetch(`/api/plans/${planId}/evolution`)
        ])
        
        if (!planRes.ok || !historyRes.ok) {
          throw new Error('Failed to load plan data')
        }
        
        const plan = await planRes.json()
        const history = await historyRes.json()
        
        setPlanData(plan)
        setVersionHistory(history.evolution_history || [])
        setError(null)
      } catch (err) {
        console.error('Plan load error:', err)
        setError(err.message)
      } finally {
        setLoading(false)
      }
    }

    fetchPlanData()
  }, [planId])

  if (loading) {
    return (
      <div className="p-4 space-y-4">
        <div className="animate-pulse space-y-4">
          <div className="h-6 bg-gray-200 rounded w-1/4"></div>
          <div className="h-4 bg-gray-200 rounded w-1/2"></div>
          <div className="space-y-2">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="h-12 bg-gray-100 rounded-lg"></div>
            ))}
          </div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-4 text-red-600">
        Error loading plan: {error}
      </div>
    )
  }

  return (
    <div className="plan-timeline p-4 bg-white rounded-lg shadow">
      {/* Current Plan Header */}
      <div className="mb-6">
        <h2 className="text-2xl font-semibold">{planData.jsonb_plan.overview.focus} Training Plan</h2>
        <p className="text-gray-600">
          {planData.jsonb_plan.overview.duration_weeks} weeks •{' '}
          {planData.jsonb_plan.overview.total_weekly_hours} hours/week
        </p>
      </div>

      {/* Week Timeline */}
      <div className="space-y-8">
        {planData.jsonb_plan.weeks.map((week, index) => (
          <div key={index} className="relative pl-6 border-l-2 border-gray-200">
            <div className="absolute w-4 h-4 bg-blue-500 rounded-full -left-[9px] top-0"></div>
            <div className="mb-2">
              <h3 className="text-lg font-semibold">Week {week.week_number}</h3>
              <p className="text-gray-600">{week.focus}</p>
            </div>
            <div className="space-y-4">
              {week.workouts.map((workout, wIndex) => (
                <div key={wIndex} className="p-4 bg-gray-50 rounded-lg">
                  <div className="flex justify-between items-start">
                    <div>
                      <h4 className="font-medium">{workout.type.replace(/_/g, ' ')}</h4>
                      <p className="text-sm text-gray-600">{workout.description}</p>
                    </div>
                    <div className="text-right">
                      <p className="text-gray-900">{workout.duration_minutes} minutes</p>
                      <p className="text-sm text-gray-500 capitalize">{workout.intensity}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>

      {/* Version History */}
      {versionHistory.length > 0 && (
        <div className="mt-8 pt-6 border-t border-gray-200">
          <h3 className="text-lg font-semibold mb-4">Version History</h3>
          <div className="space-y-4">
            {versionHistory.map((version, index) => (
              <div key={index} className="p-4 bg-gray-50 rounded-lg">
                <div className="flex justify-between items-start">
                  <div>
                    <h4 className="font-medium">Version {version.version}</h4>
                    <p className="text-sm text-gray-600">
                      {new Date(version.created_at).toLocaleDateString()}
                    </p>
                    {version.changes_summary && (
                      <p className="text-sm mt-2 text-gray-600">
                        {version.changes_summary}
                      </p>
                    )}
                  </div>
                  <Link
                    href={`/plans/${version.parent_plan_id}`}
                    className="text-blue-500 hover:text-blue-700 text-sm"
                  >
                    View →
                  </Link>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

export default PlanTimeline