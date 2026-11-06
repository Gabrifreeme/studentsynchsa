import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/postcss'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  css: {
    postcss: {
      // Tailwind v4 moved the PostCSS plugin to @tailwindcss/postcss
      plugins: [tailwindcss()],
    },
  },
})
