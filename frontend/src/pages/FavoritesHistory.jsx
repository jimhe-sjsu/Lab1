import { useEffect, useState } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { Link } from 'react-router-dom'
import { fetchUserHistory } from '../api'
import {
  fetchFavoritesThunk,
  selectFavouriteItems,
  selectFavouritesError,
  selectFavouritesStatus,
} from '../store/slices/favouritesSlice'

function FavoritesHistory() {
  const dispatch = useDispatch()
  const [activeTab, setActiveTab] = useState('favorites')
  const [history, setHistory] = useState({ reviews_written: [], restaurants_added: [] })
  const [historyLoading, setHistoryLoading] = useState(true)
  const favorites = useSelector(selectFavouriteItems)
  const favoritesStatus = useSelector(selectFavouritesStatus)
  const favoritesError = useSelector(selectFavouritesError)
  const isLoading = favoritesStatus === 'loading' || historyLoading
  const error = favoritesError

  useEffect(() => {
    let isMounted = true

    async function loadActivity() {
      try {
        setHistoryLoading(true)
        const [historyData] = await Promise.all([dispatch(fetchFavoritesThunk()).unwrap(), fetchUserHistory()])

        if (isMounted) {
          setHistory(historyData)
        }
      } catch (requestError) {
        if (isMounted) {
          console.error(requestError)
        }
      } finally {
        if (isMounted) {
          setHistoryLoading(false)
        }
      }
    }

    loadActivity()
    return () => {
      isMounted = false
    }
  }, [dispatch])

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
