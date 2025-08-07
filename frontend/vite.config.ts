import react from '@vitejs/plugin-react'
import { resolve } from 'path'
import { defineConfig } from 'vite'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": resolve(__dirname, "./src"),
    },
  },
  server: {
    port: 3030,
    proxy: {
      '/api': {
        target: 'http://localhost:8002',
        changeOrigin: true,
      },
    },
  },
})
