import { useEffect, useMemo, useState } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { Link, useSearchParams } from 'react-router-dom'
import {
  searchRestaurantsThunk,
  selectRestaurantList,
  selectRestaurantsError,
  selectRestaurantsStatus,
} from '../store/slices/restaurantsSlice'

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

function buildFiltersFromSearchParams(searchParams) {
  return {
    name: searchParams.get('name') || '',
    cuisine: searchParams.get('cuisine') || 'All',
    city: searchParams.get('city') || '',
    zipCode: searchParams.get('zip_code') || '',
    keyword: searchParams.get('keyword') || '',
    priceTier: searchParams.get('price_tier') || 'Any',
  }
}

function ExploreContent({ initialFilters }) {
  const dispatch = useDispatch()
  const [filters, setFilters] = useState(initialFilters)
  const [minimumRating, setMinimumRating] = useState(0)
  const restaurants = useSelector(selectRestaurantList)
  const restaurantsStatus = useSelector(selectRestaurantsStatus)
  const error = useSelector(selectRestaurantsError)
  const isLoading = restaurantsStatus === 'loading'

  useEffect(() => {
    dispatch(searchRestaurantsThunk(filters))
  }, [dispatch, filters])

  const allCuisines = useMemo(() => {
    return ['All', ...new Set(restaurants.map((restaurant) => restaurant.cuisine).filter(Boolean))]
  }, [restaurants])

  const filteredRestaurants = useMemo(() => {
    return restaurants.filter((restaurant) => restaurant.rating >= minimumRating)
  }, [restaurants, minimumRating])

  return (
    <section className='page'>
      <h1>Explore Restaurants</h1>
      <p className='muted'>Search by name, cuisine, location, and keywords.</p>

      <div className='filter-grid'>
        <label>
          Restaurant name
          <input value={filters.name} onChange={(event) => setFilters((prev) => ({ ...prev, name: event.target.value }))} />
        </label>

        <label>
          Cuisine
          <select value={filters.cuisine} onChange={(event) => setFilters((prev) => ({ ...prev, cuisine: event.target.value }))}>
            {allCuisines.map((option) => (
              <option key={option} value={option}>
                {option}
              </option>
            ))}
          </select>
        </label>

        <label>
          City
          <input value={filters.city} onChange={(event) => setFilters((prev) => ({ ...prev, city: event.target.value }))} />
        </label>

        <label>
          ZIP code
          <input value={filters.zipCode} onChange={(event) => setFilters((prev) => ({ ...prev, zipCode: event.target.value }))} />
        </label>

        <label>
          Keyword
          <input
            value={filters.keyword}
            onChange={(event) => setFilters((prev) => ({ ...prev, keyword: event.target.value }))}
            placeholder='quiet, wifi, outdoor'
          />
        </label>

        <label>
          Price tier
          <select value={filters.priceTier} onChange={(event) => setFilters((prev) => ({ ...prev, priceTier: event.target.value }))}>
            <option value='Any'>Any</option>
            <option value='$'>$</option>
            <option value='$$'>$$</option>
            <option value='$$$'>$$$</option>
            <option value='$$$$'>$$$$</option>
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

      {isLoading && <p className='muted'>Loading restaurants...</p>}
      {error && <p className='error-text'>{error}</p>}

      <div className='card-grid'>
        {!isLoading && !error && filteredRestaurants.map((restaurant) => <RestaurantCard key={restaurant.id} restaurant={restaurant} />)}
      </div>
    </section>
  )
}

function Explore() {
  const [searchParams] = useSearchParams()
  const searchKey = searchParams.toString()
  const initialFilters = useMemo(() => buildFiltersFromSearchParams(new URLSearchParams(searchKey)), [searchKey])

  return <ExploreContent key={searchKey} initialFilters={initialFilters} />
}

export default Explore
