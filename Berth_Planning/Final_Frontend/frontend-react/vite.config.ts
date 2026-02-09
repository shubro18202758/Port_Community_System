import { defineConfig } from 'vite'
import path from 'path'
import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [
    // The React and Tailwind plugins are both required for Make, even if
    // Tailwind is not being actively used – do not remove them
    react(),
    tailwindcss(),
  ],
  resolve: {
    alias: {
      // Alias @ to the src directory
      '@': path.resolve(__dirname, './src'),
    },
  },

  // File types to support raw imports. Never add .css, .tsx, or .ts files to this.
  assetsInclude: ['**/*.svg', '**/*.csv'],

  server: {
    proxy: {
      '/vessels': 'http://localhost:5185',
      '/berths': 'http://localhost:5185',
      '/schedules': 'http://localhost:5185',
      '/dashboard': 'http://localhost:5185',
      '/predictions': 'http://localhost:5185',
      '/suggestions': 'http://localhost:5185',
      '/ports': 'http://localhost:5185',
      '/terminals': 'http://localhost:5185',
      '/resources': 'http://localhost:5185',
      '/analytics': 'http://localhost:5185',
      '/optimization': 'http://localhost:5185',
      '/whatif': 'http://localhost:5185',
      '/ais': 'http://localhost:5185',
      '/channels': 'http://localhost:5185',
      '/anchorages': 'http://localhost:5185',
      '/pilots': 'http://localhost:5185',
      '/tugboats': 'http://localhost:5185',
      '/health': 'http://localhost:5185',
      // AI service routes - direct to Python AI service with path rewrite
      '/ai': {
        target: 'http://localhost:8001',
        changeOrigin: true,
        rewrite: (path: string) => path.replace(/^\/ai/, ''),
      },
      '/chat': {
        target: 'http://localhost:8001',
        changeOrigin: true,
      },
      '/rag': {
        target: 'http://localhost:8001',
        changeOrigin: true,
      },
      '/agents': {
        target: 'http://localhost:8001',
        changeOrigin: true,
      },
      '/monitoring': {
        target: 'http://localhost:8001',
        changeOrigin: true,
      },
      '/ml': {
        target: 'http://localhost:8001',
        changeOrigin: true,
      },
      '/api': 'http://localhost:5185',
      '/agent': {
        target: 'http://localhost:8001',
        ws: true,
        changeOrigin: true,
      },
      '/hubs': {
        target: 'http://localhost:5185',
        ws: true,
        changeOrigin: true,
      },
    },
  },
})
