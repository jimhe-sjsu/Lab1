import { Link, useParams } from 'react-router-dom'
import { findRestaurantById } from '../mockData'

function RestaurantDetails() {
  const { restaurantId } = useParams()
  const restaurant = findRestaurantById(restaurantId)

  if (!restaurant) {
    return (
      <section className='page'>
        <h1>Restaurant not found</h1>
        <p>
          Go back to <Link to='/explore'>Explore</Link>.
        </p>
      </section>
    )
  }

  return (
    <section className='page'>
      <div className='detail-hero'>
        <img src={restaurant.imageUrl} alt={restaurant.name} className='detail-image' />
        <div>
          <h1>{restaurant.name}</h1>
          <p className='muted'>
            {restaurant.cuisine} • {restaurant.city} • {restaurant.priceLevel} • {restaurant.rating.toFixed(1)}
          </p>
          <p>{restaurant.description}</p>
          <div className='hero-actions'>
            <Link to={`/restaurants/${restaurant.id}/review`} className='btn btn-primary'>
              Write Review
            </Link>
          </div>
        </div>
      </div>

      <section>
        <h2>Reviews</h2>
        <div className='review-list'>
          {restaurant.reviews.map((review) => (
            <article key={review.id} className='review-card'>
              <header>
                <strong>{review.author}</strong>
                <span className='rating-pill'>{review.rating.toFixed(1)}</span>
              </header>
              <p>{review.comment}</p>
            </article>
          ))}
        </div>
      </section>
    </section>
  )
}

export default RestaurantDetails
