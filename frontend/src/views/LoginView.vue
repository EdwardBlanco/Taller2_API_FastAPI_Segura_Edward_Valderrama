<script setup>
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuth } from '../stores/auth'

const router = useRouter()
const route = useRoute()
const auth = useAuth()

const email = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)

async function handleSubmit() {
  error.value = ''
  loading.value = true
  try {
    await auth.login(email.value.trim(), password.value)
    const redirect = typeof route.query.redirect === 'string' ? route.query.redirect : '/libros'
    router.push(redirect)
  } catch (err) {
    error.value = err.message
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="auth-wrapper">
    <div class="card">
      <div class="card-header">
        <h1 class="card-title">Iniciar sesión</h1>
      </div>
      <div class="card-body">
        <div v-if="error" class="alert alert-error">{{ error }}</div>

        <form @submit.prevent="handleSubmit">
          <div class="field">
            <label for="login-email">Correo electrónico</label>
            <input
              id="login-email"
              v-model="email"
              type="email"
              required
              autocomplete="username"
              placeholder="correo@ejemplo.com"
            />
          </div>

          <div class="field">
            <label for="login-password">Contraseña</label>
            <input
              id="login-password"
              v-model="password"
              type="password"
              required
              autocomplete="current-password"
              placeholder="••••••••"
            />
          </div>

          <button
            type="submit"
            class="btn btn-primary"
            style="width: 100%; margin-top: 8px"
            :disabled="loading"
          >
            {{ loading ? 'Ingresando...' : 'Entrar' }}
          </button>
        </form>

        <p class="hint" style="margin-top: 14px; text-align: center">
          ¿Aún no tienes cuenta de socio?
          <router-link to="/registro">Regístrate aquí</router-link>
        </p>
      </div>
    </div>
  </div>
</template>
