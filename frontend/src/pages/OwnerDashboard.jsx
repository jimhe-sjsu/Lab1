import { useEffect, useMemo, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { fetchRestaurantOwnerDashboard, fetchReviewsForRestaurant } from '../api'

function OwnerDashboard() {
  const { restaurantId } = useParams()
  const [summary, setSummary] = useState(null)
  const [reviews, setReviews] = useState([])
  const [ratingFilter, setRatingFilter] = useState('all')
  const [sortBy, setSortBy] = useState('newest')
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let mounted = true

    async function load() {
      try {
        setIsLoading(true)
        setError('')
        const [dashboardData, reviewData] = await Promise.all([
          fetchRestaurantOwnerDashboard(restaurantId),
          fetchReviewsForRestaurant(restaurantId),
        ])

        if (mounted) {
          setSummary(dashboardData)
          setReviews(reviewData)
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

  const ratingDistribution = summary?.rating_distribution || {}

  const filteredReviews = useMemo(() => {
    let nextReviews = [...reviews]

    if (ratingFilter !== 'all') {
      nextReviews = nextReviews.filter((review) => Number(review.rating) === Number(ratingFilter))
    }

    if (sortBy === 'highest') {
      nextReviews.sort((a, b) => b.rating - a.rating || new Date(b.createdAt) - new Date(a.createdAt))
    } else if (sortBy === 'lowest') {
      nextReviews.sort((a, b) => a.rating - b.rating || new Date(b.createdAt) - new Date(a.createdAt))
    } else if (sortBy === 'oldest') {
      nextReviews.sort((a, b) => new Date(a.createdAt) - new Date(b.createdAt))
    } else {
      nextReviews.sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt))
    }

    return nextReviews
  }, [ratingFilter, reviews, sortBy])

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
    <section className='page'>
      <h1>Owner Dashboard</h1>
      <p className='muted'>Analytics, sentiment, and read-only review management for your restaurant.</p>

      <div className='three-column-grid'>
        <section className='form-card'>
          <span className='muted'>Restaurant</span>
          <strong>{summary?.restaurant}</strong>
        </section>

        <section className='form-card'>
          <span className='muted'>Total reviews</span>
          <strong>{summary?.total_reviews ?? 0}</strong>
        </section>

        <section className='form-card'>
          <span className='muted'>Average rating</span>
          <strong>{Number(summary?.average_rating ?? 0).toFixed(2)}</strong>
        </section>

        <section className='form-card'>
          <span className='muted'>Favorite count</span>
          <strong>{summary?.favorite_count ?? 0}</strong>
        </section>

        <section className='form-card'>
          <span className='muted'>Total views</span>
          <strong>{summary?.total_views ?? 0}</strong>
        </section>

        <section className='form-card'>
          <span className='muted'>Public sentiment</span>
          <strong>
            +{summary?.sentiment_summary?.positive ?? 0} / {summary?.sentiment_summary?.neutral ?? 0} / -
            {summary?.sentiment_summary?.negative ?? 0}
          </strong>
        </section>
      </div>

      <div className='profile-layout'>
        <section className='form-card'>
          <h2>Rating Distribution</h2>
          <div className='list-stack'>
            {[5, 4, 3, 2, 1].map((star) => (
              <div key={star} className='summary-row'>
                <span>{star} star</span>
                <strong>{ratingDistribution[String(star)] ?? 0}</strong>
              </div>
            ))}
          </div>
        </section>

        <aside className='profile-sidebar'>
          <section className='form-card'>
            <h2>Recent Reviews</h2>
            <div className='list-stack'>
              {(summary?.recent_reviews || []).map((review) => (
                <div key={review.id} className='list-item'>
                  <strong>
                    {review.reviewer_name} • {review.rating}/5
                  </strong>
                  <span className='muted'>{new Date(review.created_at).toLocaleString()}</span>
                  <span>{review.comment || 'No comment provided.'}</span>
                </div>
              ))}
              {summary?.recent_reviews?.length === 0 && <p className='muted'>No recent reviews yet.</p>}
            </div>
          </section>
        </aside>
      </div>

      <section className='form-card'>
        <div className='section-title-row'>
          <div>
            <h2>All Reviews</h2>
            <p className='muted'>Read-only review dashboard with filtering and sorting.</p>
          </div>
          <div className='split-grid'>
            <label htmlFor='ratingFilter'>
              Filter by rating
              <select id='ratingFilter' value={ratingFilter} onChange={(event) => setRatingFilter(event.target.value)}>
                <option value='all'>All</option>
                <option value='5'>5 stars</option>
                <option value='4'>4 stars</option>
                <option value='3'>3 stars</option>
                <option value='2'>2 stars</option>
                <option value='1'>1 star</option>
              </select>
            </label>

            <label htmlFor='sortBy'>
              Sort reviews
              <select id='sortBy' value={sortBy} onChange={(event) => setSortBy(event.target.value)}>
                <option value='newest'>Newest first</option>
                <option value='oldest'>Oldest first</option>
                <option value='highest'>Highest rating</option>
                <option value='lowest'>Lowest rating</option>
              </select>
            </label>
          </div>
        </div>

        <div className='review-list'>
          {filteredReviews.map((review) => (
            <article key={review.id} className='review-card'>
              <header>
                <strong>{review.author}</strong>
                <span className='rating-pill'>{Number(review.rating).toFixed(1)}</span>
              </header>

              <p className='muted'>{review.createdAt ? new Date(review.createdAt).toLocaleString() : ''}</p>
              <p>{review.comment || 'No comment provided.'}</p>
              {review.photoUrl ? <img className='review-photo' src={review.photoUrl} alt='Review upload' /> : null}
            </article>
          ))}
          {filteredReviews.length === 0 && <p className='muted'>No reviews match the current filter.</p>}
        </div>
      </section>

      <Link to={`/restaurants/${restaurantId}`} className='btn btn-secondary'>
        Back to Restaurant
      </Link>
    </section>
  )
}

export default OwnerDashboard
