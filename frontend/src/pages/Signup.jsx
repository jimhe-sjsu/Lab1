import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth'

function Signup() {
  const [form, setForm] = useState({
    fullName: '',
    email: '',
    password: '',
    role: 'USER',
    restaurantLocation: '',
  })
  const [error, setError] = useState('')
  const { signup, isLoading } = useAuth()
  const navigate = useNavigate()

  const isOwner = form.role === 'OWNER'

  const handleSubmit = async (event) => {
    event.preventDefault()
    setError('')

    try {
      await signup(form)
      navigate(isOwner ? '/owner/profile' : '/profile')
    } catch (requestError) {
      setError(requestError.message || 'Signup failed. Please try again.')
    }
  }

  return (
    <section className='page narrow-page'>
      <h1>Sign Up</h1>
      <p className='muted'>Create your account for reviewer or restaurant owner access.</p>

      <form className='form-card' onSubmit={handleSubmit}>
        <label htmlFor='fullName'>Full name</label>
        <input
          id='fullName'
          required
          value={form.fullName}
          onChange={(event) => setForm((prev) => ({ ...prev, fullName: event.target.value }))}
        />

        <label htmlFor='email'>Email</label>
        <input
          id='email'
          type='email'
          required
          value={form.email}
          onChange={(event) => setForm((prev) => ({ ...prev, email: event.target.value }))}
        />

        <label htmlFor='password'>Password</label>
        <input
          id='password'
          type='password'
          minLength={6}
          required
          value={form.password}
          onChange={(event) => setForm((prev) => ({ ...prev, password: event.target.value }))}
        />

        <label htmlFor='role'>Account type</label>
        <select id='role' value={form.role} onChange={(event) => setForm((prev) => ({ ...prev, role: event.target.value }))}>
          <option value='USER'>Reviewer</option>
          <option value='OWNER'>Restaurant Owner</option>
        </select>

        {isOwner && (
          <>
            <label htmlFor='restaurantLocation'>Restaurant location</label>
            <input
              id='restaurantLocation'
              placeholder='San Jose, CA'
              required
              value={form.restaurantLocation}
              onChange={(event) => setForm((prev) => ({ ...prev, restaurantLocation: event.target.value }))}
            />
          </>
        )}

        {error && <p className='error-text'>{error}</p>}

        <button className='btn btn-primary' type='submit' disabled={isLoading}>
          {isLoading ? 'Creating account...' : 'Create account'}
        </button>
      </form>

      <p>
        Already registered? <Link to='/login'>Login</Link>
      </p>
    </section>
  )
}

export default Signup