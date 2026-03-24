import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { createRestaurant, uploadImage } from '../api'

function AddRestaurant() {
  const navigate = useNavigate()
  const [form, setForm] = useState({
    name: '',
    cuisine: '',
    address: '',
    city: '',
    state: '',
    zipCode: '',
    priceLevel: '$$',
    description: '',
    contactPhone: '',
    hoursText: '',
    photoUrl: '',
    amenitiesText: '',
  })
  const [photoFile, setPhotoFile] = useState(null)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (event) => {
    event.preventDefault()
    setError('')
    setIsSubmitting(true)

    try {
      let uploadedPhotoUrl = form.photoUrl
      if (photoFile) {
        const upload = await uploadImage(photoFile)
        uploadedPhotoUrl = upload.url
      }

      const created = await createRestaurant({
        name: form.name,
        cuisine_type: form.cuisine,
        address: form.address,
        city: form.city,
        state: form.state,
        zip_code: form.zipCode,
        description: form.description,
        price_tier: form.priceLevel,
        contact_phone: form.contactPhone,
        hours_text: form.hoursText,
        photo_url: uploadedPhotoUrl,
        amenities_text: form.amenitiesText,
      })
      navigate(`/restaurants/${created.id}`)
    } catch (requestError) {
      setError(requestError?.response?.data?.detail || 'Could not create restaurant.')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <section className='page'>
      <h1>Add Restaurant</h1>
      <p className='muted'>Submit a new restaurant listing to the platform.</p>

      <form className='form-card' onSubmit={handleSubmit}>
        <label htmlFor='name'>Restaurant name</label>
        <input id='name' required value={form.name} onChange={(event) => setForm((prev) => ({ ...prev, name: event.target.value }))} />

        <label htmlFor='cuisine'>Cuisine</label>
        <input id='cuisine' required value={form.cuisine} onChange={(event) => setForm((prev) => ({ ...prev, cuisine: event.target.value }))} />

        <label htmlFor='address'>Address</label>
        <input id='address' required value={form.address} onChange={(event) => setForm((prev) => ({ ...prev, address: event.target.value }))} />

        <div className='split-grid'>
          <label htmlFor='city'>
            City
            <input id='city' required value={form.city} onChange={(event) => setForm((prev) => ({ ...prev, city: event.target.value }))} />
          </label>

          <label htmlFor='state'>
            State
            <input id='state' required value={form.state} onChange={(event) => setForm((prev) => ({ ...prev, state: event.target.value }))} />
          </label>
        </div>

        <label htmlFor='zipCode'>ZIP code</label>
        <input id='zipCode' required value={form.zipCode} onChange={(event) => setForm((prev) => ({ ...prev, zipCode: event.target.value }))} />

        <label htmlFor='priceLevel'>Price tier</label>
        <select id='priceLevel' value={form.priceLevel} onChange={(event) => setForm((prev) => ({ ...prev, priceLevel: event.target.value }))}>
          <option value='$'>$</option>
          <option value='$$'>$$</option>
          <option value='$$$'>$$$</option>
          <option value='$$$$'>$$$$</option>
        </select>

        <label htmlFor='contactPhone'>Contact phone (optional)</label>
        <input id='contactPhone' value={form.contactPhone} onChange={(event) => setForm((prev) => ({ ...prev, contactPhone: event.target.value }))} />

        <label htmlFor='hoursText'>Hours (optional)</label>
        <input id='hoursText' value={form.hoursText} onChange={(event) => setForm((prev) => ({ ...prev, hoursText: event.target.value }))} />

        <label htmlFor='photoUrl'>Photo URL (optional)</label>
        <input id='photoUrl' value={form.photoUrl} onChange={(event) => setForm((prev) => ({ ...prev, photoUrl: event.target.value }))} />

        <label htmlFor='photoFile'>Upload restaurant photo</label>
        <input id='photoFile' type='file' accept='image/*' onChange={(event) => setPhotoFile(event.target.files?.[0] || null)} />

        <label htmlFor='amenitiesText'>Amenities (optional keywords)</label>
        <input id='amenitiesText' value={form.amenitiesText} onChange={(event) => setForm((prev) => ({ ...prev, amenitiesText: event.target.value }))} />

        <label htmlFor='description'>Description</label>
        <textarea id='description' rows={4} value={form.description} onChange={(event) => setForm((prev) => ({ ...prev, description: event.target.value }))} />

        {error && <p className='error-text'>{error}</p>}

        <button className='btn btn-primary' type='submit' disabled={isSubmitting}>
          {isSubmitting ? 'Submitting...' : 'Submit Restaurant'}
        </button>
      </form>
    </section>
  )
}

export default AddRestaurant
