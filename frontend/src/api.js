import axios from 'axios'

const AUTH_STATE_KEY = 'lab2_auth_state'
const TOKEN_KEY = 'lab2_access_token'

const USER_API_BASE = import.meta.env.VITE_USER_API_BASE || '/api/user'
const OWNER_API_BASE = import.meta.env.VITE_OWNER_API_BASE || '/api/owner'
const RESTAURANT_API_BASE = import.meta.env.VITE_RESTAURANT_API_BASE || '/api/restaurant'
const REVIEW_API_BASE = import.meta.env.VITE_REVIEW_API_BASE || '/api/review'

function loadPersistedAuthState() {
  try {
    const cached = localStorage.getItem(AUTH_STATE_KEY)
    return cached ? JSON.parse(cached) : null
  } catch {
    return null
  }
}

function persistAuthState(authState) {
  localStorage.setItem(AUTH_STATE_KEY, JSON.stringify(authState))
  if (authState?.token) {
    localStorage.setItem(TOKEN_KEY, authState.token)
  } else {
    localStorage.removeItem(TOKEN_KEY)
  }
}

function clearPersistedAuthState() {
  localStorage.removeItem(AUTH_STATE_KEY)
  localStorage.removeItem(TOKEN_KEY)
}

function getStoredRole() {
  return loadPersistedAuthState()?.user?.role || 'USER'
}

function getToken(tokenOverride) {
  return tokenOverride || localStorage.getItem(TOKEN_KEY)
}

function withAuthHeaders(tokenOverride, config = {}) {
  const token = getToken(tokenOverride)
  return {
    ...config,
    headers: {
      ...(config.headers || {}),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
  }
}

function createClient(baseURL) {
  const client = axios.create({
    baseURL,
    timeout: 15000,
  })

  client.interceptors.request.use((config) => {
    const token = localStorage.getItem(TOKEN_KEY)
    if (token) {
      config.headers = config.headers || {}
      if (!config.headers.Authorization) {
        config.headers.Authorization = `Bearer ${token}`
      }
    }
    return config
  })

  client.interceptors.response.use(
    (response) => response,
    (error) => {
      if (error?.response?.status === 401) {
        clearPersistedAuthState()
        window.dispatchEvent(new CustomEvent('auth:unauthorized'))
      }
      return Promise.reject(error)
    }
  )

  return client
}

const userApi = createClient(USER_API_BASE)
const ownerApi = createClient(OWNER_API_BASE)
const restaurantApi = createClient(RESTAURANT_API_BASE)
const reviewApi = createClient(REVIEW_API_BASE)

function getProfileClient(role = getStoredRole()) {
  return role === 'OWNER' ? ownerApi : userApi
}

function resolveAssetUrl(value) {
  if (!value) {
    return ''
  }

  if (/^https?:\/\//i.test(value) || value.startsWith('data:') || value.startsWith('/api/')) {
    return value
  }

  if (value.startsWith('/uploads/')) {
    return `${USER_API_BASE}${value}`
  }

  return value
}

function normalizeRestaurant(restaurant, extras = {}) {
  if (!restaurant) {
    return null
  }

  const fallbackImageUrl = `https://picsum.photos/seed/lab2-restaurant-${restaurant.id}/1200/800`

  return {
    id: restaurant.id,
    name: restaurant.name,
    cuisine: restaurant.cuisine_type,
    city: restaurant.city,
    state: restaurant.state,
    address: restaurant.address,
    zipCode: restaurant.zip_code,
    priceLevel: restaurant.price_tier || '$$',
    description: restaurant.description || 'No description provided.',
    rating: Number(extras.averageRating ?? extras.average_rating ?? restaurant.average_rating ?? 0),
    reviewCount: Number(extras.reviewCount ?? extras.review_count ?? restaurant.review_count ?? 0),
    ownerId: restaurant.owner_id,
    createdBy: restaurant.created_by,
    contactPhone: restaurant.contact_phone || '',
    hoursText: restaurant.hours_text || '',
    amenitiesText: restaurant.amenities_text || '',
    photoUrl: resolveAssetUrl(restaurant.photo_url),
    imageUrl: resolveAssetUrl(restaurant.photo_url) || fallbackImageUrl,
    viewCount: Number(restaurant.view_count ?? 0),
  }
}

function normalizeReview(review) {
  return {
    id: review.id,
    rating: Number(review.rating),
    comment: review.comment || '',
    photoUrl: resolveAssetUrl(review.photo_url),
    author: review.reviewer_name || (review.user_id ? `User #${review.user_id}` : 'Anonymous'),
    userId: review.user_id,
    createdAt: review.created_at,
    updatedAt: review.updated_at,
  }
}

async function loginReviewer({ email, password }) {
  const payload = new URLSearchParams()
  payload.set('username', email)
  payload.set('password', password)
  const { data } = await userApi.post('/auth/login', payload, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  })
  return data
}

async function loginOwner({ email, password }) {
  const payload = new URLSearchParams()
  payload.set('username', email)
  payload.set('password', password)
  const { data } = await ownerApi.post('/auth/login', payload, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  })
  return data
}

async function signupReviewer({ fullName, email, password }) {
  const { data } = await userApi.post('/auth/signup', {
    name: fullName,
    email,
    password,
    role: 'USER',
  })
  return data
}

async function signupOwner({ fullName, email, password, restaurantLocation }) {
  const { data } = await ownerApi.post('/auth/signup', {
    name: fullName,
    email,
    password,
    role: 'OWNER',
    restaurant_location: restaurantLocation?.trim() || null,
  })
  return data
}

async function logoutForRole(role, tokenOverride) {
  const client = role === 'OWNER' ? ownerApi : userApi
  const { data } = await client.post('/auth/logout', null, withAuthHeaders(tokenOverride))
  return data
}

async function fetchCurrentUserForRole(role, tokenOverride) {
  const client = role === 'OWNER' ? ownerApi : userApi
  const { data } = await client.get('/users/me', withAuthHeaders(tokenOverride))
  return data
}

async function fetchReviewerDashboard(tokenOverride) {
  const { data } = await userApi.get('/dashboard/user', withAuthHeaders(tokenOverride))
  return data
}

async function fetchHomeFeed() {
  const data = await searchRestaurants({})
  return {
    top_rated: data.slice(0, 5),
    most_reviewed: [...data].sort((a, b) => b.reviewCount - a.reviewCount).slice(0, 5),
    recent_restaurants: data.slice(0, 5),
  }
}

async function fetchRestaurants() {
  const { data } = await restaurantApi.get('/restaurants/')
  return data.map((restaurant) => normalizeRestaurant(restaurant))
}

async function searchRestaurants(filters = {}) {
  const params = {}

  if (filters.name) params.name = filters.name
  if (filters.cuisine && filters.cuisine !== 'All') params.cuisine = filters.cuisine
  if (filters.city) params.city = filters.city
  if (filters.zipCode) params.zip_code = filters.zipCode
  if (filters.keyword) params.keyword = filters.keyword
  if (filters.priceTier && filters.priceTier !== 'Any') params.price_tier = filters.priceTier

  const { data } = await restaurantApi.get('/restaurants/search', { params })
  return data.map((restaurant) => normalizeRestaurant(restaurant))
}

async function fetchRestaurantDetails(restaurantId) {
  const { data } = await restaurantApi.get(`/restaurants/${restaurantId}`)
  return {
    restaurant: normalizeRestaurant(data.restaurant, {
      averageRating: data.average_rating,
      reviewCount: data.review_count,
    }),
    reviews: (data.reviews || []).map((review) => normalizeReview(review)),
  }
}

async function fetchReviewsForRestaurant(restaurantId) {
  const { data } = await reviewApi.get(`/reviews/restaurant/${restaurantId}`)
  return (data || []).map((review) => normalizeReview(review))
}

async function createRestaurant(payload) {
  const { data } = await restaurantApi.post('/restaurants/', payload)
  return normalizeRestaurant(data)
}

async function updateRestaurant(restaurantId, payload) {
  const { data } = await restaurantApi.put(`/restaurants/${restaurantId}`, payload)
  return normalizeRestaurant(data)
}

async function submitCreateReviewJob(payload) {
  const { data } = await reviewApi.post('/reviews/', payload)
  return data
}

async function submitUpdateReviewJob(reviewId, payload) {
  const { data } = await reviewApi.put(`/reviews/${reviewId}`, payload)
  return data
}

async function submitDeleteReviewJob(reviewId) {
  const { data } = await reviewApi.delete(`/reviews/${reviewId}`)
  return data
}

async function fetchReviewJobStatus(jobId) {
  const { data } = await reviewApi.get(`/review-jobs/${jobId}`)
  return data
}

async function awaitReviewJobCompletion(jobId, { timeoutMs = 60000, intervalMs = 1000 } = {}) {
  const deadline = Date.now() + timeoutMs
  while (Date.now() < deadline) {
    const status = await fetchReviewJobStatus(jobId)
    if (status.status === 'completed' || status.status === 'failed') {
      return status
    }
    await new Promise((resolve) => window.setTimeout(resolve, intervalMs))
  }
  throw new Error('Timed out waiting for review processing.')
}

async function fetchFavorites() {
  const [{ data: favorites }, restaurants] = await Promise.all([userApi.get('/favorites/'), fetchRestaurants()])
  const restaurantMap = new Map(restaurants.map((restaurant) => [restaurant.id, restaurant]))
  return favorites.map((favorite) => restaurantMap.get(favorite.restaurant_id)).filter(Boolean)
}

async function addFavorite(restaurantId) {
  const { data } = await userApi.post(`/favorites/${restaurantId}`)
  return data
}

async function removeFavorite(restaurantId) {
  const { data } = await userApi.delete(`/favorites/${restaurantId}`)
  return data
}

async function fetchDashboardSummary() {
  return fetchReviewerDashboard()
}

async function fetchCurrentUser() {
  return fetchCurrentUserForRole(getStoredRole())
}

async function updateCurrentUser(payload) {
  const client = getProfileClient()
  const { data } = await client.put('/users/me', payload)
  return data
}

async function fetchPreferences() {
  const { data } = await userApi.get('/users/me/preferences')
  return data
}

async function updatePreferences(payload) {
  const { data } = await userApi.put('/users/me/preferences', payload)
  return data
}

async function fetchUserHistory() {
  const { data } = await userApi.get('/users/me/history')
  return data
}

async function claimRestaurant(restaurantId) {
  const { data } = await ownerApi.post(`/restaurants/${restaurantId}/claim`)
  return data
}

async function fetchRestaurantOwnerDashboard(restaurantId) {
  const { data } = await ownerApi.get(`/restaurants/${restaurantId}/dashboard`)
  return data
}

async function chatWithAssistant(payload) {
  const { data } = await userApi.post('/ai-assistant/chat', payload)
  return data
}

async function uploadImage(file) {
  const formData = new FormData()
  formData.append('file', file)
  const { data } = await userApi.post('/uploads/image', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return data
}

export {
  AUTH_STATE_KEY,
  OWNER_API_BASE,
  RESTAURANT_API_BASE,
  REVIEW_API_BASE,
  TOKEN_KEY,
  USER_API_BASE,
  addFavorite,
  awaitReviewJobCompletion,
  chatWithAssistant,
  claimRestaurant,
  clearPersistedAuthState,
  createRestaurant,
  fetchCurrentUser,
  fetchCurrentUserForRole,
  fetchDashboardSummary,
  fetchFavorites,
  fetchHomeFeed,
  fetchPreferences,
  fetchRestaurantDetails,
  fetchRestaurantOwnerDashboard,
  fetchRestaurants,
  fetchReviewerDashboard,
  fetchReviewJobStatus,
  fetchReviewsForRestaurant,
  fetchUserHistory,
  loadPersistedAuthState,
  loginOwner,
  loginReviewer,
  logoutForRole,
  normalizeRestaurant,
  normalizeReview,
  persistAuthState,
  removeFavorite,
  resolveAssetUrl,
  searchRestaurants,
  signupOwner,
  signupReviewer,
  submitCreateReviewJob,
  submitDeleteReviewJob,
  submitUpdateReviewJob,
  updateCurrentUser,
  updatePreferences,
  updateRestaurant,
  uploadImage,
}

export default restaurantApi
