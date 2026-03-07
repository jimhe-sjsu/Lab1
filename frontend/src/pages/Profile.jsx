import { useState } from 'react'
import { useAuth } from '../auth'

const cuisineOptions = ['Indian', 'Japanese', 'Mexican', 'Italian', 'Healthy', 'Middle Eastern']
const dietaryOptions = ['Vegetarian options', 'Vegan', 'Gluten-Free', 'Halal', 'Low Carb']

function toggleInArray(array, value) {
  return array.includes(value) ? array.filter((item) => item !== value) : [...array, value]
}

function Profile() {
  const { user, updateProfile, isLoading } = useAuth()
  const [saved, setSaved] = useState(false)
  const [form, setForm] = useState(() => ({
    fullName: user?.fullName || '',
    email: user?.email || '',
    city: user?.city || '',
    favoriteCuisines: user?.favoriteCuisines || [],
    dietaryPreferences: user?.dietaryPreferences || [],
  }))

  const handleSubmit = async (event) => {
    event.preventDefault()
    setSaved(false)
    await updateProfile(form)
    setSaved(true)
  }

  return (
    <section className='page'>
      <h1>Profile & Preferences</h1>
      <p className='muted'>Update your profile and recommendation preferences.</p>

      <form className='form-card' onSubmit={handleSubmit}>
        <label htmlFor='fullName'>Full name</label>
        <input
          id='fullName'
          value={form.fullName}
          onChange={(event) => setForm((prev) => ({ ...prev, fullName: event.target.value }))}
        />

        <label htmlFor='email'>Email</label>
        <input
          id='email'
          type='email'
          value={form.email}
          onChange={(event) => setForm((prev) => ({ ...prev, email: event.target.value }))}
        />

        <label htmlFor='city'>City</label>
        <input
          id='city'
          value={form.city}
          onChange={(event) => setForm((prev) => ({ ...prev, city: event.target.value }))}
        />

        <fieldset>
          <legend>Favorite cuisines</legend>
          <div className='choice-grid'>
            {cuisineOptions.map((option) => (
              <label key={option} className='checkbox-item'>
                <input
                  type='checkbox'
                  checked={form.favoriteCuisines.includes(option)}
                  onChange={() =>
                    setForm((prev) => ({
                      ...prev,
                      favoriteCuisines: toggleInArray(prev.favoriteCuisines, option),
                    }))
                  }
                />
                {option}
              </label>
            ))}
          </div>
        </fieldset>

        <fieldset>
          <legend>Dietary preferences</legend>
          <div className='choice-grid'>
            {dietaryOptions.map((option) => (
              <label key={option} className='checkbox-item'>
                <input
                  type='checkbox'
                  checked={form.dietaryPreferences.includes(option)}
                  onChange={() =>
                    setForm((prev) => ({
                      ...prev,
                      dietaryPreferences: toggleInArray(prev.dietaryPreferences, option),
                    }))
                  }
                />
                {option}
              </label>
            ))}
          </div>
        </fieldset>

        {saved && <p className='success-text'>Profile saved.</p>}

        <button className='btn btn-primary' type='submit' disabled={isLoading}>
          {isLoading ? 'Saving...' : 'Save profile'}
        </button>
      </form>
    </section>
  )
}

export default Profile
