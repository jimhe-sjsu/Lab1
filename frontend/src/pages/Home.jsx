import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { chatWithAssistant, searchRestaurants } from '../api'
import { useAuth } from '../auth'

function HomeRestaurantCard({ restaurant }) {
  return (
    <Link to={`/restaurants/${restaurant.id}`} className='restaurant-card' aria-label={`Open ${restaurant.name}`}>
      <img src={restaurant.imageUrl} alt={restaurant.name} className='restaurant-card-image' />
      <div className='restaurant-card-body'>
        <div className='restaurant-card-header'>
          <h3>{restaurant.name}</h3>
          <span className='rating-pill'>{restaurant.rating.toFixed(1)}</span>
        </div>
        <p className='muted'>
          {restaurant.cuisine} • {restaurant.city} • {restaurant.priceLevel}
        </p>
        <p>{restaurant.description}</p>
      </div>
    </Link>
  )
}

function RecommendationCard({ item }) {
  return (
    <Link to={`/restaurants/${item.id}`} className='recommendation-card'>
      <strong>{item.name}</strong>
      <span className='muted'>
        {item.cuisine} • {item.price_tier} • {item.average_rating?.toFixed?.(1) ?? item.average_rating}
      </span>
      <span>{item.reason}</span>
    </Link>
  )
}

function Home() {
  const navigate = useNavigate()
  const { isAuthenticated } = useAuth()

  const [discoverForm, setDiscoverForm] = useState({
    name: '',
    cuisine: '',
    city: '',
    keyword: '',
  })

  const [featuredRestaurants, setFeaturedRestaurants] = useState([])
  const [isLoadingFeatured, setIsLoadingFeatured] = useState(true)
  const [featuredError, setFeaturedError] = useState('')

  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: 'Hi! Tell me what kind of food or dining experience you want, and I will recommend restaurants for you.',
    },
  ])
  const [chatInput, setChatInput] = useState('')
  const [chatError, setChatError] = useState('')
  const [isChatting, setIsChatting] = useState(false)
  const [recommendations, setRecommendations] = useState([])

  function resetChat() {
    setMessages([
      {
        role: 'assistant',
        content: 'Hi! Tell me what kind of food or dining experience you want, and I will recommend restaurants for you.',
      },
    ])
    setChatInput('')
    setChatError('')
    setRecommendations([])
  }

  useEffect(() => {
    let mounted = true

    async function loadFeaturedRestaurants() {
      try {
        setIsLoadingFeatured(true)
        setFeaturedError('')
        const data = await searchRestaurants({})
        const sorted = [...data].sort((a, b) => {
          if (b.rating !== a.rating) return b.rating - a.rating
          return b.reviewCount - a.reviewCount
        })

        if (mounted) {
          setFeaturedRestaurants(sorted.slice(0, 6))
        }
      } catch (error) {
        if (mounted) {
          setFeaturedError(error?.response?.data?.detail || 'Could not load featured restaurants.')
        }
      } finally {
        if (mounted) {
          setIsLoadingFeatured(false)
        }
      }
    }

    loadFeaturedRestaurants()

    return () => {
      mounted = false
    }
  }, [])

  function handleDiscoverSubmit(event) {
    event.preventDefault()

    const params = new URLSearchParams()

    if (discoverForm.name.trim()) params.set('name', discoverForm.name.trim())
    if (discoverForm.cuisine.trim()) params.set('cuisine', discoverForm.cuisine.trim())
    if (discoverForm.city.trim()) params.set('city', discoverForm.city.trim())
    if (discoverForm.keyword.trim()) params.set('keyword', discoverForm.keyword.trim())

    navigate(`/explore?${params.toString()}`)
  }

  async function sendMessage(customMessage = null) {
    const messageToSend = (customMessage ?? chatInput).trim()
    if (!messageToSend) return

    if (!isAuthenticated) {
      navigate('/login')
      return
    }

    const nextMessages = [...messages, { role: 'user', content: messageToSend }]
    setMessages(nextMessages)
    setChatInput('')
    setChatError('')
    setIsChatting(true)

    try {
      const response = await chatWithAssistant({
        message: messageToSend,
        conversation_history: nextMessages.map((item) => ({
          role: item.role,
          content: item.content,
        })),
      })

      setMessages((prev) => [...prev, { role: 'assistant', content: response.reply }])
      setRecommendations(response.recommendations || [])
    } catch (error) {
      setChatError(error?.response?.data?.detail || 'Assistant is not responding right now.')
    } finally {
      setIsChatting(false)
    }
  }

  const quickPrompts = [
    'Best rated near me',
    'Find dinner tonight',
    'Romantic anniversary dinner',
    'Vegan casual places',
  ]

  return (
    <section className='page'>
      <section className='home-hero'>
        <div className='home-hero-overlay'>
          <span className='eyebrow light'>Yelp Prototype</span>
          <h1>Discover great places to eat near you</h1>
          <p className='lead hero-lead'>
            Search restaurants, read reviews, save favorites, and get AI-powered recommendations.
          </p>

          <form className='hero-search-form' onSubmit={handleDiscoverSubmit}>
            <input
              type='text'
              placeholder='Restaurant name'
              value={discoverForm.name}
              onChange={(event) => setDiscoverForm((prev) => ({ ...prev, name: event.target.value }))}
            />
            <input
              type='text'
              placeholder='Cuisine'
              value={discoverForm.cuisine}
              onChange={(event) => setDiscoverForm((prev) => ({ ...prev, cuisine: event.target.value }))}
            />
            <input
              type='text'
              placeholder='City'
              value={discoverForm.city}
              onChange={(event) => setDiscoverForm((prev) => ({ ...prev, city: event.target.value }))}
            />
            <input
              type='text'
              placeholder='Keyword like wifi, quiet, brunch'
              value={discoverForm.keyword}
              onChange={(event) => setDiscoverForm((prev) => ({ ...prev, keyword: event.target.value }))}
            />
            <button type='submit' className='btn btn-primary'>
              Search
            </button>
          </form>

          <div className='quick-actions'>
            {quickPrompts.map((prompt) => (
              <button key={prompt} type='button' className='chip-button' onClick={() => sendMessage(prompt)}>
                {prompt}
              </button>
            ))}
          </div>
        </div>
      </section>

      <section className='home-main-grid'>
        <div className='home-left-column'>
          <section className='section-block'>
            <div className='section-title-row'>
              <div>
                <h2>Featured Restaurants</h2>
                <p className='muted'>Top picks from your restaurant list.</p>
              </div>
              <Link to='/explore' className='link-accent'>
                View all
              </Link>
            </div>

            {isLoadingFeatured && <p className='muted'>Loading featured restaurants...</p>}
            {featuredError && <p className='error-text'>{featuredError}</p>}

            <div className='card-grid'>
              {!isLoadingFeatured &&
                !featuredError &&
                featuredRestaurants.map((restaurant) => (
                  <HomeRestaurantCard key={restaurant.id} restaurant={restaurant} />
                ))}
            </div>
          </section>
        </div>

        <aside className='home-right-column'>
          <section className='chat-widget'>
            <div className='chat-header-row'>
              <div>
                <h2>Ask the AI Assistant</h2>
                <p className='muted'>
                  Try: “vegan casual dinner in San Jose” or “romantic anniversary dinner”
                </p>
              </div>
              <div className='button-row'>
                {isAuthenticated && (
                  <button type='button' className='btn btn-secondary' onClick={resetChat}>
                    Clear Chat
                  </button>
                )}
                {isAuthenticated ? null : (
                  <Link to='/login' className='btn btn-secondary'>
                    Login
                  </Link>
                )}
              </div>
            </div>

            <div className='chat-window'>
              {messages.map((message, index) => (
                <div key={index} className={`chat-bubble ${message.role}`}>
                  {message.content}
                </div>
              ))}
              {isChatting && <div className='chat-bubble assistant'>Thinking...</div>}
            </div>

            <div className='chat-input-row'>
              <input
                type='text'
                placeholder='Ask for restaurant recommendations...'
                value={chatInput}
                onChange={(event) => setChatInput(event.target.value)}
                onKeyDown={(event) => {
                  if (event.key === 'Enter') {
                    event.preventDefault()
                    sendMessage()
                  }
                }}
              />
              <button type='button' className='btn btn-primary' onClick={() => sendMessage()} disabled={isChatting}>
                Send
              </button>
            </div>

            {chatError && <p className='error-text'>{chatError}</p>}

            {recommendations.length > 0 && (
              <div>
                <h3>Recommendations</h3>
                <div className='chat-recommendations'>
                  {recommendations.map((item) => (
                    <RecommendationCard key={item.id} item={item} />
                  ))}
                </div>
              </div>
            )}
          </section>
        </aside>
      </section>
    </section>
  )
}

export default Home