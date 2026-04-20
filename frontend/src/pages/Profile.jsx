import { useEffect, useState } from 'react'
import { Link, Navigate } from 'react-router-dom'
import {
  fetchCurrentUser,
  fetchFavorites,
  fetchPreferences,
  updateCurrentUser,
  updatePreferences,
  uploadImage,
} from '../api'
import { useAuth } from '../auth'

const COUNTRY_OPTIONS = ['United States', 'Canada', 'Mexico', 'India', 'Japan', 'China', 'United Kingdom']
const CUISINES = ['Italian', 'Chinese', 'Mexican', 'Indian', 'Japanese', 'American', 'Thai', 'Mediterranean']
const DIETARY = ['Vegetarian', 'Vegan', 'Halal', 'Kosher', 'Gluten-free']
const AMBIANCE = ['Casual', 'Fine dining', 'Family-friendly', 'Romantic', 'Quiet', 'Outdoor seating']

function arrayFromCsv(value) {
  return value
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean)
}

function formatRole(role) {
  return role === 'OWNER' ? 'Restaurant Owner' : 'Reviewer'
}

function Profile() {
  const { token, refreshUser, user } = useAuth()

  const [profile, setProfile] = useState({
    name: '',
    email: '',
    role: 'USER',
    phone_number: '',
    about_me: '',
    city: '',
    state: '',
    country: 'United States',
    languages: '',
    gender: '',
    profile_image_url: '',
    restaurant_location: '',
  })

  const [preferences, setPreferences] = useState({
    preferred_cuisines: [],
    price_range: '$$',
    preferred_locations: [],
    search_radius: 25,
    dietary_needs: [],
    ambiance_preferences: [],
    sort_preference: 'rating',
  })

  const [locationsInput, setLocationsInput] = useState('')
  const [favoritesPreview, setFavoritesPreview] = useState([])
  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [profileImageFile, setProfileImageFile] = useState(null)

  useEffect(() => {
    let mounted = true

    async function loadProfileData() {
      try {
        setIsLoading(true)
        setError('')

        const [profileData, preferencesData, favoritesData] = await Promise.all([
          fetchCurrentUser(),
          fetchPreferences(),
          fetchFavorites(),
        ])

        if (!mounted) return

        setProfile({
          name: profileData.name || '',
          email: profileData.email || '',
          role: profileData.role || 'USER',
          phone_number: profileData.phone_number || '',
          about_me: profileData.about_me || '',
          city: profileData.city || '',
          state: profileData.state || '',
          country: profileData.country || 'United States',
          languages: profileData.languages || '',
          gender: profileData.gender || '',
          profile_image_url: profileData.profile_image_url || '',
          restaurant_location: profileData.restaurant_location || '',
        })

        setPreferences({
          preferred_cuisines: preferencesData.preferred_cuisines || [],
          price_range: preferencesData.price_range || '$$',
          preferred_locations: preferencesData.preferred_locations || [],
          search_radius: preferencesData.search_radius || 25,
          dietary_needs: preferencesData.dietary_needs || [],
          ambiance_preferences: preferencesData.ambiance_preferences || [],
          sort_preference: preferencesData.sort_preference || 'rating',
        })

        setLocationsInput((preferencesData.preferred_locations || []).join(', '))
        setFavoritesPreview((favoritesData || []).slice(0, 4))
      } catch (requestError) {
        if (mounted) {
          setError(requestError?.response?.data?.detail || 'Could not load profile and dining preferences.')
        }
      } finally {
        if (mounted) {
          setIsLoading(false)
        }
      }
    }

    loadProfileData()

    return () => {
      mounted = false
    }
  }, [])

  function toggleInList(key, value) {
    setPreferences((prev) => ({
      ...prev,
      [key]: prev[key].includes(value) ? prev[key].filter((item) => item !== value) : [...prev[key], value],
    }))
  }

  async function handleSave(event) {
    event.preventDefault()
    setError('')
    setSuccess('')

    try {
      setIsSaving(true)

      let uploadedProfileImageUrl = profile.profile_image_url
      if (profileImageFile) {
        const upload = await uploadImage(profileImageFile)
        uploadedProfileImageUrl = upload.url
      }

      const cleanedProfile = {
        ...profile,
        profile_image_url: uploadedProfileImageUrl,
        state: profile.state.toUpperCase().slice(0, 2),
      }

      const preferencePayload = {
        ...preferences,
        preferred_locations: arrayFromCsv(locationsInput),
        search_radius: preferences.search_radius ? Number(preferences.search_radius) : null,
      }

      await Promise.all([updateCurrentUser(cleanedProfile), updatePreferences(preferencePayload)])

      if (token) {
        await refreshUser(token, cleanedProfile.email)
      }

      setProfile(cleanedProfile)
      setSuccess('Profile and dining preferences saved successfully.')
    } catch (requestError) {
      setError(requestError?.response?.data?.detail || 'Could not save profile and preferences.')
    } finally {
      setIsSaving(false)
    }
  }

  if (user?.role === 'OWNER') {
    return <Navigate to='/owner/profile' replace />
  }

  return (
    <section className='page'>
      <div>
        <h1>Profile & Dining Preferences</h1>
        <p className='muted'>
          Keep your account details up to date and save dining preferences that improve search,
          favorites, and AI assistant recommendations.
        </p>
      </div>

      {isLoading && <p className='muted'>Loading your profile...</p>}
      {error && <p className='error-text'>{error}</p>}

      {!isLoading && (
        <div className='profile-layout'>
          <form className='form-card' onSubmit={handleSave}>
            <div className='section-title-row'>
              <div>
                <h2>Personal Information</h2>
                <p className='muted'>Basic account details required for your Yelp-style profile.</p>
              </div>
              <span className='profile-badge'>{formatRole(profile.role)}</span>
            </div>

            {profile.profile_image_url ? (
              <img
                src={profile.profile_image_url}
                alt={`${profile.name || 'User'} profile`}
                className='profile-avatar-preview'
              />
            ) : null}

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
                Email address
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

              <label htmlFor='languages'>
                Languages
                <input
                  id='languages'
                  placeholder='English, Telugu'
                  value={profile.languages}
                  onChange={(event) => setProfile((prev) => ({ ...prev, languages: event.target.value }))}
                />
              </label>
            </div>

            <label htmlFor='about'>
              About me
              <textarea
                id='about'
                rows={3}
                placeholder='Tell people a little about your food style or dining interests'
                value={profile.about_me}
                onChange={(event) => setProfile((prev) => ({ ...prev, about_me: event.target.value }))}
              />
            </label>

            <div className='split-grid'>
              <label htmlFor='city'>
                City
                <input
                  id='city'
                  placeholder='San Jose'
                  value={profile.city}
                  onChange={(event) => setProfile((prev) => ({ ...prev, city: event.target.value }))}
                />
              </label>

              <label htmlFor='state'>
                State code
                <input
                  id='state'
                  maxLength={2}
                  placeholder='CA'
                  value={profile.state}
                  onChange={(event) =>
                    setProfile((prev) => ({
                      ...prev,
                      state: event.target.value.toUpperCase().replace(/[^A-Z]/g, '').slice(0, 2),
                    }))
                  }
                />
                <span className='helper-text'>Use 2-letter format like CA, NY, TX.</span>
              </label>
            </div>

            <div className='split-grid'>
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

              <label htmlFor='gender'>
                Gender
                <input
                  id='gender'
                  placeholder='Optional'
                  value={profile.gender}
                  onChange={(event) => setProfile((prev) => ({ ...prev, gender: event.target.value }))}
                />
              </label>
            </div>

            <label htmlFor='profileImage'>
              Profile image URL
              <input
                id='profileImage'
                placeholder='https://...'
                value={profile.profile_image_url}
                onChange={(event) => setProfile((prev) => ({ ...prev, profile_image_url: event.target.value }))}
              />
            </label>

            <label htmlFor='profileImageFile'>
              Upload profile image
              <input
                id='profileImageFile'
                type='file'
                accept='image/*'
                onChange={(event) => setProfileImageFile(event.target.files?.[0] || null)}
              />
            </label>

            <div className='divider-line' />

            <div>
              <h2>Dining Preferences</h2>
              <p className='muted'>
                These preferences should help the AI assistant and search experience feel more personalized.
              </p>
            </div>

            <fieldset>
              <legend>Favorite cuisines</legend>
              <div className='choice-grid'>
                {CUISINES.map((option) => (
                  <label key={option} className='checkbox-item'>
                    <input
                      type='checkbox'
                      checked={preferences.preferred_cuisines.includes(option)}
                      onChange={() => toggleInList('preferred_cuisines', option)}
                    />
                    {option}
                  </label>
                ))}
              </div>
            </fieldset>

            <div className='split-grid'>
              <label htmlFor='priceRange'>
                Budget preference
                <select
                  id='priceRange'
                  value={preferences.price_range || '$$'}
                  onChange={(event) => setPreferences((prev) => ({ ...prev, price_range: event.target.value }))}
                >
                  <option value='$'>$</option>
                  <option value='$$'>$$</option>
                  <option value='$$$'>$$$</option>
                  <option value='$$$$'>$$$$</option>
                </select>
              </label>

              <label htmlFor='sortPreference'>
                Default sort
                <select
                  id='sortPreference'
                  value={preferences.sort_preference || 'rating'}
                  onChange={(event) => setPreferences((prev) => ({ ...prev, sort_preference: event.target.value }))}
                >
                  <option value='rating'>Rating</option>
                  <option value='distance'>Distance</option>
                  <option value='popularity'>Popularity</option>
                  <option value='price'>Price</option>
                </select>
              </label>
            </div>

            <div className='split-grid'>
              <label htmlFor='locations'>
                Preferred dining locations
                <input
                  id='locations'
                  placeholder='San Jose, Santa Clara, 95112'
                  value={locationsInput}
                  onChange={(event) => setLocationsInput(event.target.value)}
                />
                <span className='helper-text'>Enter cities or ZIP codes separated by commas.</span>
              </label>

              <label htmlFor='searchRadius'>
                Search radius (miles)
                <input
                  id='searchRadius'
                  type='number'
                  min='1'
                  max='100'
                  value={preferences.search_radius || ''}
                  onChange={(event) =>
                    setPreferences((prev) => ({
                      ...prev,
                      search_radius: event.target.value ? Number(event.target.value) : '',
                    }))
                  }
                />
                <span className='helper-text'>Used by the AI assistant with your saved locations.</span>
              </label>
            </div>

            <fieldset>
              <legend>Dietary needs</legend>
              <div className='choice-grid'>
                {DIETARY.map((option) => (
                  <label key={option} className='checkbox-item'>
                    <input
                      type='checkbox'
                      checked={preferences.dietary_needs.includes(option)}
                      onChange={() => toggleInList('dietary_needs', option)}
                    />
                    {option}
                  </label>
                ))}
              </div>
            </fieldset>

            <fieldset>
              <legend>Dining atmosphere</legend>
              <div className='choice-grid'>
                {AMBIANCE.map((option) => (
                  <label key={option} className='checkbox-item'>
                    <input
                      type='checkbox'
                      checked={preferences.ambiance_preferences.includes(option)}
                      onChange={() => toggleInList('ambiance_preferences', option)}
                    />
                    {option}
                  </label>
                ))}
              </div>
            </fieldset>

            {success && <p className='success-text'>{success}</p>}

            <button className='btn btn-primary' type='submit' disabled={isSaving}>
              {isSaving ? 'Saving...' : 'Save Profile & Preferences'}
            </button>
          </form>

          <aside className='profile-sidebar'>
            <section className='form-card'>
              <h2>Why this matters</h2>
              <div className='list-stack'>
                <div className='list-item'>Your saved cuisines help the AI recommend better matches.</div>
                <div className='list-item'>Budget and ambiance guide restaurant ranking.</div>
                <div className='list-item'>Preferred locations keep results closer to what you want.</div>
                <div className='list-item'>Favorites and history make the app feel more like Yelp.</div>
              </div>
            </section>

            <section className='form-card'>
              <div className='section-title-row'>
                <div>
                  <h2>Favorites Preview</h2>
                  <p className='muted'>Quick access to restaurants you saved.</p>
                </div>
                <Link to='/my-activity' className='link-accent'>
                  View all
                </Link>
              </div>

              {favoritesPreview.length > 0 ? (
                <div className='list-stack'>
                  {favoritesPreview.map((restaurant) => (
                    <Link key={restaurant.id} className='list-item' to={`/restaurants/${restaurant.id}`}>
                      <strong>{restaurant.name}</strong>
                      <span className='muted'>
                        {restaurant.cuisine} • {restaurant.city} • {restaurant.priceLevel}
                      </span>
                    </Link>
                  ))}
                </div>
              ) : (
                <p className='muted'>No favorites yet. Save restaurants from Explore or Details page.</p>
              )}
            </section>

            <section className='form-card'>
              <h2>Saved Preference Summary</h2>

              <div className='summary-block'>
                <strong>Cuisines</strong>
                <div className='profile-chip-row'>
                  {preferences.preferred_cuisines.length > 0 ? (
                    preferences.preferred_cuisines.map((item) => (
                      <span key={item} className='profile-chip'>
                        {item}
                      </span>
                    ))
                  ) : (
                    <span className='muted'>No cuisines selected yet.</span>
                  )}
                </div>
              </div>

              <div className='summary-block'>
                <strong>Dietary</strong>
                <div className='profile-chip-row'>
                  {preferences.dietary_needs.length > 0 ? (
                    preferences.dietary_needs.map((item) => (
                      <span key={item} className='profile-chip'>
                        {item}
                      </span>
                    ))
                  ) : (
                    <span className='muted'>No dietary filters selected.</span>
                  )}
                </div>
              </div>

              <div className='summary-block'>
                <strong>Ambiance</strong>
                <div className='profile-chip-row'>
                  {preferences.ambiance_preferences.length > 0 ? (
                    preferences.ambiance_preferences.map((item) => (
                      <span key={item} className='profile-chip'>
                        {item}
                      </span>
                    ))
                  ) : (
                    <span className='muted'>No ambiance preferences selected.</span>
                  )}
                </div>
              </div>

              <div className='summary-block'>
                <strong>Search radius</strong>
                <div className='profile-chip-row'>
                  <span className='profile-chip'>{preferences.search_radius || 25} miles</span>
                </div>
              </div>
            </section>
          </aside>
        </div>
      )}
    </section>
  )
}

export default Profile