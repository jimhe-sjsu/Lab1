import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { chatWithAssistant, fetchHomeFeed } from '../api'
import { useAuth } from '../auth'

function HomeList({ title, items, renderDescription }) {
  return (
    <section className='list-panel'>
      <h2>{title}</h2>
      <div className='list-stack'>
        {items.map((item) => (
          <Link key={`${title}-${item.id}`} className='list-item' to={`/restaurants/${item.id}`}>
            <strong>{item.name}</strong>
            <span className='muted'>{renderDescription(item)}</span>
          </Link>
        ))}
      </div>
    </section>
  )
}

function ChatAssistant() {
  const { isAuthenticated } = useAuth()
  const [input, setInput] = useState('')
  const [messages, setMessages] = useState([])
  const [recommendations, setRecommendations] = useState([])
  const [isThinking, setIsThinking] = useState(false)
  const [error, setError] = useState('')

  async function handleSend(event) {
    event.preventDefault()
    if (!isAuthenticated) {
      setError('Login is required to use the AI assistant.')
      return
    }
    if (!input.trim()) {
      return
    }

    const userMessage = { role: 'user', content: input.trim() }
    const nextMessages = [...messages, userMessage]

    setMessages(nextMessages)
    setInput('')
    setError('')
    setIsThinking(true)

    try {
      const response = await chatWithAssistant({
        message: userMessage.content,
        conversation_history: nextMessages,
      })

      setMessages((prev) => [...prev, { role: 'assistant', content: response.reply }])
      setRecommendations(response.recommendations || [])
    } catch (requestError) {
      setError(requestError?.response?.data?.detail || 'AI assistant is unavailable right now.')
    } finally {
      setIsThinking(false)
    }
  }

  return (
    <section className='chat-widget'>
      <div className='chat-header-row'>
        <h2>AI Assistant</h2>
        <button type='button' className='btn btn-secondary' onClick={() => { setMessages([]); setRecommendations([]); setError('') }}>
          Clear
        </button>
      </div>

      <div className='chat-window'>
        {messages.length === 0 ? <p className='muted'>Ask for personalized restaurant recommendations.</p> : null}
        {messages.map((message, index) => (
          <div key={`${message.role}-${index}`} className={message.role === 'assistant' ? 'chat-bubble assistant' : 'chat-bubble user'}>
            {message.content}
          </div>
        ))}
        {isThinking ? <p className='muted'>Assistant is thinking...</p> : null}
      </div>

      {recommendations.length > 0 ? (
        <div className='chat-recommendations'>
          {recommendations.map((item) => (
            <Link className='recommendation-card' key={item.id} to={`/restaurants/${item.id}`}>
              <strong>{item.name}</strong>
              <span className='muted'>
                {item.cuisine} • {item.price_tier} • {item.average_rating.toFixed(1)} ({item.review_count})
              </span>
              <span className='muted'>{item.reason}</span>
            </Link>
          ))}
        </div>
      ) : null}

      {error && <p className='error-text'>{error}</p>}

      <form className='chat-input-row' onSubmit={handleSend}>
        <input
          value={input}
          onChange={(event) => setInput(event.target.value)}
          placeholder='e.g. Romantic dinner near 95112'
          disabled={!isAuthenticated}
        />
        <button className='btn btn-primary' type='submit' disabled={isThinking}>
          Send
        </button>
      </form>
    </section>
  )
}

function Home() {
  const [feed, setFeed] = useState({ top_rated: [], most_reviewed: [], recent_restaurants: [] })
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let isMounted = true

    async function loadHomeFeed() {
      try {
        setIsLoading(true)
        const data = await fetchHomeFeed()
        if (isMounted) {
          setFeed(data)
        }
      } catch (requestError) {
        if (isMounted) {
          setError(requestError?.response?.data?.detail || 'Could not load home feed.')
        }
      } finally {
        if (isMounted) {
          setIsLoading(false)
        }
      }
    }

    loadHomeFeed()
    return () => {
      isMounted = false
    }
  }, [])

  return (
    <section className='page'>
      <section className='hero-page'>
        <p className='eyebrow'>DATA236 Lab 1</p>
        <h1>Discover restaurants, save favorites, and write reviews.</h1>
        <p className='lead'>Use the AI assistant for personalized recommendations, then open cards to inspect full details.</p>
        <div className='hero-actions'>
          <Link className='btn btn-primary' to='/explore'>
            Explore Restaurants
          </Link>
          <Link className='btn btn-secondary' to='/signup'>
            Create Account
          </Link>
        </div>
      </section>

      <ChatAssistant />

      {isLoading && <p className='muted'>Loading home feed...</p>}
      {error && <p className='error-text'>{error}</p>}

      {!isLoading && !error && (
        <div className='three-column-grid'>
          <HomeList
            title='Top Rated'
            items={feed.top_rated}
            renderDescription={(item) => `Average rating: ${Number(item.average_rating).toFixed(1)}`}
          />
          <HomeList title='Most Reviewed' items={feed.most_reviewed} renderDescription={(item) => `Reviews: ${item.review_count}`} />
          <HomeList
            title='Recently Added'
            items={feed.recent_restaurants}
            renderDescription={(item) => `${item.city} • ${item.price_tier || '$$'}`}
          />
        </div>
      )}
    </section>
  )
}

export default Home
