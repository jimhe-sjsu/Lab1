import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { fetchFavorites, fetchUserHistory } from '../api'

function FavoritesHistory() {
  const [activeTab, setActiveTab] = useState('favorites')
  const [favorites, setFavorites] = useState([])
  const [history, setHistory] = useState({ reviews_written: [], restaurants_added: [] })
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let isMounted = true

    async function loadActivity() {
      try {
        setIsLoading(true)
        const [favoriteRestaurants, historyData] = await Promise.all([fetchFavorites(), fetchUserHistory()])

        if (isMounted) {
          setFavorites(favoriteRestaurants)
          setHistory(historyData)
        }
      } catch (requestError) {
        if (isMounted) {
          setError(requestError?.response?.data?.detail || 'Could not load activity.')
        }
      } finally {
        if (isMounted) {
          setIsLoading(false)
        }
      }
    }

    loadActivity()
    return () => {
      isMounted = false
    }
  }, [])

  return (
    <section className='page'>
      <h1>My Activity</h1>
      <p className='muted'>Track your favorites, submitted reviews, and added restaurants.</p>

      <div className='tab-row'>
        <button type='button' className={activeTab === 'favorites' ? 'tab active-tab' : 'tab'} onClick={() => setActiveTab('favorites')}>
          Favorites
        </button>
        <button type='button' className={activeTab === 'history' ? 'tab active-tab' : 'tab'} onClick={() => setActiveTab('history')}>
          History
        </button>
      </div>

      {isLoading && <p className='muted'>Loading activity...</p>}
      {error && <p className='error-text'>{error}</p>}

      {!isLoading && activeTab === 'favorites' ? (
        <div className='list-stack'>
          {favorites.map((restaurant) => (
            <Link className='list-item' key={restaurant.id} to={`/restaurants/${restaurant.id}`}>
              <strong>{restaurant.name}</strong>
              <span className='muted'>
                {restaurant.cuisine} • {restaurant.city}
              </span>
            </Link>
          ))}
          {favorites.length === 0 && <p className='muted'>No favorites yet.</p>}
        </div>
      ) : !isLoading ? (
        <div className='history-grid'>
          <section className='form-card'>
            <h2>Reviews Written</h2>
            <div className='list-stack'>
              {history.reviews_written?.map((review) => (
                <Link className='list-item' key={review.review_id} to={`/restaurants/${review.restaurant_id}`}>
                  <strong>{review.restaurant_name}</strong>
                  <span className='muted'>
                    Rating: {review.rating} • {new Date(review.created_at).toLocaleDateString()}
                  </span>
                </Link>
              ))}
              {history.reviews_written?.length === 0 && <p className='muted'>No reviews written yet.</p>}
            </div>
          </section>

          <section className='form-card'>
            <h2>Restaurants Added</h2>
            <div className='list-stack'>
              {history.restaurants_added?.map((restaurant) => (
                <Link className='list-item' key={restaurant.restaurant_id} to={`/restaurants/${restaurant.restaurant_id}`}>
                  <strong>{restaurant.name}</strong>
                  <span className='muted'>
                    {restaurant.cuisine_type} • {restaurant.city}
                  </span>
                </Link>
              ))}
              {history.restaurants_added?.length === 0 && <p className='muted'>No restaurants added yet.</p>}
            </div>
          </section>
        </div>
      ) : null}
    </section>
  )
}

export default FavoritesHistory
