import { useState } from 'react'
import { Link, Navigate, NavLink, Outlet, Route, Routes, useLocation } from 'react-router-dom'
import { useAuth } from './auth'
import AddRestaurant from './pages/AddRestaurant'
import Explore from './pages/Explore'
import FavoritesHistory from './pages/FavoritesHistory'
import Home from './pages/Home'
import Login from './pages/Login'
import Profile from './pages/Profile'
import RestaurantDetails from './pages/RestaurantDetails'
import Signup from './pages/Signup'
import WriteReview from './pages/WriteReview'

function ProtectedRoute({ children }) {
  const { isAuthenticated } = useAuth()
  const location = useLocation()

  if (!isAuthenticated) {
    return <Navigate to='/login' replace state={{ from: location.pathname }} />
  }

  return children
}

const publicLinks = [
  { to: '/', label: 'Home' },
  { to: '/explore', label: 'Explore' },
]

const privateLinks = [
  { to: '/restaurants/new', label: 'Add Restaurant' },
  { to: '/my-activity', label: 'Favorites/History' },
  { to: '/profile', label: 'Profile' },
]

function Navbar() {
  const [isOpen, setIsOpen] = useState(false)
  const { isAuthenticated, logout } = useAuth()

  const closeMenu = () => setIsOpen(false)

  return (
    <header className='navbar-shell'>
      <nav className='navbar'>
        <Link to='/' className='brand' onClick={closeMenu}>
          yelp
        </Link>

        <button className='menu-toggle' type='button' onClick={() => setIsOpen((prev) => !prev)}>
          {isOpen ? 'Close' : 'Menu'}
        </button>

        <div className={`nav-links ${isOpen ? 'open' : ''}`}>
          {publicLinks.map((link) => (
            <NavLink key={link.to} to={link.to} onClick={closeMenu} className={({ isActive }) => (isActive ? 'active-link' : '')}>
              {link.label}
            </NavLink>
          ))}

          {isAuthenticated &&
            privateLinks.map((link) => (
              <NavLink
                key={link.to}
                to={link.to}
                onClick={closeMenu}
                className={({ isActive }) => (isActive ? 'active-link' : '')}
              >
                {link.label}
              </NavLink>
            ))}

          {!isAuthenticated ? (
            <>
              <NavLink to='/login' onClick={closeMenu} className={({ isActive }) => (isActive ? 'active-link' : '')}>
                Login
              </NavLink>
              <NavLink to='/signup' onClick={closeMenu} className={({ isActive }) => (isActive ? 'active-link' : '')}>
                Sign Up
              </NavLink>
            </>
          ) : (
            <button
              className='link-button'
              type='button'
              onClick={() => {
                logout()
                closeMenu()
              }}
            >
              Log Out
            </button>
          )}
        </div>
      </nav>
    </header>
  )
}

function Layout() {
  return (
    <div className='app-shell'>
      <Navbar />
      <main className='main-content'>
        <Outlet />
      </main>
    </div>
  )
}

function NotFound() {
  return (
    <section className='page'>
      <h1>404</h1>
      <p>Page not found.</p>
      <Link to='/explore'>Back to Explore</Link>
    </section>
  )
}

function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path='/' element={<Home />} />
        <Route path='/explore' element={<Explore />} />
        <Route path='/restaurants/:restaurantId' element={<RestaurantDetails />} />
        <Route path='/login' element={<Login />} />
        <Route path='/signup' element={<Signup />} />

        <Route
          path='/profile'
          element={
            <ProtectedRoute>
              <Profile />
            </ProtectedRoute>
          }
        />
        <Route
          path='/restaurants/new'
          element={
            <ProtectedRoute>
              <AddRestaurant />
            </ProtectedRoute>
          }
        />
        <Route
          path='/restaurants/:restaurantId/review'
          element={
            <ProtectedRoute>
              <WriteReview />
            </ProtectedRoute>
          }
        />
        <Route
          path='/my-activity'
          element={
            <ProtectedRoute>
              <FavoritesHistory />
            </ProtectedRoute>
          }
        />

        <Route path='*' element={<NotFound />} />
      </Route>
    </Routes>
  )
}

export default App
