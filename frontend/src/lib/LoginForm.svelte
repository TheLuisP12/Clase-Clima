<script>
  import { createEventDispatcher } from 'svelte';

  const dispatch = createEventDispatcher();

  // API configurable vía variable de entorno de Vite.
  const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000';
  const LOGIN_ENDPOINT = `${API_URL}/api/auth/login`;

  const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

  let email = '';
  let password = '';
  let isLoading = false;
  let serverError = '';

  // Estado de "tocado" para no mostrar errores antes de que el usuario
  // interactúe con el campo.
  let emailTouched = false;
  let passwordTouched = false;

  // --- Validación reactiva del lado del cliente ---
  $: emailError = !email
    ? 'El correo es obligatorio.'
    : !EMAIL_REGEX.test(email)
      ? 'Ingresa un correo con formato válido.'
      : '';

  $: passwordError = !password ? 'La contraseña es obligatoria.' : '';

  $: isFormValid = !emailError && !passwordError;

  $: isSubmitDisabled = !isFormValid || isLoading;

  function markTouched(field) {
    if (field === 'email') emailTouched = true;
    if (field === 'password') passwordTouched = true;
  }

  async function handleSubmit() {
    // Se marcan ambos campos como tocados para revelar cualquier error
    // pendiente antes de intentar la petición.
    emailTouched = true;
    passwordTouched = true;
    serverError = '';

    // Validación del lado del cliente ANTES de cualquier petición de red.
    if (!isFormValid) {
      return;
    }

    isLoading = true;

    try {
      const response = await fetch(LOGIN_ENDPOINT, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ email, password })
      });

      if (response.status === 200) {
        const data = await response.json();
        const token = data.access_token;

        if (token) {
          localStorage.setItem('access_token', token);
        }

        dispatch('success');
        return;
      }

      // 401 o cualquier otro código: mensaje genérico, sin revelar
      // si el correo existe ni detalles técnicos del backend.
      serverError = 'Correo o contraseña incorrectos.';
    } catch (error) {
      // No se exponen detalles técnicos ni stacktraces en la UI,
      // y no se registran credenciales ni tokens en consola.
      serverError = 'No se pudo iniciar sesión. Inténtalo de nuevo más tarde.';
    } finally {
      isLoading = false;
      password = '';
    }
  }
</script>

<div class="w-full max-w-md rounded-xl bg-white p-8 shadow-md">
  <h1 class="text-2xl font-semibold text-gray-800 mb-1 text-center">Iniciar sesión</h1>
  <p class="text-gray-500 text-sm mb-6 text-center">Ingresa tus credenciales para continuar</p>

  <form on:submit|preventDefault={handleSubmit} novalidate class="space-y-4">
    <div>
      <label for="email" class="block text-sm font-medium text-gray-700 mb-1">
        Correo electrónico
      </label>
      <input
        id="email"
        type="email"
        autocomplete="email"
        bind:value={email}
        on:blur={() => markTouched('email')}
        class="w-full rounded-md border px-3 py-2 text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-offset-1 transition-colors
          {emailTouched && emailError
            ? 'border-red-500 focus:ring-red-400'
            : 'border-gray-300 focus:ring-blue-400'}"
        placeholder="tucorreo@ejemplo.com"
      />
      {#if emailTouched && emailError}
        <p class="mt-1 text-sm text-red-600">{emailError}</p>
      {/if}
    </div>

    <div>
      <label for="password" class="block text-sm font-medium text-gray-700 mb-1">
        Contraseña
      </label>
      <input
        id="password"
        type="password"
        autocomplete="current-password"
        bind:value={password}
        on:blur={() => markTouched('password')}
        class="w-full rounded-md border px-3 py-2 text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-offset-1 transition-colors
          {passwordTouched && passwordError
            ? 'border-red-500 focus:ring-red-400'
            : 'border-gray-300 focus:ring-blue-400'}"
        placeholder="••••••••"
      />
      {#if passwordTouched && passwordError}
        <p class="mt-1 text-sm text-red-600">{passwordError}</p>
      {/if}
    </div>

    {#if serverError}
      <div class="rounded-md bg-red-50 border border-red-200 px-3 py-2">
        <p class="text-sm text-red-700">{serverError}</p>
      </div>
    {/if}

    <button
      type="submit"
      disabled={isSubmitDisabled}
      class="w-full rounded-md px-4 py-2 text-sm font-medium text-white transition-colors
        {isSubmitDisabled
          ? 'bg-blue-300 cursor-not-allowed'
          : 'bg-blue-600 hover:bg-blue-700'}"
    >
      {#if isLoading}
        Ingresando...
      {:else}
        Ingresar
      {/if}
    </button>
  </form>
</div>
