<script>
  import { createEventDispatcher } from 'svelte';

  const dispatch = createEventDispatcher();

  const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000';
  const WEATHER_ENDPOINT = `${API_URL}/api/v1/weather`;

  // Países/regiones disponibles para el selector. La spec no define un
  // endpoint para esta lista, así que se mantiene estática en el cliente.
  const LOCATIONS = [
    'Peru',
    'Argentina',
    'Chile',
    'Colombia',
    'Ecuador',
    'Mexico',
    'Spain',
    'United States',
    'Brazil',
    'Bolivia'
  ];

  let selectedLocation = '';
  let isLoading = false;
  let errorMessage = '';
  let weather = null;

  $: isQueryDisabled = !selectedLocation || isLoading;

  async function handleConsultar() {
    // Validación del lado del cliente antes de cualquier petición de red.
    if (!selectedLocation) {
      return;
    }

    isLoading = true;
    errorMessage = '';
    weather = null;

    const token = localStorage.getItem('access_token');
    if (!token) {
      // Sin sesión activa: bloquear la acción y redirigir al login
      // (Escenario 2 de specs/02-Consulta-clima.md).
      isLoading = false;
      dispatch('unauthorized');
      return;
    }

    try {
      const response = await fetch(
        `${WEATHER_ENDPOINT}?location=${encodeURIComponent(selectedLocation)}`,
        {
          headers: {
            Authorization: `Bearer ${token}`
          }
        }
      );

      if (response.status === 401) {
        dispatch('unauthorized');
        return;
      }

      if (response.status === 404) {
        errorMessage = 'No se encontró información del clima para esa ubicación.';
        return;
      }

      if (response.status !== 200) {
        errorMessage = 'No se pudo obtener el clima. Inténtalo de nuevo más tarde.';
        return;
      }

      weather = await response.json();
    } catch (error) {
      // Fallos de red: nunca se expone el detalle técnico en la UI.
      errorMessage = 'No se pudo obtener el clima. Inténtalo de nuevo más tarde.';
    } finally {
      isLoading = false;
    }
  }
</script>

<div class="w-full max-w-md rounded-xl bg-white p-6 shadow-md">
  <h2 class="text-lg font-semibold text-gray-800 mb-4">Consulta meteorológica</h2>

  <div class="space-y-3">
    <div>
      <label for="location" class="block text-sm font-medium text-gray-700 mb-1">
        País o región
      </label>
      <select
        id="location"
        bind:value={selectedLocation}
        class="w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
      >
        <option value="" disabled selected>Selecciona una ubicación</option>
        {#each LOCATIONS as location}
          <option value={location}>{location}</option>
        {/each}
      </select>
    </div>

    <button
      type="button"
      on:click={handleConsultar}
      disabled={isQueryDisabled}
      class="w-full rounded-md px-4 py-2 text-sm font-medium text-white transition-colors
        {isQueryDisabled ? 'bg-blue-300 cursor-not-allowed' : 'bg-blue-600 hover:bg-blue-700'}"
    >
      {#if isLoading}
        Consultando...
      {:else}
        Consultar
      {/if}
    </button>

    {#if errorMessage}
      <div class="rounded-md bg-red-50 border border-red-200 px-3 py-2">
        <p class="text-sm text-red-700">{errorMessage}</p>
      </div>
    {/if}

    {#if weather}
      <div class="rounded-md bg-blue-50 border border-blue-200 px-4 py-3 space-y-1">
        <p class="text-sm text-gray-700">
          <span class="font-medium">Ubicación:</span> {weather.location}
        </p>
        <p class="text-sm text-gray-700">
          <span class="font-medium">Temperatura:</span> {weather.temperature}
        </p>
        <p class="text-sm text-gray-700">
          <span class="font-medium">Estado:</span> {weather.condition}
        </p>
        <p class="text-sm text-gray-700">
          <span class="font-medium">Humedad:</span> {weather.humidity}
        </p>
      </div>
    {/if}
  </div>
</div>
