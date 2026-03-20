import { useEffect, useState } from 'react'
import { fetchCurrentUser, fetchPreferences, updateCurrentUser, updatePreferences } from '../api'
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

function Profile() {
  const { token, refreshUser } = useAuth()

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
  })

  const [preferences, setPreferences] = useState({
    preferred_cuisines: [],
    price_range: '$$',
    preferred_locations: [],
    dietary_needs: [],
    ambiance_preferences: [],
    sort_preference: 'rating',
  })

  const [locationsInput, setLocationsInput] = useState('')
  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  useEffect(() => {
    let mounted = true

    async function loadProfileData() {
      try {
        setIsLoading(true)
        const [profileData, preferencesData] = await Promise.all([fetchCurrentUser(), fetchPreferences()])

        if (!mounted) {
          return
        }

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
        })

        setPreferences({
          preferred_cuisines: preferencesData.preferred_cuisines || [],
          price_range: preferencesData.price_range || '$$',
          preferred_locations: preferencesData.preferred_locations || [],
          dietary_needs: preferencesData.dietary_needs || [],
          ambiance_preferences: preferencesData.ambiance_preferences || [],
          sort_preference: preferencesData.sort_preference || 'rating',
        })

        setLocationsInput((preferencesData.preferred_locations || []).join(', '))
      } catch (requestError) {
        if (mounted) {
          setError(requestError?.response?.data?.detail || 'Could not load profile/preferences.')
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

  const toggleInList = (key, value) => {
    setPreferences((prev) => ({
      ...prev,
      [key]: prev[key].includes(value) ? prev[key].filter((item) => item !== value) : [...prev[key], value],
    }))
  }

  const handleSave = async (event) => {
    event.preventDefault()
    setError('')
    setSuccess('')

    try {
      setIsSaving(true)

      const preferencePayload = {
        ...preferences,
        preferred_locations: arrayFromCsv(locationsInput),
      }

      await Promise.all([updateCurrentUser(profile), updatePreferences(preferencePayload)])
      if (token) {
        await refreshUser(token, profile.email)
      }
      setSuccess('Profile and preferences saved.')
    } catch (requestError) {
      setError(requestError?.response?.data?.detail || 'Could not save profile/preferences.')
    } finally {
      setIsSaving(false)
    }
  }

  return (
    <section className='page'>
      <h1>Profile & Preferences</h1>
      <p className='muted'>Update your personal details and AI recommendation preferences.</p>

      {isLoading && <p className='muted'>Loading your profile...</p>}
      {error && <p className='error-text'>{error}</p>}

      {!isLoading && (
        <form className='form-card' onSubmit={handleSave}>
          <h2>Profile</h2>

          <label htmlFor='name'>Name</label>
          <input id='name' value={profile.name} onChange={(event) => setProfile((prev) => ({ ...prev, name: event.target.value }))} />

          <label htmlFor='email'>Email</label>
          <input
            id='email'
            type='email'
            value={profile.email}
            onChange={(event) => setProfile((prev) => ({ ...prev, email: event.target.value }))}
          />

          <label htmlFor='role'>Account type</label>
          <select id='role' value={profile.role} onChange={(event) => setProfile((prev) => ({ ...prev, role: event.target.value }))}>
            <option value='USER'>Reviewer</option>
            <option value='OWNER'>Restaurant Owner</option>
          </select>

          <label htmlFor='phone'>Phone number</label>
          <input
            id='phone'
            value={profile.phone_number}
            onChange={(event) => setProfile((prev) => ({ ...prev, phone_number: event.target.value }))}
          />

          <label htmlFor='about'>About me</label>
          <textarea
            id='about'
            rows={3}
            value={profile.about_me}
            onChange={(event) => setProfile((prev) => ({ ...prev, about_me: event.target.value }))}
          />

          <div className='split-grid'>
            <label htmlFor='city'>
              City
              <input id='city' value={profile.city} onChange={(event) => setProfile((prev) => ({ ...prev, city: event.target.value }))} />
            </label>

            <label htmlFor='state'>
              State (abbr.)
              <input
                id='state'
                maxLength={10}
                value={profile.state}
                onChange={(event) => setProfile((prev) => ({ ...prev, state: event.target.value }))}
              />
            </label>
          </div>

          <label htmlFor='country'>Country</label>
          <select id='country' value={profile.country} onChange={(event) => setProfile((prev) => ({ ...prev, country: event.target.value }))}>
            {COUNTRY_OPTIONS.map((country) => (
              <option key={country} value={country}>
                {country}
              </option>
            ))}
          </select>

          <label htmlFor='languages'>Languages (comma separated)</label>
          <input
            id='languages'
            value={profile.languages}
            onChange={(event) => setProfile((prev) => ({ ...prev, languages: event.target.value }))}
          />

          <label htmlFor='gender'>Gender</label>
          <input id='gender' value={profile.gender} onChange={(event) => setProfile((prev) => ({ ...prev, gender: event.target.value }))} />

          <label htmlFor='profileImage'>Profile image URL</label>
          <input
            id='profileImage'
            value={profile.profile_image_url}
            onChange={(event) => setProfile((prev) => ({ ...prev, profile_image_url: event.target.value }))}
          />

          <h2>AI Preferences</h2>

          <fieldset>
            <legend>Preferred cuisines</legend>
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

          <label htmlFor='priceRange'>Price range</label>
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

          <label htmlFor='locations'>Preferred locations (city/zip, comma separated)</label>
          <input id='locations' value={locationsInput} onChange={(event) => setLocationsInput(event.target.value)} />

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
            <legend>Ambiance preferences</legend>
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

          <label htmlFor='sortPreference'>Sort preference</label>
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

          {success && <p className='success-text'>{success}</p>}

          <button className='btn btn-primary' type='submit' disabled={isSaving}>
            {isSaving ? 'Saving...' : 'Save Profile & Preferences'}
          </button>
        </form>
      )}
    </section>
  )
}

export default Profile
