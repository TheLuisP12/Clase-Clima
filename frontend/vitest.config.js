import { defineConfig } from 'vitest/config';
import { svelte } from '@sveltejs/vite-plugin-svelte';

// Config de testing (QA) separada de vite.config.js de la app.
// No modifica la config de build/dev de producción.
export default defineConfig({
  plugins: [svelte({ hot: false })],
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./tests/setup.js'],
    css: true
  },
  resolve: {
    conditions: ['browser']
  }
});
