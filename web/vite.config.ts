import path from 'node:path'
import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      '@': path.resolve(import.meta.dirname, './src'),
    },
  },
  // maplibre-gl ships its own web worker as a separate file; Vite's dep
  // pre-bundler doesn't follow that dynamic worker import correctly and
  // breaks it ("Worker failed to load... maplibre-gl-worker.mjs" in dev).
  // Excluding it from pre-bundling is maplibre-gl's own documented fix.
  optimizeDeps: {
    exclude: ['maplibre-gl'],
  },
})
