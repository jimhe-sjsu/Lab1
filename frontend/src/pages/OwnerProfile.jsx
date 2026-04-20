import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { fetchCurrentUser, fetchRestaurants, updateCurrentUser } from '../api'
import { useAuth } from '../auth'

const COUNTRY_OPTIONS = ['United States', 'Canada', 'Mexico', 'India', 'Japan', 'China', 'United Kingdom']

function OwnerProfile() {
  const { token, refreshUser, user } = useAuth()

  const [profile, setProfile] = useState({
    name: '',
    email: '',
    phone_number: '',
    city: '',
    state: '',
    country: 'United States',
    profile_image_url: '',
    restaurant_location: '',
  })

  const [restaurants, setRestaurants] = useState([])
  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  useEffect(() => {
    let mounted = true

    async function loadData() {
      try {
        setIsLoading(true)
        setError('')

        const [profileData, restaurantData] = await Promise.all([
          fetchCurrentUser(),
          fetchRestaurants(),
        ])

        if (!mounted) return

        setProfile({
          name: profileData.name || '',
          email: profileData.email || '',
          phone_number: profileData.phone_number || '',
          city: profileData.city || '',
          state: profileData.state || '',
          country: profileData.country || 'United States',
          profile_image_url: profileData.profile_image_url || '',
          restaurant_location: profileData.restaurant_location || '',
        })

        setRestaurants(restaurantData || [])
      } catch (requestError) {
        if (mounted) {
          setError(requestError?.response?.data?.detail || 'Could not load owner profile.')
        }
      } finally {
        if (mounted) {
          setIsLoading(false)
        }
      }
    }

    loadData()

    return () => {
      mounted = false
    }
  }, [])

  const myRestaurants = useMemo(() => {
    return restaurants.filter(
      (restaurant) =>
        restaurant.ownerId === user?.userId || restaurant.createdBy === user?.userId
    )
  }, [restaurants, user?.userId])

  const postedRestaurants = useMemo(() => {
    return myRestaurants.filter((restaurant) => restaurant.createdBy === user?.userId)
  }, [myRestaurants, user?.userId])

  const claimedRestaurants = useMemo(() => {
    return myRestaurants.filter((restaurant) => restaurant.ownerId === user?.userId)
  }, [myRestaurants, user?.userId])

  async function handleSave(event) {
    event.preventDefault()
    setError('')
    setSuccess('')

    try {
      setIsSaving(true)

      const cleanedProfile = {
        ...profile,
        state: profile.state.toUpperCase().slice(0, 2),
      }

      await updateCurrentUser(cleanedProfile)

      if (token) {
        await refreshUser(token, cleanedProfile.email)
      }

      setProfile(cleanedProfile)
      setSuccess('Owner profile updated successfully.')
    } catch (requestError) {
      setError(requestError?.response?.data?.detail || 'Could not save owner profile.')
    } finally {
      setIsSaving(false)
    }
  }

    function RestaurantManagerCard({ restaurant }) {
    const isManaged = restaurant.ownerId === user?.userId

    return (
        <article className='owner-restaurant-card'>
        <div className='owner-restaurant-top'>
            <h3 className='owner-restaurant-title'>{restaurant.name}</h3>
            <span className='owner-status-badge'>
            {isManaged ? 'Owner Managed' : 'Posted by You'}
            </span>
        </div>

        <p className='owner-restaurant-meta'>
            {restaurant.cuisine} • {restaurant.city}, {restaurant.state} • {restaurant.priceLevel}
        </p>

        <div className='owner-restaurant-actions'>
            <Link to={`/restaurants/${restaurant.id}`} className='btn btn-secondary owner-action-btn'>
            Open
            </Link>

            <Link to={`/restaurants/${restaurant.id}`} className='btn btn-secondary owner-action-btn'>
            Manage
            </Link>

            {isManaged && (
            <Link
                to={`/restaurants/${restaurant.id}/owner-dashboard`}
                className='btn btn-secondary owner-action-btn'
            >
                Dashboard
            </Link>
            )}
        </div>
        </article>
    )
    }

  return (
    <section className='page'>
      <div>
        <h1>Owner Profile</h1>
        <p className='muted'>
          Manage your owner account, registered restaurant location, and restaurants you posted or claimed.
        </p>
      </div>

      {isLoading && <p className='muted'>Loading owner profile...</p>}
      {error && <p className='error-text'>{error}</p>}

      {!isLoading && (
        <div className='profile-layout'>
          <form className='form-card' onSubmit={handleSave}>
            <h2>Owner Information</h2>

            <div className='split-grid'>
              <label htmlFor='name'>
                Full name
                <input
                  id='name'
                  value={profile.name}
                  onChange={(event) => setProfile((prev) => ({ ...prev, name: event.target.value }))}
                />
              </label>

              <label htmlFor='email'>
                Email
                <input
                  id='email'
                  type='email'
                  value={profile.email}
                  onChange={(event) => setProfile((prev) => ({ ...prev, email: event.target.value }))}
                />
              </label>
            </div>

            <div className='split-grid'>
              <label htmlFor='phone'>
                Phone number
                <input
                  id='phone'
                  value={profile.phone_number}
                  onChange={(event) => setProfile((prev) => ({ ...prev, phone_number: event.target.value }))}
                />
              </label>

              <label htmlFor='restaurantLocation'>
                Registered restaurant location
                <input
                  id='restaurantLocation'
                  placeholder='San Jose, CA'
                  value={profile.restaurant_location}
                  onChange={(event) => setProfile((prev) => ({ ...prev, restaurant_location: event.target.value }))}
                />
              </label>
            </div>

            <div className='split-grid'>
              <label htmlFor='city'>
                City
                <input
                  id='city'
                  value={profile.city}
                  onChange={(event) => setProfile((prev) => ({ ...prev, city: event.target.value }))}
                />
              </label>

              <label htmlFor='state'>
                State code
                <input
                  id='state'
                  maxLength={2}
                  value={profile.state}
                  onChange={(event) =>
                    setProfile((prev) => ({
                      ...prev,
                      state: event.target.value.toUpperCase().replace(/[^A-Z]/g, '').slice(0, 2),
                    }))
                  }
                />
              </label>
            </div>

            <label htmlFor='country'>
              Country
              <select
                id='country'
                value={profile.country}
                onChange={(event) => setProfile((prev) => ({ ...prev, country: event.target.value }))}
              >
                {COUNTRY_OPTIONS.map((country) => (
                  <option key={country} value={country}>
                    {country}
                  </option>
                ))}
              </select>
            </label>

            <label htmlFor='profileImage'>
              Profile image URL
              <input
                id='profileImage'
                value={profile.profile_image_url}
                onChange={(event) => setProfile((prev) => ({ ...prev, profile_image_url: event.target.value }))}
              />
            </label>

            {success && <p className='success-text'>{success}</p>}

            <button className='btn btn-primary' type='submit' disabled={isSaving}>
              {isSaving ? 'Saving...' : 'Save Owner Profile'}
            </button>
          </form>

          <aside className='profile-sidebar'>
            <section className='form-card'>
              <h2>Owner Actions</h2>
              <div className='list-stack'>
                <Link to='/restaurants/new' className='list-item'>
                  <strong>Post a restaurant</strong>
                  <span className='muted'>Create a new restaurant listing that appears in your owner profile.</span>
                </Link>
                <div className='list-item'>
                  <strong>Claim a restaurant</strong>
                  <span className='muted'>
                    Claim is allowed only for owners whose registered restaurant location matches the listing.
                  </span>
                </div>
              </div>
            </section>

            <section className='form-card'>
            <h2>My Restaurants</h2>
            <p className='muted'>These are restaurants you posted or currently manage.</p>

            {myRestaurants.length > 0 ? (
                <div className='list-stack'>
                {myRestaurants.map((restaurant) => (
                    <RestaurantManagerCard key={restaurant.id} restaurant={restaurant} />
                ))}
                </div>
            ) : (
                <p className='muted'>No owner restaurants yet.</p>
            )}
            </section>

            <section className='form-card'>
              <h2>Quick Summary</h2>
              <div className='list-stack'>
                <div className='list-item'>
                  <strong>Posted by you</strong>
                  <span className='summary-count'>{postedRestaurants.length}</span>
                </div>
                <div className='list-item'>
                  <strong>Claimed/managed by you</strong>
                  <span className='summary-count'>{claimedRestaurants.length}</span>
                </div>
                <div className='list-item'>
                  <strong>Total visible in owner profile</strong>
                  <span className='summary-count'>{myRestaurants.length}</span>
                </div>
              </div>
            </section>
          </aside>
        </div>
      )}
    </section>
  )
}

export default OwnerProfile