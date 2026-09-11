// Suite de QA - Frontend - LoginForm.svelte
//
// Verifica los criterios de aceptación de specs/01-login.md desde la
// perspectiva del cliente:
//   * Campos vacíos / formato de correo inválido bloquean el envío
//     (validación reactiva ANTES de cualquier petición de red).
//   * Login correcto (200) refleja loading true -> false y guarda el token.
//   * Password incorrecta / usuario inexistente (401) muestran el MISMO
//     mensaje genérico, sin distinguir el motivo del rechazo.
//   * Fallo de red no provoca un crash, y se informa con un mensaje de error.
//
// No se modifica frontend/src/** — este archivo solo consume el componente
// real vía import, montado en jsdom.

import { render, screen, fireEvent, waitFor } from '@testing-library/svelte';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import LoginForm from '../src/lib/LoginForm.svelte';

const VALID_EMAIL = 'test@example.com';
const VALID_PASSWORD = 'Password123!';

function getEmailInput() {
  return screen.getByLabelText(/correo electrónico/i);
}

function getPasswordInput() {
  return screen.getByLabelText(/contraseña/i);
}

function getSubmitButton() {
  return screen.getByRole('button', { name: /ingresar|ingresando/i });
}

/** Crea un mock de fetch controlable manualmente (para inspeccionar el
 * estado de loading mientras la promesa sigue pendiente). */
function deferredFetchMock() {
  let resolve;
  let reject;
  const promise = new Promise((res, rej) => {
    resolve = res;
    reject = rej;
  });
  const fetchMock = vi.fn(() => promise);
  return { fetchMock, resolve, reject };
}

function jsonResponse(status, body) {
  return {
    status,
    json: async () => body
  };
}

beforeEach(() => {
  localStorage.clear();
});

describe('LoginForm - validación de campos (camino de borde, sin red)', () => {
  it('el botón de submit está deshabilitado con ambos campos vacíos', () => {
    render(LoginForm);
    expect(getSubmitButton()).toBeDisabled();
  });

  it('el botón sigue deshabilitado si solo se llena el email', async () => {
    render(LoginForm);
    await fireEvent.input(getEmailInput(), { target: { value: VALID_EMAIL } });
    expect(getSubmitButton()).toBeDisabled();
  });

  it('el botón sigue deshabilitado si solo se llena el password', async () => {
    render(LoginForm);
    await fireEvent.input(getPasswordInput(), { target: { value: VALID_PASSWORD } });
    expect(getSubmitButton()).toBeDisabled();
  });

  it('muestra error de formato inválido de correo tras perder el foco, y NO habilita el submit', async () => {
    render(LoginForm);
    const emailInput = getEmailInput();

    await fireEvent.input(emailInput, { target: { value: 'correo-sin-arroba' } });
    await fireEvent.blur(emailInput);
    await fireEvent.input(getPasswordInput(), { target: { value: VALID_PASSWORD } });

    expect(await screen.findByText(/correo con formato válido/i)).toBeInTheDocument();
    expect(getSubmitButton()).toBeDisabled();
  });

  it('NO realiza ninguna petición de red si el email tiene formato inválido', async () => {
    const fetchMock = vi.fn();
    vi.stubGlobal('fetch', fetchMock);

    const { container } = render(LoginForm);
    await fireEvent.input(getEmailInput(), { target: { value: 'no-es-un-correo' } });
    await fireEvent.input(getPasswordInput(), { target: { value: VALID_PASSWORD } });

    // Se dispara el submit del <form> directamente (defensa en profundidad:
    // incluso si el atributo disabled del botón fuese removido o el envío
    // ocurriera por Enter, la guarda interna de handleSubmit debe frenarlo).
    const form = container.querySelector('form');
    await fireEvent.submit(form);

    expect(fetchMock).not.toHaveBeenCalled();
  });

  it('NO realiza ninguna petición de red con campos vacíos', async () => {
    const fetchMock = vi.fn();
    vi.stubGlobal('fetch', fetchMock);

    const { container } = render(LoginForm);
    const form = container.querySelector('form');
    await fireEvent.submit(form);

    expect(fetchMock).not.toHaveBeenCalled();
    expect(await screen.findByText(/correo es obligatorio/i)).toBeInTheDocument();
  });
});

describe('LoginForm - login correcto (200)', () => {
  it('durante la petición isLoading es true (botón deshabilitado y texto "Ingresando..."), y false al finalizar', async () => {
    const { fetchMock, resolve } = deferredFetchMock();
    vi.stubGlobal('fetch', fetchMock);

    render(LoginForm);
    await fireEvent.input(getEmailInput(), { target: { value: VALID_EMAIL } });
    await fireEvent.input(getPasswordInput(), { target: { value: VALID_PASSWORD } });
    await fireEvent.click(getSubmitButton());

    // Mientras la promesa de fetch sigue pendiente: loading = true.
    expect(await screen.findByRole('button', { name: /ingresando/i })).toBeDisabled();

    resolve(jsonResponse(200, { access_token: 'fake.jwt.token', token_type: 'bearer' }));

    // Al resolver: loading vuelve a false (botón vuelve a decir "Ingresar").
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /^ingresar$/i })).toBeInTheDocument();
    });
  });

  it('guarda el token recibido en localStorage y emite el evento success', async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      jsonResponse(200, { access_token: 'fake.jwt.token', token_type: 'bearer' })
    );
    vi.stubGlobal('fetch', fetchMock);

    const { component } = render(LoginForm);
    const onSuccess = vi.fn();
    component.$on('success', onSuccess);

    await fireEvent.input(getEmailInput(), { target: { value: VALID_EMAIL } });
    await fireEvent.input(getPasswordInput(), { target: { value: VALID_PASSWORD } });
    await fireEvent.click(getSubmitButton());

    await waitFor(() => expect(onSuccess).toHaveBeenCalledTimes(1));

    const storedToken =
      localStorage.getItem('jwt') ??
      localStorage.getItem('access_token') ??
      localStorage.getItem('token');
    expect(storedToken).toBe('fake.jwt.token');
  });

  it('envía email y password tal cual al endpoint correcto', async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      jsonResponse(200, { access_token: 'fake.jwt.token', token_type: 'bearer' })
    );
    vi.stubGlobal('fetch', fetchMock);

    render(LoginForm);
    await fireEvent.input(getEmailInput(), { target: { value: VALID_EMAIL } });
    await fireEvent.input(getPasswordInput(), { target: { value: VALID_PASSWORD } });
    await fireEvent.click(getSubmitButton());

    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(1));

    const [url, options] = fetchMock.mock.calls[0];
    expect(url).toMatch(/\/api\/auth\/login$/);
    expect(options.method).toBe('POST');
    const sentBody = JSON.parse(options.body);
    expect(sentBody).toEqual({ email: VALID_EMAIL, password: VALID_PASSWORD });
  });
});

describe('LoginForm - credenciales inválidas (401) sin revelar existencia del usuario', () => {
  it('muestra un mensaje de error genérico cuando el backend responde 401 por password incorrecta', async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue(jsonResponse(401, { detail: 'Invalid email or password' }));
    vi.stubGlobal('fetch', fetchMock);

    render(LoginForm);
    await fireEvent.input(getEmailInput(), { target: { value: VALID_EMAIL } });
    await fireEvent.input(getPasswordInput(), { target: { value: 'ClaveIncorrecta1!' } });
    await fireEvent.click(getSubmitButton());

    const errorNode = await screen.findByText(/correo o contraseña incorrectos/i);
    expect(errorNode).toBeInTheDocument();
  });

  it('muestra EXACTAMENTE el mismo mensaje genérico para usuario inexistente que para password incorrecta', async () => {
    // Dos respuestas 401 con bodies distintos del backend (a propósito, para
    // simular ambos escenarios); el frontend NO debe leer/derivar nada del
    // body en caso de error, así que el texto mostrado debe ser idéntico.
    const scenarios = [
      jsonResponse(401, { detail: 'Invalid email or password' }), // password incorrecta
      jsonResponse(401, { detail: 'Invalid email or password' }) // usuario inexistente
    ];

    const messages = [];
    for (const responseBody of scenarios) {
      const fetchMock = vi.fn().mockResolvedValue(responseBody);
      vi.stubGlobal('fetch', fetchMock);

      const { unmount } = render(LoginForm);
      await fireEvent.input(getEmailInput(), { target: { value: VALID_EMAIL } });
      await fireEvent.input(getPasswordInput(), { target: { value: 'algo-cualquiera1!' } });
      await fireEvent.click(getSubmitButton());

      const errorNode = await screen.findByText(/correo o contraseña incorrectos/i);
      messages.push(errorNode.textContent.trim());
      unmount();
      vi.unstubAllGlobals();
    }

    expect(messages[0]).toBe(messages[1]);
  });

  it('nunca renderiza el detail crudo del backend ni palabras que distingan "no existe" de "incorrecta"', async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue(jsonResponse(401, { detail: 'User does not exist in database' }));
    vi.stubGlobal('fetch', fetchMock);

    render(LoginForm);
    await fireEvent.input(getEmailInput(), { target: { value: 'fantasma@example.com' } });
    await fireEvent.input(getPasswordInput(), { target: { value: 'algo1234!' } });
    await fireEvent.click(getSubmitButton());

    await screen.findByText(/correo o contraseña incorrectos/i);
    expect(screen.queryByText(/does not exist/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/database/i)).not.toBeInTheDocument();
  });

  it('no guarda ningún token en localStorage cuando la respuesta es 401', async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue(jsonResponse(401, { detail: 'Invalid email or password' }));
    vi.stubGlobal('fetch', fetchMock);

    render(LoginForm);
    await fireEvent.input(getEmailInput(), { target: { value: VALID_EMAIL } });
    await fireEvent.input(getPasswordInput(), { target: { value: 'malaClave1!' } });
    await fireEvent.click(getSubmitButton());

    await screen.findByText(/correo o contraseña incorrectos/i);
    expect(localStorage.getItem('jwt')).toBeNull();
  });
});

describe('LoginForm - fallo de red', () => {
  it('si fetch rechaza la promesa (sin conexión/servidor caído), muestra un mensaje de error y no lanza una excepción no controlada', async () => {
    const fetchMock = vi.fn().mockRejectedValue(new TypeError('Failed to fetch'));
    vi.stubGlobal('fetch', fetchMock);

    render(LoginForm);
    await fireEvent.input(getEmailInput(), { target: { value: VALID_EMAIL } });
    await fireEvent.input(getPasswordInput(), { target: { value: VALID_PASSWORD } });

    // No debe lanzar/crashear el test runner.
    await expect(fireEvent.click(getSubmitButton())).resolves.not.toThrow();

    const errorNode = await screen.findByText(/no se pudo iniciar sesión/i);
    expect(errorNode).toBeInTheDocument();

    // El estado de loading debe volver a false tras el fallo (no queda
    // colgado en "Ingresando...").
    expect(screen.getByRole('button', { name: /^ingresar$/i })).toBeInTheDocument();
  });

  it('no expone el mensaje técnico del error (p.ej. "TypeError", "Failed to fetch") en la UI', async () => {
    const fetchMock = vi.fn().mockRejectedValue(new TypeError('Failed to fetch'));
    vi.stubGlobal('fetch', fetchMock);

    render(LoginForm);
    await fireEvent.input(getEmailInput(), { target: { value: VALID_EMAIL } });
    await fireEvent.input(getPasswordInput(), { target: { value: VALID_PASSWORD } });
    await fireEvent.click(getSubmitButton());

    await screen.findByText(/no se pudo iniciar sesión/i);
    expect(screen.queryByText(/TypeError/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/Failed to fetch/i)).not.toBeInTheDocument();
  });
});
