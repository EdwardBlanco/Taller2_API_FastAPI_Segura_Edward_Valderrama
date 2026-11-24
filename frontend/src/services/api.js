const API_ORIGIN = (import.meta.env.VITE_API_URL || '').replace(/\/$/, '')
const API_BASE = `${API_ORIGIN}/api/v1`

const STORAGE_ACCESS = 'biblioteca_access_token'
const STORAGE_REFRESH = 'biblioteca_refresh_token'

let refreshPromise = null
let onSessionExpired = null

export function setSessionExpiredHandler(fn) {
  onSessionExpired = fn
}

export function getAccessToken() {
  return localStorage.getItem(STORAGE_ACCESS)
}

export function getRefreshToken() {
  return localStorage.getItem(STORAGE_REFRESH)
}

export function setTokens(accessToken, refreshToken) {
  if (accessToken) localStorage.setItem(STORAGE_ACCESS, accessToken)
  if (refreshToken) localStorage.setItem(STORAGE_REFRESH, refreshToken)
}

export function clearTokens() {
  localStorage.removeItem(STORAGE_ACCESS)
  localStorage.removeItem(STORAGE_REFRESH)
}

function buildQuery(params = {}) {
  const qs = new URLSearchParams()
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      qs.append(key, String(value))
    }
  })
  const str = qs.toString()
  return str ? `?${str}` : ''
}

export function formatApiError(data, fallback = 'Ocurrió un error al comunicarse con el servidor') {
  if (!data) return fallback
  if (typeof data === 'string') return data
  if (typeof data.detail === 'string') return data.detail
  if (Array.isArray(data.detail)) {
    return data.detail
      .map((err) => {
        const loc = Array.isArray(err.loc) ? err.loc.filter((p) => p !== 'body').join('.') : ''
        const msg = err.msg || 'Valor inválido'
        return loc ? `${loc}: ${msg}` : msg
      })
      .join(' · ')
  }
  return fallback
}

async function parseResponseBody(res) {
  if (res.status === 204) return null
  const contentType = res.headers.get('content-type') || ''
  if (contentType.includes('application/json')) {
    try {
      return await res.json()
    } catch {
      return null
    }
  }
  const text = await res.text()
  return text || null
}

async function tryRefreshTokens() {
  const refreshToken = getRefreshToken()
  if (!refreshToken) return false

  if (!refreshPromise) {
    refreshPromise = (async () => {
      try {
        const res = await fetch(`${API_BASE}/auth/refresh`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ refresh_token: refreshToken }),
        })
        if (!res.ok) {
          clearTokens()
          if (onSessionExpired) onSessionExpired()
          return false
        }
        const data = await res.json()
        setTokens(data.access_token, data.refresh_token)
        return true
      } catch {
        clearTokens()
        if (onSessionExpired) onSessionExpired()
        return false
      } finally {
        refreshPromise = null
      }
    })()
  }

  return refreshPromise
}

export async function apiRequest(
  path,
  { method = 'GET', params, body, isFormData = false, isUrlEncoded = false, auth = true, _retried = false } = {},
) {
  const url = `${API_BASE}${path}${buildQuery(params)}`
  const headers = {}

  if (auth) {
    const token = getAccessToken()
    if (token) {
      headers.Authorization = `Bearer ${token}`
    }
  }

  let fetchBody
  if (body !== undefined && body !== null) {
    if (isFormData) {
      fetchBody = body
    } else if (isUrlEncoded) {
      headers['Content-Type'] = 'application/x-www-form-urlencoded'
      fetchBody = body instanceof URLSearchParams ? body.toString() : new URLSearchParams(body).toString()
    } else {
      headers['Content-Type'] = 'application/json'
      fetchBody = JSON.stringify(body)
    }
  }

  let res
  try {
    res = await fetch(url, { method, headers, body: fetchBody })
  } catch {
    throw new Error('No se pudo conectar con el servidor backend. Verifica que la API esté ejecutándose.')
  }

  if (res.status === 401 && auth && !_retried && !path.startsWith('/auth/login') && !path.startsWith('/auth/refresh')) {
    const refreshed = await tryRefreshTokens()
    if (refreshed) {
      return apiRequest(path, { method, params, body, isFormData, isUrlEncoded, auth, _retried: true })
    }
  }

  const data = await parseResponseBody(res)
  if (!res.ok) {
    const error = new Error(formatApiError(data, `Error ${res.status}`))
    error.status = res.status
    error.data = data
    throw error
  }

  return data
}

export const api = {
  // Salud
  health: () => apiRequest('/health', { auth: false }),

  // Autenticación
  auth: {
    registro: (datos) => apiRequest('/auth/registro', { method: 'POST', body: datos, auth: false }),
    login: (email, password) =>
      apiRequest('/auth/login', {
        method: 'POST',
        body: { username: email, password },
        isUrlEncoded: true,
        auth: false,
      }),
    refresh: (refresh_token) =>
      apiRequest('/auth/refresh', { method: 'POST', body: { refresh_token }, auth: false }),
    logout: (refresh_token) =>
      apiRequest('/auth/logout', { method: 'POST', body: { refresh_token } }),
    me: () => apiRequest('/auth/me'),
    cambiarPassword: (datos) => apiRequest('/auth/me/password', { method: 'PATCH', body: datos }),
  },

  // Libros
  libros: {
    listar: (params) => apiRequest('/libros', { params, auth: false }),
    obtener: (id) => apiRequest(`/libros/${id}`, { auth: false }),
    crear: (datos) => apiRequest('/libros', { method: 'POST', body: datos }),
    crearConPortada: (formData) =>
      apiRequest('/libros/con-portada', { method: 'POST', body: formData, isFormData: true }),
    actualizar: (id, datos) => apiRequest(`/libros/${id}`, { method: 'PATCH', body: datos }),
    eliminar: (id) => apiRequest(`/libros/${id}`, { method: 'DELETE' }),
    subirPortada: (id, archivo) => {
      const fd = new FormData()
      fd.append('portada', archivo)
      return apiRequest(`/libros/${id}/portada`, { method: 'POST', body: fd, isFormData: true })
    },
    eliminarPortada: (id) => apiRequest(`/libros/${id}/portada`, { method: 'DELETE' }),
  },

  // Autores
  autores: {
    listar: (params) => apiRequest('/autores', { params, auth: false }),
    obtener: (id) => apiRequest(`/autores/${id}`, { auth: false }),
    libros: (id) => apiRequest(`/autores/${id}/libros`, { auth: false }),
    crear: (datos) => apiRequest('/autores', { method: 'POST', body: datos }),
    actualizar: (id, datos) => apiRequest(`/autores/${id}`, { method: 'PATCH', body: datos }),
    eliminar: (id) => apiRequest(`/autores/${id}`, { method: 'DELETE' }),
  },

  // Categorías
  categorias: {
    listar: (params) => apiRequest('/categorias', { params, auth: false }),
    obtener: (id) => apiRequest(`/categorias/${id}`, { auth: false }),
    crear: (datos) => apiRequest('/categorias', { method: 'POST', body: datos }),
    actualizar: (id, datos) => apiRequest(`/categorias/${id}`, { method: 'PATCH', body: datos }),
    eliminar: (id) => apiRequest(`/categorias/${id}`, { method: 'DELETE' }),
  },

  // Socios
  socios: {
    me: () => apiRequest('/socios/me'),
    actualizarMe: (datos) => apiRequest('/socios/me', { method: 'PATCH', body: datos }),
    misPrestamos: (params) => apiRequest('/socios/me/prestamos', { params }),
    misMultas: () => apiRequest('/socios/me/multas'),
    listar: (params) => apiRequest('/socios', { params }),
    obtener: (id) => apiRequest(`/socios/${id}`),
    prestamos: (id, params) => apiRequest(`/socios/${id}/prestamos`, { params }),
    crear: (datos) => apiRequest('/socios', { method: 'POST', body: datos }),
    actualizar: (id, datos) => apiRequest(`/socios/${id}`, { method: 'PATCH', body: datos }),
    eliminar: (id) => apiRequest(`/socios/${id}`, { method: 'DELETE' }),
  },

  // Préstamos
  prestamos: {
    listar: (params) => apiRequest('/prestamos', { params }),
    obtener: (id) => apiRequest(`/prestamos/${id}`),
    crear: (datos) => apiRequest('/prestamos', { method: 'POST', body: datos }),
    devolver: (id, datos) => apiRequest(`/prestamos/${id}/devolucion`, { method: 'POST', body: datos }),
    pagarMulta: (id) => apiRequest(`/prestamos/${id}/pago-multa`, { method: 'POST' }),
  },

  // Reportes
  reportes: {
    resumen: () => apiRequest('/reportes/resumen'),
    librosMasPrestados: (limite = 5) =>
      apiRequest('/reportes/libros-mas-prestados', { params: { limite } }),
    categorias: () => apiRequest('/reportes/categorias'),
    prestamosVencidos: () => apiRequest('/reportes/prestamos-vencidos'),
    sociosConMultas: () => apiRequest('/reportes/socios-con-multas'),
    autores: () => apiRequest('/reportes/autores'),
  },

  // Usuarios (Admin)
  usuarios: {
    listar: (params) => apiRequest('/usuarios', { params }),
    crear: (datos) => apiRequest('/usuarios', { method: 'POST', body: datos }),
    cambiarRol: (id, rol) => apiRequest(`/usuarios/${id}/rol`, { method: 'PATCH', body: { rol } }),
    cambiarActivo: (id, activo) =>
      apiRequest(`/usuarios/${id}/activo`, { method: 'PATCH', body: { activo } }),
  },
}
