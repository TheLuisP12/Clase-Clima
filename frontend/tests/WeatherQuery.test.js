// Suite de QA - Frontend - WeatherQuery.svelte
//
// Verifica los criterios de aceptación de specs/02-Consulta-clima.md desde
// la perspectiva del cliente:
//   * El botón "Consultar" está deshabilitado sin ubicación seleccionada.
//   * Consulta exitosa (200) muestra temperatura, estado y humedad.
//   * Sin sesión activa (sin token) o 401 del backend emite 'unauthorized'.
//   * Errores del backend/red no crashean y muestran un mensaje claro.
//
// No se modifica frontend/src/** — este archivo solo consume el componente
// real vía import, montado en jsdom.

import { render, screen, fireEvent, waitFor } from '@testing-library/svelte';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import WeatherQuery from '../src/lib/WeatherQuery.svelte';

const FAKE_TOKEN = 'fake.jwt.token';

function getLocationSelect() {
  return screen.getByLabelText(/país o región/i);
}

function getConsultarButton() {
  return screen.getByRole('button', { name: /consultar|consultando/i });
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

describe('WeatherQuery - validación de selección (camino de borde, sin red)', () => {
  it('el botón "Consultar" está deshabilitado sin ubicación seleccionada', () => {
    render(WeatherQuery);
    expect(getConsultarButton()).toBeDisabled();
  });

  it('el botón se habilita al seleccionar una ubicación', async () => {
    render(WeatherQuery);
    await fireEvent.change(getLocationSelect(), { target: { value: 'Peru' } });
    expect(getConsultarButton()).not.toBeDisabled();
  });
});

describe('WeatherQuery - consulta exitosa (200)', () => {
  it('muestra temperatura, estado y humedad tras una consulta exitosa', async () => {
    localStorage.setItem('access_token', FAKE_TOKEN);
    const fetchMock = vi.fn().mockResolvedValue(
      jsonResponse(200, {
        location: 'Peru',
        temperature: '24°C',
        condition: 'Despejado',
        humidity: '60%'
      })
    );
    vi.stubGlobal('fetch', fetchMock);

    render(WeatherQuery);
    await fireEvent.change(getLocationSelect(), { target: { value: 'Peru' } });
    await fireEvent.click(getConsultarButton());

    expect(await screen.findByText('24°C')).toBeInTheDocument();
    expect(screen.getByText('Despejado')).toBeInTheDocument();
    expect(screen.getByText('60%')).toBeInTheDocument();
  });

  it('envía el token como Bearer y la ubicación seleccionada como query param', async () => {
    localStorage.setItem('access_token', FAKE_TOKEN);
    const fetchMock = vi.fn().mockResolvedValue(
      jsonResponse(200, {
        location: 'Chile',
        temperature: '18°C',
        condition: 'Nublado',
        humidity: '70%'
      })
    );
    vi.stubGlobal('fetch', fetchMock);

    render(WeatherQuery);
    await fireEvent.change(getLocationSelect(), { target: { value: 'Chile' } });
    await fireEvent.click(getConsultarButton());

    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(1));

    const [url, options] = fetchMock.mock.calls[0];
    expect(url).toMatch(/\/api\/v1\/weather\?location=Chile$/);
    expect(options.headers.Authorization).toBe(`Bearer ${FAKE_TOKEN}`);
  });

  it('durante la petición isLoading es true (botón deshabilitado y texto "Consultando...")', async () => {
    localStorage.setItem('access_token', FAKE_TOKEN);
    let resolveFetch;
    const fetchMock = vi.fn(
      () =>
        new Promise((resolve) => {
          resolveFetch = resolve;
        })
    );
    vi.stubGlobal('fetch', fetchMock);

    render(WeatherQuery);
    await fireEvent.change(getLocationSelect(), { target: { value: 'Peru' } });
    await fireEvent.click(getConsultarButton());

    expect(await screen.findByRole('button', { name: /consultando/i })).toBeDisabled();

    resolveFetch(
      jsonResponse(200, {
        location: 'Peru',
        temperature: '24°C',
        condition: 'Despejado',
        humidity: '60%'
      })
    );

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /^consultar$/i })).toBeInTheDocument();
    });
  });
});

describe('WeatherQuery - sin sesión activa', () => {
  it('sin token en localStorage, emite "unauthorized" y no llama a fetch', async () => {
    const fetchMock = vi.fn();
    vi.stubGlobal('fetch', fetchMock);

    const { component } = render(WeatherQuery);
    const onUnauthorized = vi.fn();
    component.$on('unauthorized', onUnauthorized);

    await fireEvent.change(getLocationSelect(), { target: { value: 'Peru' } });
    await fireEvent.click(getConsultarButton());

    await waitFor(() => expect(onUnauthorized).toHaveBeenCalledTimes(1));
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it('si el backend responde 401 (token expirado), emite "unauthorized"', async () => {
    localStorage.setItem('access_token', FAKE_TOKEN);
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse(401, { detail: 'Not authenticated' }));
    vi.stubGlobal('fetch', fetchMock);

    const { component } = render(WeatherQuery);
    const onUnauthorized = vi.fn();
    component.$on('unauthorized', onUnauthorized);

    await fireEvent.change(getLocationSelect(), { target: { value: 'Peru' } });
    await fireEvent.click(getConsultarButton());

    await waitFor(() => expect(onUnauthorized).toHaveBeenCalledTimes(1));
  });
});

describe('WeatherQuery - errores del backend / red', () => {
  it('ubicación no encontrada (404) muestra un mensaje claro sin crashear', async () => {
    localStorage.setItem('access_token', FAKE_TOKEN);
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse(404, { detail: 'Location not found' }));
    vi.stubGlobal('fetch', fetchMock);

    render(WeatherQuery);
    await fireEvent.change(getLocationSelect(), { target: { value: 'Peru' } });
    await fireEvent.click(getConsultarButton());

    expect(await screen.findByText(/no se encontró información del clima/i)).toBeInTheDocument();
  });

  it('fallo de red (fetch rechaza) muestra un mensaje de error sin exponer detalles técnicos', async () => {
    localStorage.setItem('access_token', FAKE_TOKEN);
    const fetchMock = vi.fn().mockRejectedValue(new TypeError('Failed to fetch'));
    vi.stubGlobal('fetch', fetchMock);

    render(WeatherQuery);
    await fireEvent.change(getLocationSelect(), { target: { value: 'Peru' } });
    await expect(fireEvent.click(getConsultarButton())).resolves.not.toThrow();

    const errorNode = await screen.findByText(/no se pudo obtener el clima/i);
    expect(errorNode).toBeInTheDocument();
    expect(screen.queryByText(/TypeError/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/Failed to fetch/i)).not.toBeInTheDocument();
  });

  it('error 502 del backend muestra un mensaje genérico', async () => {
    localStorage.setItem('access_token', FAKE_TOKEN);
    const fetchMock = vi
      .fn()
      .mockResolvedValue(jsonResponse(502, { detail: 'Weather service is currently unavailable' }));
    vi.stubGlobal('fetch', fetchMock);

    render(WeatherQuery);
    await fireEvent.change(getLocationSelect(), { target: { value: 'Peru' } });
    await fireEvent.click(getConsultarButton());

    expect(await screen.findByText(/no se pudo obtener el clima/i)).toBeInTheDocument();
  });
});
