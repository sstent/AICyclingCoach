import { useRouter } from 'next/router'
import PlanTimeline from '../src/components/PlanTimeline'

const PlanDetails = () => {
  const router = useRouter()
  const { planId } = router.query

  // If the planId is not available yet (still loading), show a loading state
  if (!planId) {
    return (
      <div className="min-h-screen bg-gray-50 p-4 md:p-6">
        <div className="max-w-4xl mx-auto">
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
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 p-4 md:p-6">
      <div className="max-w-4xl mx-auto">
        <PlanTimeline planId={planId} />
      </div>
    </div>
  )
}

export default PlanDetails