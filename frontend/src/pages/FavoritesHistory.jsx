import { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { favoriteRestaurantIds, recentlyViewed, restaurants } from '../mockData'

function FavoritesHistory() {
  const [activeTab, setActiveTab] = useState('favorites')

  const favorites = useMemo(() => restaurants.filter((restaurant) => favoriteRestaurantIds.includes(restaurant.id)), [])

  const history = useMemo(
    () =>
      recentlyViewed.map((entry) => ({
        ...entry,
        restaurant: restaurants.find((restaurant) => restaurant.id === entry.id),
      })),
    []
  )

  return (
    <section className='page'>
      <h1>My Activity</h1>
      <p className='muted'>Track your favorite spots and recently viewed restaurants.</p>

      <div className='tab-row'>
        <button type='button' className={activeTab === 'favorites' ? 'tab active-tab' : 'tab'} onClick={() => setActiveTab('favorites')}>
          Favorites
        </button>
        <button type='button' className={activeTab === 'history' ? 'tab active-tab' : 'tab'} onClick={() => setActiveTab('history')}>
          History
        </button>
      </div>

      {activeTab === 'favorites' ? (
        <div className='list-stack'>
          {favorites.map((restaurant) => (
            <Link className='list-item' key={restaurant.id} to={`/restaurants/${restaurant.id}`}>
              <strong>{restaurant.name}</strong>
              <span className='muted'>
                {restaurant.cuisine} • {restaurant.city}
              </span>
            </Link>
          ))}
        </div>
      ) : (
        <div className='list-stack'>
          {history.map((entry) => (
            <Link className='list-item' key={`${entry.id}-${entry.viewedAt}`} to={`/restaurants/${entry.id}`}>
              <strong>{entry.restaurant?.name || 'Unknown restaurant'}</strong>
              <span className='muted'>{new Date(entry.viewedAt).toLocaleString()}</span>
            </Link>
          ))}
        </div>
      )}
    </section>
  )
}

export default FavoritesHistory
