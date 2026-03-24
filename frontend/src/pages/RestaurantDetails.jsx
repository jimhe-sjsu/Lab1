import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import {
  addFavorite,
  claimRestaurant,
  createReview,
  deleteReview,
  fetchFavorites,
  fetchRestaurantDetails,
  removeFavorite,
  updateRestaurant,
  updateReview,
  uploadImage,
} from '../api'
import { useAuth } from '../auth'

function buildRestaurantEditData(restaurant) {
  return {
    name: restaurant?.name || '',
    cuisine: restaurant?.cuisine || '',
    address: restaurant?.address || '',
    city: restaurant?.city || '',
    state: restaurant?.state || '',
    zipCode: restaurant?.zipCode || '',
    description: restaurant?.description || '',
    contactPhone: restaurant?.contactPhone || '',
    hoursText: restaurant?.hoursText || '',
    amenitiesText: restaurant?.amenitiesText || '',
    photoUrl: restaurant?.photoUrl || '',
    priceLevel: restaurant?.priceLevel || '$$',
  }
}

function RestaurantDetails() {
  const { restaurantId } = useParams()
  const navigate = useNavigate()
  const { isAuthenticated, user } = useAuth()

  const [restaurant, setRestaurant] = useState(null)
  const [reviews, setReviews] = useState([])
  const [isFavorite, setIsFavorite] = useState(false)

  const [newReview, setNewReview] = useState({ rating: 5, comment: '', photoUrl: '' })
  const [editingReviewId, setEditingReviewId] = useState(null)
  const [editingReview, setEditingReview] = useState({ rating: 5, comment: '', photoUrl: '' })

  const [isEditingRestaurant, setIsEditingRestaurant] = useState(false)
  const [restaurantEdit, setRestaurantEdit] = useState(buildRestaurantEditData(null))
  const [restaurantPhotoFile, setRestaurantPhotoFile] = useState(null)

  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState('')
  const [actionError, setActionError] = useState('')

  const userId = user?.userId
  const isOwnerRole = user?.role === 'OWNER'
  const isReviewer = user?.role !== 'OWNER'
  const canWriteReview = isAuthenticated && isReviewer

  useEffect(() => {
    let isMounted = true

    async function loadRestaurant() {
      try {
        setIsLoading(true)
        const data = await fetchRestaurantDetails(restaurantId)

        if (!isMounted) {
          return
        }

        setRestaurant(data.restaurant)
        setReviews(data.reviews)
        setRestaurantEdit(buildRestaurantEditData(data.restaurant))

        if (isAuthenticated) {
          const favorites = await fetchFavorites()
          if (isMounted) {
            setIsFavorite(favorites.some((favorite) => favorite.id === data.restaurant.id))
          }
        }
      } catch (requestError) {
        if (isMounted) {
          setError(requestError?.response?.data?.detail || 'Could not load restaurant details.')
        }
      } finally {
        if (isMounted) {
          setIsLoading(false)
        }
      }
    }

    loadRestaurant()
    return () => {
      isMounted = false
    }
  }, [restaurantId, isAuthenticated])

  async function toggleFavorite() {
    if (!restaurant) {
      return
    }

    setActionError('')

    try {
      if (isFavorite) {
        await removeFavorite(restaurant.id)
        setIsFavorite(false)
      } else {
        await addFavorite(restaurant.id)
        setIsFavorite(true)
      }
    } catch (requestError) {
      setActionError(requestError?.response?.data?.detail || 'Could not update favorite.')
    }
  }

  async function handleClaimRestaurant() {
    setActionError('')

    try {
      await claimRestaurant(restaurantId)
      const data = await fetchRestaurantDetails(restaurantId)
      setRestaurant(data.restaurant)
    } catch (requestError) {
      setActionError(requestError?.response?.data?.detail || 'Could not claim restaurant.')
    }
  }

  async function saveRestaurantEdits(event) {
    event.preventDefault()
    if (!restaurant) {
      return
    }

    setActionError('')

    try {
      let uploadedPhotoUrl = restaurantEdit.photoUrl.trim() || null
      if (restaurantPhotoFile) {
        const upload = await uploadImage(restaurantPhotoFile)
        uploadedPhotoUrl = upload.url
      }

      const updated = await updateRestaurant(restaurant.id, {
        name: restaurantEdit.name,
        cuisine_type: restaurantEdit.cuisine,
        address: restaurantEdit.address,
        city: restaurantEdit.city,
        state: restaurantEdit.state.toUpperCase().slice(0, 2),
        zip_code: restaurantEdit.zipCode,
        description: restaurantEdit.description,
        contact_phone: restaurantEdit.contactPhone,
        hours_text: restaurantEdit.hoursText,
        amenities_text: restaurantEdit.amenitiesText,
        photo_url: uploadedPhotoUrl,
        price_tier: restaurantEdit.priceLevel,
      })

      setRestaurant((prev) => ({
        ...updated,
        rating: prev?.rating ?? updated.rating,
        reviewCount: prev?.reviewCount ?? updated.reviewCount,
      }))
      setRestaurantEdit(buildRestaurantEditData(updated))
      setRestaurantPhotoFile(null)
      setIsEditingRestaurant(false)
    } catch (requestError) {
      setActionError(requestError?.response?.data?.detail || 'Could not update restaurant listing.')
    }
  }

  async function handleCreateReview(event) {
    event.preventDefault()
    setActionError('')

    try {
      const created = await createReview({
        restaurant_id: Number(restaurantId),
        rating: newReview.rating,
        comment: newReview.comment,
        photo_url: newReview.photoUrl.trim() || null,
      })
      setReviews((prev) => [created, ...prev])
      setNewReview({ rating: 5, comment: '', photoUrl: '' })
    } catch (requestError) {
      setActionError(requestError?.response?.data?.detail || 'Could not submit review.')
    }
  }

  function startEdit(review) {
    setEditingReviewId(review.id)
    setEditingReview({ rating: review.rating, comment: review.comment, photoUrl: review.photoUrl || '' })
  }

  async function saveEdit(reviewId) {
    setActionError('')
    try {
      const updated = await updateReview(reviewId, {
        rating: editingReview.rating,
        comment: editingReview.comment,
        photo_url: editingReview.photoUrl.trim() || null,
      })
      setReviews((prev) => prev.map((review) => (review.id === reviewId ? updated : review)))
      setEditingReviewId(null)
    } catch (requestError) {
      setActionError(requestError?.response?.data?.detail || 'Could not update review.')
    }
  }

  async function removeReview(reviewId) {
    setActionError('')
    try {
      await deleteReview(reviewId)
      setReviews((prev) => prev.filter((review) => review.id !== reviewId))
    } catch (requestError) {
      setActionError(requestError?.response?.data?.detail || 'Could not delete review.')
    }
  }

  if (isLoading) {
    return (
      <section className='page'>
        <p className='muted'>Loading restaurant details...</p>
      </section>
    )
  }

  if (error || !restaurant) {
    return (
      <section className='page'>
        <h1>Restaurant not found</h1>
        <p className='error-text'>{error || 'Unknown error.'}</p>
        <p>
          Go back to <Link to='/explore'>Explore</Link>.
        </p>
      </section>
    )
  }

  const canClaim = isAuthenticated && isOwnerRole && !restaurant.ownerId
  const isClaimedByCurrentOwner = isAuthenticated && isOwnerRole && restaurant.ownerId === userId
  const canEditRestaurant = isAuthenticated && (restaurant.createdBy === userId || restaurant.ownerId === userId)

  return (
    <section className='page'>
      <div className='detail-hero'>
        <img src={restaurant.imageUrl} alt={restaurant.name} className='detail-image' />
        <div>
          <h1>{restaurant.name}</h1>
          <p className='muted'>
            {restaurant.cuisine} • {restaurant.city} • {restaurant.priceLevel} • {restaurant.rating.toFixed(1)}
          </p>
          <p className='muted'>
            {restaurant.address}, {restaurant.city}, {restaurant.state} {restaurant.zipCode}
          </p>
          {restaurant.contactPhone ? <p className='muted'>Contact: {restaurant.contactPhone}</p> : null}
          {restaurant.hoursText ? <p className='muted'>Hours: {restaurant.hoursText}</p> : null}
          {restaurant.amenitiesText ? <p className='muted'>Amenities: {restaurant.amenitiesText}</p> : null}
          <p>{restaurant.description}</p>

          <div className='hero-actions'>
            {canWriteReview && (
              <Link to={`/restaurants/${restaurant.id}/review`} className='btn btn-primary'>
                Write Review
              </Link>
            )}

            {isAuthenticated && (
              <button type='button' className='btn btn-secondary' onClick={toggleFavorite}>
                {isFavorite ? 'Remove Favorite' : 'Add Favorite'}
              </button>
            )}

            {canClaim && (
              <button type='button' className='btn btn-secondary' onClick={handleClaimRestaurant}>
                Claim Restaurant
              </button>
            )}

            {isClaimedByCurrentOwner && (
              <button
                type='button'
                className='btn btn-secondary'
                onClick={() => navigate(`/restaurants/${restaurant.id}/owner-dashboard`)}
              >
                Owner Dashboard
              </button>
            )}

            {canEditRestaurant && (
              <button
                type='button'
                className='btn btn-secondary'
                onClick={() => setIsEditingRestaurant((prev) => !prev)}
              >
                {isEditingRestaurant ? 'Close Edit' : 'Edit Listing'}
              </button>
            )}
          </div>

          {actionError && <p className='error-text'>{actionError}</p>}
        </div>
      </div>

      {isEditingRestaurant && canEditRestaurant && (
        <section className='form-card'>
          <h2>Edit Listing</h2>
          <p className='muted'>Update cuisine, location, contact info, photo, pricing tier, amenities, and hours.</p>

          <form className='inline-form' onSubmit={saveRestaurantEdits}>
            <div className='split-grid'>
              <label htmlFor='editName'>
                Restaurant name
                <input
                  id='editName'
                  value={restaurantEdit.name}
                  onChange={(event) => setRestaurantEdit((prev) => ({ ...prev, name: event.target.value }))}
                />
              </label>

              <label htmlFor='editCuisine'>
                Cuisine type
                <input
                  id='editCuisine'
                  value={restaurantEdit.cuisine}
                  onChange={(event) => setRestaurantEdit((prev) => ({ ...prev, cuisine: event.target.value }))}
                />
              </label>
            </div>

            <label htmlFor='editAddress'>
              Address
              <input
                id='editAddress'
                value={restaurantEdit.address}
                onChange={(event) => setRestaurantEdit((prev) => ({ ...prev, address: event.target.value }))}
              />
            </label>

            <div className='split-grid'>
              <label htmlFor='editCity'>
                City
                <input
                  id='editCity'
                  value={restaurantEdit.city}
                  onChange={(event) => setRestaurantEdit((prev) => ({ ...prev, city: event.target.value }))}
                />
              </label>

              <label htmlFor='editState'>
                State code
                <input
                  id='editState'
                  maxLength={2}
                  value={restaurantEdit.state}
                  onChange={(event) =>
                    setRestaurantEdit((prev) => ({
                      ...prev,
                      state: event.target.value.toUpperCase().replace(/[^A-Z]/g, '').slice(0, 2),
                    }))
                  }
                />
              </label>

              <label htmlFor='editZipCode'>
                ZIP code
                <input
                  id='editZipCode'
                  value={restaurantEdit.zipCode}
                  onChange={(event) => setRestaurantEdit((prev) => ({ ...prev, zipCode: event.target.value }))}
                />
              </label>
            </div>

            <div className='split-grid'>
              <label htmlFor='editContactPhone'>
                Contact phone
                <input
                  id='editContactPhone'
                  value={restaurantEdit.contactPhone}
                  onChange={(event) => setRestaurantEdit((prev) => ({ ...prev, contactPhone: event.target.value }))}
                />
              </label>

              <label htmlFor='editHoursText'>
                Hours of operation
                <input
                  id='editHoursText'
                  value={restaurantEdit.hoursText}
                  onChange={(event) => setRestaurantEdit((prev) => ({ ...prev, hoursText: event.target.value }))}
                />
              </label>
            </div>

            <div className='split-grid'>
              <label htmlFor='editPriceTier'>
                Price tier
                <select
                  id='editPriceTier'
                  value={restaurantEdit.priceLevel}
                  onChange={(event) => setRestaurantEdit((prev) => ({ ...prev, priceLevel: event.target.value }))}
                >
                  <option value='$'>$</option>
                  <option value='$$'>$$</option>
                  <option value='$$$'>$$$</option>
                  <option value='$$$$'>$$$$</option>
                </select>
              </label>

              <label htmlFor='editAmenitiesText'>
                Amenities
                <input
                  id='editAmenitiesText'
                  value={restaurantEdit.amenitiesText}
                  onChange={(event) => setRestaurantEdit((prev) => ({ ...prev, amenitiesText: event.target.value }))}
                />
              </label>
            </div>

            <label htmlFor='editPhotoUrl'>
              Photo URL
              <input
                id='editPhotoUrl'
                value={restaurantEdit.photoUrl}
                onChange={(event) => setRestaurantEdit((prev) => ({ ...prev, photoUrl: event.target.value }))}
              />
            </label>

            <label htmlFor='editPhotoFile'>
              Upload restaurant photo
              <input
                id='editPhotoFile'
                type='file'
                accept='image/*'
                onChange={(event) => setRestaurantPhotoFile(event.target.files?.[0] || null)}
              />
            </label>

            <label htmlFor='editDescription'>
              Description
              <textarea
                id='editDescription'
                rows={4}
                value={restaurantEdit.description}
                onChange={(event) => setRestaurantEdit((prev) => ({ ...prev, description: event.target.value }))}
              />
            </label>

            <button className='btn btn-primary' type='submit'>
              Save Listing Changes
            </button>
          </form>
        </section>
      )}

      {canWriteReview && (
        <section className='form-card'>
          <h2>Quick Review</h2>
          <form onSubmit={handleCreateReview} className='inline-form'>
            <label htmlFor='newRating'>
              Rating
              <select
                id='newRating'
                value={newReview.rating}
                onChange={(event) => setNewReview((prev) => ({ ...prev, rating: Number(event.target.value) }))}
              >
                <option value={5}>5</option>
                <option value={4}>4</option>
                <option value={3}>3</option>
                <option value={2}>2</option>
                <option value={1}>1</option>
              </select>
            </label>

            <label htmlFor='newComment'>
              Comment
              <textarea
                id='newComment'
                rows={3}
                required
                value={newReview.comment}
                onChange={(event) => setNewReview((prev) => ({ ...prev, comment: event.target.value }))}
              />
            </label>

            <label htmlFor='newPhotoUrl'>
              Photo URL (optional)
              <input
                id='newPhotoUrl'
                type='url'
                placeholder='https://...'
                value={newReview.photoUrl}
                onChange={(event) => setNewReview((prev) => ({ ...prev, photoUrl: event.target.value }))}
              />
            </label>

            <button className='btn btn-primary' type='submit'>
              Submit Review
            </button>
          </form>
        </section>
      )}

      <section>
        <h2>Reviews</h2>
        <div className='review-list'>
          {reviews.map((review) => {
            const canEditThisReview = isReviewer && isAuthenticated && review.userId === userId
            const isEditing = editingReviewId === review.id

            return (
              <article key={review.id} className='review-card'>
                <header>
                  <strong>{review.author}</strong>
                  <span className='rating-pill'>{review.rating.toFixed(1)}</span>
                </header>

                <p className='muted'>{review.createdAt ? new Date(review.createdAt).toLocaleString() : ''}</p>

                {isEditing ? (
                  <div className='inline-form'>
                    <label htmlFor={`rating-${review.id}`}>
                      Rating
                      <select
                        id={`rating-${review.id}`}
                        value={editingReview.rating}
                        onChange={(event) => setEditingReview((prev) => ({ ...prev, rating: Number(event.target.value) }))}
                      >
                        <option value={5}>5</option>
                        <option value={4}>4</option>
                        <option value={3}>3</option>
                        <option value={2}>2</option>
                        <option value={1}>1</option>
                      </select>
                    </label>

                    <label htmlFor={`comment-${review.id}`}>
                      Comment
                      <textarea
                        id={`comment-${review.id}`}
                        rows={3}
                        value={editingReview.comment}
                        onChange={(event) => setEditingReview((prev) => ({ ...prev, comment: event.target.value }))}
                      />
                    </label>

                    <label htmlFor={`photo-${review.id}`}>
                      Photo URL (optional)
                      <input
                        id={`photo-${review.id}`}
                        type='url'
                        placeholder='https://...'
                        value={editingReview.photoUrl}
                        onChange={(event) => setEditingReview((prev) => ({ ...prev, photoUrl: event.target.value }))}
                      />
                    </label>

                    <div className='hero-actions'>
                      <button type='button' className='btn btn-primary' onClick={() => saveEdit(review.id)}>
                        Save
                      </button>
                      <button type='button' className='btn btn-secondary' onClick={() => setEditingReviewId(null)}>
                        Cancel
                      </button>
                    </div>
                  </div>
                ) : (
                  <>
                    <p>{review.comment}</p>
                    {review.photoUrl ? <img className='review-photo' src={review.photoUrl} alt='Review' /> : null}
                  </>
                )}

                {canEditThisReview && !isEditing && (
                  <div className='hero-actions'>
                    <button type='button' className='btn btn-secondary' onClick={() => startEdit(review)}>
                      Edit
                    </button>
                    <button type='button' className='btn btn-secondary' onClick={() => removeReview(review.id)}>
                      Delete
                    </button>
                  </div>
                )}
              </article>
            )
          })}
          {reviews.length === 0 && <p className='muted'>No reviews yet.</p>}
        </div>
      </section>
    </section>
  )
}

export default RestaurantDetails
