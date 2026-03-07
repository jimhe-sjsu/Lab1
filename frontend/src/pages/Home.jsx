import { Link } from 'react-router-dom'

function Home() {
  return (
    <section className='page hero-page'>
      <p className='eyebrow'>DATA236 Lab 1 Frontend</p>
      <h1>Discover restaurants, save favorites, and write reviews.</h1>
      <p className='lead'>This version focuses on core frontend flows and excludes chatbot UI for now.</p>
      <div className='hero-actions'>
        <Link className='btn btn-primary' to='/explore'>
          Explore Restaurants
        </Link>
        <Link className='btn btn-secondary' to='/signup'>
          Create Account
        </Link>
      </div>
    </section>
  )
}

export default Home
