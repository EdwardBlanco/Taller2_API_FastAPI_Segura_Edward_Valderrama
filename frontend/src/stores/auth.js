import { computed, reactive } from 'vue'
import {
  api,
  clearTokens,
  getAccessToken,
  getRefreshToken,
  setSessionExpiredHandler,
  setTokens,
} from '../services/api'

const state = reactive({
  user: null,
  initialized: false,
  loading: false,
})

setSessionExpiredHandler(() => {
  state.user = null
})

export function useAuth() {
  const isAuthenticated = computed(() => Boolean(state.user))
  const role = computed(() => state.user?.rol || null)
  const isAdmin = computed(() => state.user?.rol === 'admin')
  const isStaff = computed(() => ['admin', 'bibliotecario'].includes(state.user?.rol))
  const isSocio = computed(() => state.user?.rol === 'socio')

  async function init() {
    if (state.initialized) return
    state.loading = true
    try {
      if (getAccessToken() || getRefreshToken()) {
        state.user = await api.auth.me()
      }
    } catch {
      clearTokens()
      state.user = null
    } finally {
      state.initialized = true
      state.loading = false
    }
  }

  async function login(email, password) {
    const tokens = await api.auth.login(email, password)
    setTokens(tokens.access_token, tokens.refresh_token)
    state.user = await api.auth.me()
    state.initialized = true
    return state.user
  }

  async function register(payload) {
    return api.auth.registro(payload)
  }

  async function logout() {
    const refreshToken = getRefreshToken()
    try {
      if (refreshToken && getAccessToken()) {
        await api.auth.logout(refreshToken)
      }
    } catch {
      // Aunque falle la revocación remota, limpiamos sesión local
    } finally {
      clearTokens()
      state.user = null
    }
  }

  async function refreshUser() {
    state.user = await api.auth.me()
    return state.user
  }

  return {
    state,
    user: computed(() => state.user),
    isAuthenticated,
    role,
    isAdmin,
    isStaff,
    isSocio,
    init,
    login,
    register,
    logout,
    refreshUser,
  }
}
