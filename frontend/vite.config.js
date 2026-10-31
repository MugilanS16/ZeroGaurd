import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  build: {
    outDir: 'dist',
  },
  server: {
    proxy: {
      '/api': 'http://localhost:5000',
      '/login': 'http://localhost:5000',
      '/register': 'http://localhost:5000',
      '/dashboard': 'http://localhost:5000',
      '/report': 'http://localhost:5000',
      '/admin': 'http://localhost:5000',
      '/chatbot': 'http://localhost:5000',
      '/tracker': 'http://localhost:5000',
      '/awareness': 'http://localhost:5000',
      '/fraud-checker': 'http://localhost:5000',
      '/static': 'http://localhost:5000',
    }
  }
})
