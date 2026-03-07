import { useState } from 'react'

function AddRestaurant() {
  const [saved, setSaved] = useState(false)
  const [form, setForm] = useState({
    name: '',
    cuisine: '',
    city: '',
    priceLevel: '$$',
    description: '',
  })

  const handleSubmit = (event) => {
    event.preventDefault()
    setSaved(true)
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

        <label htmlFor='city'>City</label>
        <input id='city' required value={form.city} onChange={(event) => setForm((prev) => ({ ...prev, city: event.target.value }))} />

        <label htmlFor='priceLevel'>Price level</label>
        <select id='priceLevel' value={form.priceLevel} onChange={(event) => setForm((prev) => ({ ...prev, priceLevel: event.target.value }))}>
          <option value='$'>$</option>
          <option value='$$'>$$</option>
          <option value='$$$'>$$$</option>
        </select>

        <label htmlFor='description'>Description</label>
        <textarea
          id='description'
          rows={4}
          value={form.description}
          onChange={(event) => setForm((prev) => ({ ...prev, description: event.target.value }))}
        />

        {saved && <p className='success-text'>Restaurant form submitted (frontend demo).</p>}

        <button className='btn btn-primary' type='submit'>
          Submit Restaurant
        </button>
      </form>
    </section>
  )
}

export default AddRestaurant
