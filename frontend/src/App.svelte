<script>
  import { onMount } from 'svelte';
  import LoginForm from './lib/LoginForm.svelte';
  import Dashboard from './lib/Dashboard.svelte';

  let isAuthenticated = false;

  // Ciclo de vida: al montar la app, revisamos si ya existe una sesión
  // guardada (token JWT) para no forzar un nuevo login innecesariamente.
  onMount(() => {
    const existingToken = localStorage.getItem('access_token');
    if (existingToken) {
      isAuthenticated = true;
    }
  });

  function handleLoginSuccess() {
    isAuthenticated = true;
  }

  function handleLogout() {
    localStorage.removeItem('access_token');
    isAuthenticated = false;
  }
</script>

<main class="min-h-screen flex items-center justify-center bg-gray-100 px-4">
  {#if isAuthenticated}
    <Dashboard on:logout={handleLogout} />
  {:else}
    <LoginForm on:success={handleLoginSuccess} />
  {/if}
</main>
