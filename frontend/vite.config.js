import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

const backendRoutes = [
  '/auth',
  '/restaurants',
  '/reviews',
  '/favorites',
  '/dashboard',
  '/home',
  '/users',
  '/ai-assistant',
  '/protected',
]

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: Object.fromEntries(
      backendRoutes.map((route) => [
        route,
        {
          target: 'http://localhost:8000',
          changeOrigin: true,
        },
      ])
    ),
  },
})
