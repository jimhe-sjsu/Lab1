export const restaurants = [
  {
    id: 'r1',
    name: 'Golden Curry House',
    cuisine: 'Indian',
    city: 'San Jose',
    priceLevel: '$$',
    rating: 4.7,
    imageUrl:
      'https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?auto=format&fit=crop&w=1200&q=80',
    tags: ['Spicy', 'Family Friendly', 'Takeout'],
    description: 'Known for rich curries, naan, and fast service near downtown.',
    reviews: [
      { id: 'rv1', author: 'Alice', rating: 5, comment: 'Butter chicken was excellent and portions were big.' },
      { id: 'rv2', author: 'Mark', rating: 4, comment: 'Great flavors, but peak-hour wait can be long.' },
    ],
  },
  {
    id: 'r2',
    name: 'Pacific Ramen Bar',
    cuisine: 'Japanese',
    city: 'Santa Clara',
    priceLevel: '$$',
    rating: 4.5,
    imageUrl:
      'https://images.unsplash.com/photo-1557872943-16a5ac26437e?auto=format&fit=crop&w=1200&q=80',
    tags: ['Late Night', 'Noodles', 'Cozy'],
    description: 'Tonkotsu broth, vegetarian options, and quick bar seating.',
    reviews: [
      { id: 'rv3', author: 'Nina', rating: 5, comment: 'Broth was deep and flavorful.' },
      { id: 'rv4', author: 'Leo', rating: 4, comment: 'Solid ramen and friendly staff.' },
    ],
  },
  {
    id: 'r3',
    name: 'Sunset Tacos',
    cuisine: 'Mexican',
    city: 'Campbell',
    priceLevel: '$',
    rating: 4.3,
    imageUrl:
      'https://images.unsplash.com/photo-1551504734-5ee1c4a1479b?auto=format&fit=crop&w=1200&q=80',
    tags: ['Street Food', 'Budget', 'Outdoor Seating'],
    description: 'Casual taco spot popular for fish tacos and house salsa.',
    reviews: [
      { id: 'rv5', author: 'Sara', rating: 4, comment: 'Fresh tortillas and fast service.' },
      { id: 'rv6', author: 'Jason', rating: 5, comment: 'Great value and flavor combo.' },
    ],
  },
  {
    id: 'r4',
    name: 'Harvest Bowl Kitchen',
    cuisine: 'Healthy',
    city: 'Sunnyvale',
    priceLevel: '$$',
    rating: 4.6,
    imageUrl:
      'https://images.unsplash.com/photo-1466978913421-dad2ebd01d17?auto=format&fit=crop&w=1200&q=80',
    tags: ['Vegan', 'Gluten-Free', 'Lunch'],
    description: 'Build-your-own bowls with seasonal produce and grain options.',
    reviews: [
      { id: 'rv7', author: 'Priya', rating: 5, comment: 'Great for clean eating and quick lunch.' },
      { id: 'rv8', author: 'Matt', rating: 4, comment: 'Good ingredients and plenty of choices.' },
    ],
  },
]

export const favoriteRestaurantIds = ['r1', 'r4']

export const recentlyViewed = [
  { id: 'r2', viewedAt: '2026-03-02T16:30:00Z' },
  { id: 'r1', viewedAt: '2026-03-02T14:15:00Z' },
  { id: 'r3', viewedAt: '2026-03-01T20:05:00Z' },
]

export function findRestaurantById(id) {
  return restaurants.find((restaurant) => restaurant.id === id)
}
