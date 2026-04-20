import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { createReview, fetchRestaurantDetails, uploadImage } from '../api'

function WriteReview() {
  const { restaurantId } = useParams()
  const navigate = useNavigate()
  const [restaurant, setRestaurant] = useState(null)
  const [form, setForm] = useState({ rating: 5, comment: '', photoUrl: '' })
  const [reviewPhotoFile, setReviewPhotoFile] = useState(null)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    let isMounted = true

    async function loadRestaurant() {
      try {
        const data = await fetchRestaurantDetails(restaurantId)
        if (isMounted) {
          setRestaurant(data.restaurant)
        }
      } catch (requestError) {
        if (isMounted) {
          setError(requestError?.response?.data?.detail || 'Could not load restaurant.')
        }
      }
    }

    loadRestaurant()
    return () => {
      isMounted = false
    }
  }, [restaurantId])

  if (error && !restaurant) {
    return (
      <section className='page'>
        <h1>Restaurant not found</h1>
        <p className='error-text'>{error}</p>
        <p>
          Visit <Link to='/explore'>Explore</Link>.
        </p>
      </section>
    )
  }

  if (!restaurant) {
    return (
      <section className='page'>
        <p className='muted'>Loading restaurant...</p>
      </section>
    )
  }

  const handleSubmit = async (event) => {
    event.preventDefault()
    setError('')
    setIsSubmitting(true)

    try {
      let uploadedPhotoUrl = form.photoUrl.trim() || null
      if (reviewPhotoFile) {
        const upload = await uploadImage(reviewPhotoFile)
        uploadedPhotoUrl = upload.url
      }

      await createReview({
        restaurant_id: Number(restaurantId),
        rating: form.rating,
        comment: form.comment,
        photo_url: uploadedPhotoUrl,
      })
      navigate(`/restaurants/${restaurantId}`)
    } catch (requestError) {
      setError(requestError?.response?.data?.detail || 'Could not submit review.')
    } finally {
      setIsSubmitting(false)
    }
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
        <textarea id='comment' rows={5} required value={form.comment} onChange={(event) => setForm((prev) => ({ ...prev, comment: event.target.value }))} />

        <label htmlFor='photoUrl'>Photo URL (optional)</label>
        <input id='photoUrl' type='url' placeholder='https://...' value={form.photoUrl} onChange={(event) => setForm((prev) => ({ ...prev, photoUrl: event.target.value }))} />

        <label htmlFor='reviewPhotoFile'>Upload review photo</label>
        <input id='reviewPhotoFile' type='file' accept='image/*' onChange={(event) => setReviewPhotoFile(event.target.files?.[0] || null)} />

        {error && <p className='error-text'>{error}</p>}

        <button className='btn btn-primary' type='submit' disabled={isSubmitting}>
          {isSubmitting ? 'Submitting...' : 'Submit Review'}
        </button>
      </form>
    </section>
  )
}

export default WriteReview
