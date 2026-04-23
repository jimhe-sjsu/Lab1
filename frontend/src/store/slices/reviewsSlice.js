import { createAction, createAsyncThunk, createSlice } from '@reduxjs/toolkit'
import {
  awaitReviewJobCompletion,
  fetchReviewsForRestaurant,
  submitCreateReviewJob,
  submitDeleteReviewJob,
  submitUpdateReviewJob,
} from '../../api'

export const reviewJobStatusReceived = createAction('reviews/jobStatusReceived')

const initialState = {
  byRestaurant: {},
  jobs: {},
  status: 'idle',
  error: null,
}

export const fetchReviewsThunk = createAsyncThunk('reviews/fetchByRestaurant', async (restaurantId) => {
  const reviews = await fetchReviewsForRestaurant(restaurantId)
  return { restaurantId: Number(restaurantId), reviews }
})

export const createReviewThunk = createAsyncThunk('reviews/create', async (payload, thunkAPI) => {
  const job = await submitCreateReviewJob(payload)
  thunkAPI.dispatch(reviewJobStatusReceived(job))
  const finalJob = await awaitReviewJobCompletion(job.job_id)
  thunkAPI.dispatch(reviewJobStatusReceived(finalJob))
  if (finalJob.status !== 'completed') {
    throw new Error(finalJob.error || 'Could not submit review.')
  }
  const reviews = await fetchReviewsForRestaurant(payload.restaurant_id)
  return { restaurantId: Number(payload.restaurant_id), reviews, job: finalJob }
})

export const updateReviewThunk = createAsyncThunk('reviews/update', async ({ reviewId, payload, restaurantId }, thunkAPI) => {
  const job = await submitUpdateReviewJob(reviewId, payload)
  thunkAPI.dispatch(reviewJobStatusReceived(job))
  const finalJob = await awaitReviewJobCompletion(job.job_id)
  thunkAPI.dispatch(reviewJobStatusReceived(finalJob))
  if (finalJob.status !== 'completed') {
    throw new Error(finalJob.error || 'Could not update review.')
  }
  const reviews = await fetchReviewsForRestaurant(restaurantId)
  return { restaurantId: Number(restaurantId), reviews, job: finalJob }
})

export const deleteReviewThunk = createAsyncThunk('reviews/delete', async ({ reviewId, restaurantId }, thunkAPI) => {
  const job = await submitDeleteReviewJob(reviewId)
  thunkAPI.dispatch(reviewJobStatusReceived(job))
  const finalJob = await awaitReviewJobCompletion(job.job_id)
  thunkAPI.dispatch(reviewJobStatusReceived(finalJob))
  if (finalJob.status !== 'completed') {
    throw new Error(finalJob.error || 'Could not delete review.')
  }
  const reviews = await fetchReviewsForRestaurant(restaurantId)
  return { restaurantId: Number(restaurantId), reviews, job: finalJob }
})

const reviewsSlice = createSlice({
  name: 'reviews',
  initialState,
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(fetchReviewsThunk.pending, (state) => {
        state.status = 'loading'
        state.error = null
      })
      .addCase(fetchReviewsThunk.fulfilled, (state, action) => {
        state.byRestaurant[action.payload.restaurantId] = action.payload.reviews
        state.status = 'succeeded'
      })
      .addCase(fetchReviewsThunk.rejected, (state, action) => {
        state.status = 'failed'
        state.error = action.error.message || 'Could not load reviews.'
      })
      .addCase(createReviewThunk.pending, (state) => {
        state.status = 'loading'
        state.error = null
      })
      .addCase(createReviewThunk.fulfilled, (state, action) => {
        state.byRestaurant[action.payload.restaurantId] = action.payload.reviews
        state.jobs[action.payload.job.job_id] = action.payload.job
        state.status = 'succeeded'
      })
      .addCase(createReviewThunk.rejected, (state, action) => {
        state.status = 'failed'
        state.error = action.error.message || 'Could not create review.'
      })
      .addCase(updateReviewThunk.fulfilled, (state, action) => {
        state.byRestaurant[action.payload.restaurantId] = action.payload.reviews
        state.jobs[action.payload.job.job_id] = action.payload.job
        state.status = 'succeeded'
      })
      .addCase(updateReviewThunk.rejected, (state, action) => {
        state.status = 'failed'
        state.error = action.error.message || 'Could not update review.'
      })
      .addCase(deleteReviewThunk.fulfilled, (state, action) => {
        state.byRestaurant[action.payload.restaurantId] = action.payload.reviews
        state.jobs[action.payload.job.job_id] = action.payload.job
        state.status = 'succeeded'
      })
      .addCase(deleteReviewThunk.rejected, (state, action) => {
        state.status = 'failed'
        state.error = action.error.message || 'Could not delete review.'
      })
      .addCase(reviewJobStatusReceived, (state, action) => {
        state.jobs[action.payload.job_id] = action.payload
      })
  },
})

export const selectReviewsByRestaurant = (restaurantId) => (state) => state.reviews.byRestaurant[Number(restaurantId)] || []
export const selectReviewJobs = (state) => state.reviews.jobs
export const selectReviewsStatus = (state) => state.reviews.status
export const selectReviewsError = (state) => state.reviews.error

export default reviewsSlice.reducer
