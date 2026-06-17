import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  build: {
    lib: {
      entry: 'src/main.tsx',
      name: 'BQSQLAgent',
      fileName: 'bq-sql-agent',
      formats: ['iife'],
    },
    // Bundle React so the IIFE is self-contained
    rollupOptions: {
      external: [],
    },
  },
})
