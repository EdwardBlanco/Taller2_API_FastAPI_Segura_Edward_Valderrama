<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { api } from './services/api'
import { useAuth } from './stores/auth'

const router = useRouter()
const auth = useAuth()
const apiHealth = ref({ status: 'checking', database: 'checking' })

async function checkHealth() {
  try {
    apiHealth.value = await api.health()
  } catch {
    apiHealth.value = { status: 'error', database: 'error' }
  }
}

async function handleLogout() {
  await auth.logout()
  router.push('/libros')
}

onMounted(() => {
  auth.init()
  checkHealth()
})
</script>

<template>
  <div class="app-shell">
    <header class="topbar">
      <div class="topbar-inner">
        <router-link to="/libros" class="brand">
          <span class="brand-mark">B</span>
          <span>Biblioteca</span>
        </router-link>

        <nav class="nav-links" aria-label="Navegación principal">
          <router-link to="/libros" class="nav-link">Catálogo</router-link>
          <router-link to="/autores" class="nav-link">Autores</router-link>
          <router-link to="/categorias" class="nav-link">Categorías</router-link>
          <router-link v-if="auth.isAuthenticated.value" to="/prestamos" class="nav-link">
            Préstamos
          </router-link>
          <router-link v-if="auth.isStaff.value" to="/socios" class="nav-link">
            Socios
          </router-link>
          <router-link v-if="auth.isStaff.value" to="/reportes" class="nav-link">
            Reportes
          </router-link>
          <router-link v-if="auth.isAdmin.value" to="/usuarios" class="nav-link">
            Usuarios
          </router-link>
          <router-link v-if="auth.isAuthenticated.value" to="/mi-cuenta" class="nav-link">
            Mi cuenta
          </router-link>
        </nav>

        <div class="topbar-right">
          <template v-if="auth.isAuthenticated.value">
            <div class="user-pill">
              <span>{{ auth.user.value?.nombre }}</span>
              <span class="badge badge-primary">{{ auth.role.value }}</span>
            </div>
            <button type="button" class="btn btn-secondary btn-sm" @click="handleLogout">
              Salir
            </button>
          </template>
          <template v-else>
            <router-link to="/login" class="btn btn-secondary btn-sm">Iniciar sesión</router-link>
            <router-link to="/registro" class="btn btn-primary btn-sm">Registrarse</router-link>
          </template>
        </div>
      </div>
    </header>

    <main class="main-container">
      <router-view />
    </main>

    <footer class="footer">
      <div class="footer-inner">
        <span>Sistema de Gestión de Biblioteca · API v1</span>
        <div>
          <span
            class="status-dot"
            :class="{
              ok: apiHealth.status === 'ok',
              error: apiHealth.status === 'error',
            }"
          />
          <span v-if="apiHealth.status === 'ok'">API y base de datos conectadas</span>
          <span v-else-if="apiHealth.status === 'error'">Sin conexión con la API</span>
          <span v-else>Verificando conexión...</span>
        </div>
      </div>
    </footer>
  </div>
</template>
