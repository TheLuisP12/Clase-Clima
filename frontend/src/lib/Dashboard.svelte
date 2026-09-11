<script>
  import { createEventDispatcher } from 'svelte';
  import WeatherQuery from './WeatherQuery.svelte';

  const dispatch = createEventDispatcher();

  function handleLogout() {
    dispatch('logout');
  }
</script>

<div class="w-full max-w-md space-y-4">
  <div class="rounded-xl bg-white p-8 shadow-md text-center">
    <h1 class="text-2xl font-semibold text-gray-800 mb-2">¡Bienvenido!</h1>
    <p class="text-gray-600 mb-6">Has iniciado sesión correctamente.</p>
    <button
      type="button"
      on:click={handleLogout}
      class="rounded-md bg-gray-800 px-4 py-2 text-sm font-medium text-white hover:bg-gray-700 transition-colors"
    >
      Cerrar sesión
    </button>
  </div>

  <WeatherQuery on:unauthorized={handleLogout} />
</div>
