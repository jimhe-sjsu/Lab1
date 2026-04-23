import { createAsyncThunk, createSlice } from '@reduxjs/toolkit'
import { addFavorite, fetchFavorites, removeFavorite } from '../../api'

const initialState = {
  items: [],
  status: 'idle',
  error: null,
}

export const fetchFavoritesThunk = createAsyncThunk('favourites/fetchAll', async () => fetchFavorites())

export const addFavoriteThunk = createAsyncThunk('favourites/add', async (restaurantId) => {
  await addFavorite(restaurantId)
  return fetchFavorites()
})

export const removeFavoriteThunk = createAsyncThunk('favourites/remove', async (restaurantId) => {
  await removeFavorite(restaurantId)
  return fetchFavorites()
})

const favouritesSlice = createSlice({
  name: 'favourites',
  initialState,
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(fetchFavoritesThunk.pending, (state) => {
        state.status = 'loading'
        state.error = null
      })
      .addCase(fetchFavoritesThunk.fulfilled, (state, action) => {
        state.items = action.payload
        state.status = 'succeeded'
      })
      .addCase(fetchFavoritesThunk.rejected, (state, action) => {
        state.status = 'failed'
        state.error = action.error.message || 'Could not load favourites.'
      })
      .addCase(addFavoriteThunk.fulfilled, (state, action) => {
        state.items = action.payload
        state.status = 'succeeded'
      })
      .addCase(addFavoriteThunk.rejected, (state, action) => {
        state.status = 'failed'
        state.error = action.error.message || 'Could not add favourite.'
      })
      .addCase(removeFavoriteThunk.fulfilled, (state, action) => {
        state.items = action.payload
        state.status = 'succeeded'
      })
      .addCase(removeFavoriteThunk.rejected, (state, action) => {
        state.status = 'failed'
        state.error = action.error.message || 'Could not remove favourite.'
      })
  },
})

export const selectFavouriteItems = (state) => state.favourites.items
export const selectFavouritesStatus = (state) => state.favourites.status
export const selectFavouritesError = (state) => state.favourites.error

export default favouritesSlice.reducer
