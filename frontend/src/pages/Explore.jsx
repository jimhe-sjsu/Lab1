import { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { restaurants } from '../mockData'

const allCuisines = ['All', ...new Set(restaurants.map((restaurant) => restaurant.cuisine))]

function RestaurantCard({ restaurant }) {
  return (
    <Link to={`/restaurants/${restaurant.id}`} className='restaurant-card' aria-label={`Open ${restaurant.name}`}>
      <img src={restaurant.imageUrl} alt={restaurant.name} className='restaurant-card-image' />
      <div className='restaurant-card-body'>
        <div className='restaurant-card-header'>
          <h3>{restaurant.name}</h3>
          <span className='rating-pill'>{restaurant.rating.toFixed(1)}</span>
        </div>
        <p className='muted'>
          {restaurant.cuisine} • {restaurant.city} • {restaurant.priceLevel}
        </p>
        <p>{restaurant.description}</p>
      </div>
    </Link>
  )
}

function Explore() {
  const [search, setSearch] = useState('')
  const [cuisine, setCuisine] = useState('All')
  const [maxPrice, setMaxPrice] = useState('$$$')
  const [minimumRating, setMinimumRating] = useState(0)

  const filteredRestaurants = useMemo(() => {
    return restaurants.filter((restaurant) => {
      const matchesSearch =
        restaurant.name.toLowerCase().includes(search.toLowerCase()) ||
        restaurant.city.toLowerCase().includes(search.toLowerCase())
      const matchesCuisine = cuisine === 'All' || restaurant.cuisine === cuisine
      const matchesPrice = restaurant.priceLevel.length <= maxPrice.length
      const matchesRating = restaurant.rating >= minimumRating
      return matchesSearch && matchesCuisine && matchesPrice && matchesRating
    })
  }, [search, cuisine, maxPrice, minimumRating])

  return (
    <section className='page'>
      <h1>Explore Restaurants</h1>
      <p className='muted'>Search by keyword and filter by cuisine, price, and rating.</p>

      <div className='filter-grid'>
        <label>
          Search
          <input value={search} onChange={(event) => setSearch(event.target.value)} placeholder='Name or city' />
        </label>

        <label>
          Cuisine
          <select value={cuisine} onChange={(event) => setCuisine(event.target.value)}>
            {allCuisines.map((option) => (
              <option key={option} value={option}>
                {option}
              </option>
            ))}
          </select>
        </label>

        <label>
          Max price
          <select value={maxPrice} onChange={(event) => setMaxPrice(event.target.value)}>
            <option value='$'>$</option>
            <option value='$$'>$$</option>
            <option value='$$$'>$$$</option>
          </select>
        </label>

        <label>
          Minimum rating
          <select value={minimumRating} onChange={(event) => setMinimumRating(Number(event.target.value))}>
            <option value={0}>Any</option>
            <option value={3.5}>3.5+</option>
            <option value={4}>4.0+</option>
            <option value={4.5}>4.5+</option>
          </select>
        </label>
      </div>

      <div className='results-header'>
        <strong>{filteredRestaurants.length}</strong> result(s)
      </div>

      <div className='card-grid'>
        {filteredRestaurants.map((restaurant) => (
          <RestaurantCard key={restaurant.id} restaurant={restaurant} />
        ))}
      </div>
    </section>
  )
}

export default Explore
