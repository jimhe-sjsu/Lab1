import { useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { findRestaurantById } from '../mockData'

function WriteReview() {
  const { restaurantId } = useParams()
  const restaurant = findRestaurantById(restaurantId)
  const [submitted, setSubmitted] = useState(false)
  const [form, setForm] = useState({ rating: 5, comment: '' })

  if (!restaurant) {
    return (
      <section className='page'>
        <h1>Restaurant not found</h1>
        <p>
          Visit <Link to='/explore'>Explore</Link>.
        </p>
      </section>
    )
  }

  const handleSubmit = (event) => {
    event.preventDefault()
    setSubmitted(true)
  }

  return (
    <section className='page narrow-page'>
      <h1>Write Review</h1>
      <p className='muted'>
        Sharing review for <strong>{restaurant.name}</strong>
      </p>

      <form className='form-card' onSubmit={handleSubmit}>
        <label htmlFor='rating'>Rating</label>
        <select id='rating' value={form.rating} onChange={(event) => setForm((prev) => ({ ...prev, rating: Number(event.target.value) }))}>
          <option value={5}>5 - Excellent</option>
          <option value={4}>4 - Good</option>
          <option value={3}>3 - Average</option>
          <option value={2}>2 - Fair</option>
          <option value={1}>1 - Poor</option>
        </select>

        <label htmlFor='comment'>Comment</label>
        <textarea
          id='comment'
          rows={5}
          required
          value={form.comment}
          onChange={(event) => setForm((prev) => ({ ...prev, comment: event.target.value }))}
        />

        {submitted && <p className='success-text'>Review submitted (frontend demo).</p>}

        <button className='btn btn-primary' type='submit'>
          Submit Review
        </button>
      </form>
    </section>
  )
}

export default WriteReview
