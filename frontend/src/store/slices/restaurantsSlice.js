import { createAsyncThunk, createSlice } from '@reduxjs/toolkit'
import { createRestaurant, fetchRestaurantDetails, fetchRestaurants, searchRestaurants, updateRestaurant } from '../../api'

const initialState = {
  items: [],
  detailById: {},
  status: 'idle',
  error: null,
}

export const fetchRestaurantsThunk = createAsyncThunk('restaurants/fetchAll', async () => fetchRestaurants())

export const searchRestaurantsThunk = createAsyncThunk('restaurants/search', async (filters) => searchRestaurants(filters))

export const fetchRestaurantDetailsThunk = createAsyncThunk('restaurants/fetchDetails', async (restaurantId) => {
  const data = await fetchRestaurantDetails(restaurantId)
  return { restaurantId: Number(restaurantId), ...data }
})

export const createRestaurantThunk = createAsyncThunk('restaurants/create', async (payload) => createRestaurant(payload))

export const updateRestaurantThunk = createAsyncThunk('restaurants/update', async ({ restaurantId, payload }) => {
  const restaurant = await updateRestaurant(restaurantId, payload)
  return { restaurantId: Number(restaurantId), restaurant }
})

const restaurantsSlice = createSlice({
  name: 'restaurants',
  initialState,
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(fetchRestaurantsThunk.pending, (state) => {
        state.status = 'loading'
        state.error = null
      })
      .addCase(fetchRestaurantsThunk.fulfilled, (state, action) => {
        state.items = action.payload
        state.status = 'succeeded'
      })
      .addCase(fetchRestaurantsThunk.rejected, (state, action) => {
        state.status = 'failed'
        state.error = action.error.message || 'Could not load restaurants.'
      })
      .addCase(searchRestaurantsThunk.pending, (state) => {
        state.status = 'loading'
        state.error = null
      })
      .addCase(searchRestaurantsThunk.fulfilled, (state, action) => {
        state.items = action.payload
        state.status = 'succeeded'
      })
      .addCase(searchRestaurantsThunk.rejected, (state, action) => {
        state.status = 'failed'
        state.error = action.error.message || 'Could not search restaurants.'
      })
      .addCase(fetchRestaurantDetailsThunk.pending, (state) => {
        state.status = 'loading'
        state.error = null
      })
      .addCase(fetchRestaurantDetailsThunk.fulfilled, (state, action) => {
        state.detailById[action.payload.restaurantId] = action.payload.restaurant
        state.status = 'succeeded'
      })
      .addCase(fetchRestaurantDetailsThunk.rejected, (state, action) => {
        state.status = 'failed'
        state.error = action.error.message || 'Could not load restaurant details.'
      })
      .addCase(createRestaurantThunk.fulfilled, (state, action) => {
        state.items.unshift(action.payload)
      })
      .addCase(updateRestaurantThunk.fulfilled, (state, action) => {
        state.detailById[action.payload.restaurantId] = action.payload.restaurant
        state.items = state.items.map((restaurant) =>
          restaurant.id === action.payload.restaurantId ? action.payload.restaurant : restaurant
        )
      })
  },
})

export const selectRestaurantList = (state) => state.restaurants.items
export const selectRestaurantsStatus = (state) => state.restaurants.status
export const selectRestaurantsError = (state) => state.restaurants.error
export const selectRestaurantDetail = (restaurantId) => (state) => state.restaurants.detailById[Number(restaurantId)] || null

export default restaurantsSlice.reducer
