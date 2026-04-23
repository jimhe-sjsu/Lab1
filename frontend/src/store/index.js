import { configureStore } from '@reduxjs/toolkit'
import authReducer from './slices/authSlice'
import favouritesReducer from './slices/favouritesSlice'
import restaurantsReducer from './slices/restaurantsSlice'
import reviewsReducer from './slices/reviewsSlice'

export const store = configureStore({
  reducer: {
    auth: authReducer,
    restaurants: restaurantsReducer,
    reviews: reviewsReducer,
    favourites: favouritesReducer,
  },
})
