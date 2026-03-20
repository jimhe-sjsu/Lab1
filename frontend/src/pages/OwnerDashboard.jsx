import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { fetchRestaurantOwnerDashboard } from '../api'

function OwnerDashboard() {
  const { restaurantId } = useParams()
  const [summary, setSummary] = useState(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let mounted = true

    async function load() {
      try {
        setIsLoading(true)
        const data = await fetchRestaurantOwnerDashboard(restaurantId)
        if (mounted) {
          setSummary(data)
        }
      } catch (requestError) {
        if (mounted) {
          setError(requestError?.response?.data?.detail || 'Could not load owner dashboard.')
        }
      } finally {
        if (mounted) {
          setIsLoading(false)
        }
      }
    }

    load()
    return () => {
      mounted = false
    }
  }, [restaurantId])

  if (isLoading) {
    return (
      <section className='page'>
        <p className='muted'>Loading owner analytics...</p>
      </section>
    )
  }

  if (error) {
    return (
      <section className='page'>
        <h1>Owner Dashboard</h1>
        <p className='error-text'>{error}</p>
        <Link to={`/restaurants/${restaurantId}`}>Back to Restaurant</Link>
      </section>
    )
  }

  return (
    <section className='page narrow-page'>
      <h1>Owner Dashboard</h1>
      <p className='muted'>Analytics for your claimed restaurant.</p>

      <div className='form-card'>
        <div className='summary-row'>
          <span className='muted'>Restaurant</span>
          <strong>{summary?.restaurant}</strong>
        </div>
        <div className='summary-row'>
          <span className='muted'>Total reviews</span>
          <strong>{summary?.total_reviews ?? 0}</strong>
        </div>
        <div className='summary-row'>
          <span className='muted'>Average rating</span>
          <strong>{Number(summary?.average_rating ?? 0).toFixed(2)}</strong>
        </div>
        <div className='summary-row'>
          <span className='muted'>Favorite count</span>
          <strong>{summary?.favorite_count ?? 0}</strong>
        </div>
      </div>

      <Link to={`/restaurants/${restaurantId}`} className='btn btn-secondary'>
        Back to Restaurant
      </Link>
    </section>
  )
}

export default OwnerDashboard
