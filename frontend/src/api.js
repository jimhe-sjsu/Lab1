import axios from 'axios'

const TOKEN_KEY = 'lab1_access_token'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '',
  timeout: 10000,
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem(TOKEN_KEY)
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error?.response?.status === 401) {
      localStorage.removeItem(TOKEN_KEY)
      window.dispatchEvent(new CustomEvent('auth:unauthorized'))
    }
    return Promise.reject(error)
  }
)

function normalizeRestaurant(restaurant, extras = {}) {
  if (!restaurant) {
    return null
  }

  const fallbackImageUrl = `https://picsum.photos/seed/lab1-restaurant-${restaurant.id}/1200/800`

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
    imageUrl: restaurant.photo_url || fallbackImageUrl,
  }
}

function normalizeReview(review) {
  return {
    id: review.id,
    rating: Number(review.rating),
    comment: review.comment || '',
    photoUrl: review.photo_url || '',
    author: review.user_id ? `User #${review.user_id}` : 'Anonymous',
    userId: review.user_id,
    createdAt: review.created_at,
    updatedAt: review.updated_at,
  }
}

async function fetchHomeFeed() {
  const { data } = await api.get('/home')
  return data
}

async function fetchRestaurants() {
  const { data } = await api.get('/restaurants/')
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

  const { data } = await api.get('/restaurants/search', { params })
  return data.map((restaurant) => normalizeRestaurant(restaurant))
}

async function fetchRestaurantDetails(restaurantId) {
  const { data } = await api.get(`/restaurants/${restaurantId}`)
  return {
    restaurant: normalizeRestaurant(data.restaurant, {
      averageRating: data.average_rating,
      reviewCount: data.review_count,
    }),
    reviews: (data.reviews || []).map((review) => normalizeReview(review)),
  }
}

async function createRestaurant(payload) {
  const { data } = await api.post('/restaurants/', payload)
  return normalizeRestaurant(data)
}

async function updateRestaurant(restaurantId, payload) {
  const { data } = await api.put(`/restaurants/${restaurantId}`, payload)
  return normalizeRestaurant(data)
}

async function createReview(payload) {
  const { data } = await api.post('/reviews/', payload)
  return normalizeReview(data)
}

async function updateReview(reviewId, payload) {
  const { data } = await api.put(`/reviews/${reviewId}`, payload)
  return normalizeReview(data)
}

async function deleteReview(reviewId) {
  const { data } = await api.delete(`/reviews/${reviewId}`)
  return data
}

async function fetchFavorites() {
  const [{ data: favorites }, { data: restaurants }] = await Promise.all([api.get('/favorites/'), api.get('/restaurants/')])

  const restaurantMap = new Map(restaurants.map((restaurant) => [restaurant.id, restaurant]))

  return favorites
    .map((favorite) => normalizeRestaurant(restaurantMap.get(favorite.restaurant_id)))
    .filter(Boolean)
}

async function addFavorite(restaurantId) {
  const { data } = await api.post(`/favorites/${restaurantId}`)
  return data
}

async function removeFavorite(restaurantId) {
  const { data } = await api.delete(`/favorites/${restaurantId}`)
  return data
}

async function fetchDashboardSummary() {
  const { data } = await api.get('/dashboard/user')
  return data
}

async function fetchCurrentUser() {
  const { data } = await api.get('/users/me')
  return data
}

async function updateCurrentUser(payload) {
  const { data } = await api.put('/users/me', payload)
  return data
}

async function fetchPreferences() {
  const { data } = await api.get('/users/me/preferences')
  return data
}

async function updatePreferences(payload) {
  const { data } = await api.put('/users/me/preferences', payload)
  return data
}

async function fetchUserHistory() {
  const { data } = await api.get('/users/me/history')
  return data
}

async function claimRestaurant(restaurantId) {
  const { data } = await api.post(`/restaurants/${restaurantId}/claim`)
  return data
}

async function fetchRestaurantOwnerDashboard(restaurantId) {
  const { data } = await api.get(`/restaurants/${restaurantId}/dashboard`)
  return data
}

async function chatWithAssistant(payload) {
  const { data } = await api.post('/ai-assistant/chat', payload)
  return data
}

export {
  TOKEN_KEY,
  addFavorite,
  chatWithAssistant,
  claimRestaurant,
  createRestaurant,
  createReview,
  deleteReview,
  fetchCurrentUser,
  fetchDashboardSummary,
  fetchFavorites,
  fetchHomeFeed,
  fetchPreferences,
  fetchRestaurantDetails,
  fetchRestaurantOwnerDashboard,
  fetchRestaurants,
  fetchUserHistory,
  normalizeRestaurant,
  removeFavorite,
  searchRestaurants,
  updateCurrentUser,
  updatePreferences,
  updateRestaurant,
  updateReview,
}

export default api
