import '@testing-library/jest-dom/vitest';
import { cleanup } from '@testing-library/svelte';
import { afterEach, vi } from 'vitest';

// Limpia el DOM entre tests y evita fugas de estado entre casos.
afterEach(() => {
  cleanup();
  localStorage.clear();
  vi.restoreAllMocks();
});
