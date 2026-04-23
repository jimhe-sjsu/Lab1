import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api/user': {
        target: 'http://localhost:8001',
        changeOrigin: true,
      },
      '/api/owner': {
        target: 'http://localhost:8002',
        changeOrigin: true,
      },
      '/api/restaurant': {
        target: 'http://localhost:8003',
        changeOrigin: true,
      },
      '/api/review': {
        target: 'http://localhost:8004',
        changeOrigin: true,
      },
    },
  },
})
