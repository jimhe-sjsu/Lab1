import { useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth'

function Login() {
  const [form, setForm] = useState({ email: '', password: '', role: 'USER' })
  const [error, setError] = useState('')
  const { login, isLoading } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()

  const targetPath = location.state?.from || (form.role === 'OWNER' ? '/owner/profile' : '/explore')

  const handleSubmit = async (event) => {
    event.preventDefault()
    setError('')

    try {
      await login(form)
      navigate(targetPath, { replace: true })
    } catch (requestError) {
      setError(requestError.message || 'Login failed. Please try again.')
    }
  }

  return (
    <section className='page narrow-page'>
      <h1>Login</h1>
      <p className='muted'>Use your account to save favorites and submit reviews.</p>

      <form className='form-card' onSubmit={handleSubmit}>
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
          required
          value={form.password}
          onChange={(event) => setForm((prev) => ({ ...prev, password: event.target.value }))}
        />

        <label htmlFor='role'>Portal</label>
        <select id='role' value={form.role} onChange={(event) => setForm((prev) => ({ ...prev, role: event.target.value }))}>
          <option value='USER'>Reviewer</option>
          <option value='OWNER'>Restaurant Owner</option>
        </select>

        {error && <p className='error-text'>{error}</p>}

        <button className='btn btn-primary' type='submit' disabled={isLoading}>
          {isLoading ? 'Logging in...' : 'Login'}
        </button>
      </form>

      <p>
        Need an account? <Link to='/signup'>Sign up</Link>
      </p>
    </section>
  )
}

export default Login
