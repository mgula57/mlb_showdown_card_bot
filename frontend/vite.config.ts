import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// https://vite.dev/config/
export default defineConfig({
    plugins: [react(), tailwindcss()],
    build: {
        sourcemap: false, // Disable sourcemaps in production (saves ~5MB)
        rollupOptions: {
            output: {
                manualChunks: {
                    'react-vendor': ['react', 'react-dom', 'react-router-dom'],
                    'icons': ['react-icons'],
                }
            }
        }
    },
    server: {
        proxy: {
            '/api': {
                target: 'http://127.0.0.1:5000',
                changeOrigin: true,
            },
            '/static': {
                target: 'http://127.0.0.1:5000',
                changeOrigin: true,
            },
        }
    },
    publicDir: 'public',
})
