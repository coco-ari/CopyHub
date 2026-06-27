import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],
  server: {
    proxy: {
      '/api': {
        target: process.env.VITE_BACKEND_URL || 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/ws': {
        target: (process.env.VITE_BACKEND_WS_URL || process.env.VITE_BACKEND_URL || 'ws://127.0.0.1:8000').replace(/^http/, 'ws'),
        ws: true,
      }
    }
  }
})
