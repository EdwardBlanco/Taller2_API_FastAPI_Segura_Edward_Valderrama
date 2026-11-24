<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from '../stores/auth'

const router = useRouter()
const auth = useAuth()

const form = reactive({
  nombre: '',
  email: '',
  telefono: '',
  password: '',
  confirmar_password: '',
})

const error = ref('')
const success = ref('')
const loading = ref(false)

async function handleSubmit() {
  error.value = ''
  success.value = ''

  if (form.password !== form.confirmar_password) {
    error.value = 'Las contraseñas no coinciden'
    return
  }

  loading.value = true
  try {
    await auth.register({
      nombre: form.nombre.trim(),
      email: form.email.trim(),
      telefono: form.telefono.trim() || null,
      password: form.password,
      confirmar_password: form.confirmar_password,
    })
    success.value = 'Cuenta registrada correctamente. Ahora puedes iniciar sesión.'
    setTimeout(() => router.push('/login'), 1100)
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
        <h1 class="card-title">Registro de socio</h1>
      </div>
      <div class="card-body">
        <div v-if="error" class="alert alert-error">{{ error }}</div>
        <div v-if="success" class="alert alert-success">{{ success }}</div>

        <form @submit.prevent="handleSubmit">
          <div class="field">
            <label for="reg-nombre">Nombre completo</label>
            <input
              id="reg-nombre"
              v-model="form.nombre"
              type="text"
              required
              minlength="3"
              maxlength="100"
              placeholder="Ana Torres"
            />
          </div>

          <div class="field">
            <label for="reg-email">Correo electrónico</label>
            <input
              id="reg-email"
              v-model="form.email"
              type="email"
              required
              placeholder="ana@ejemplo.com"
            />
          </div>

          <div class="field">
            <label for="reg-tel">Teléfono (opcional)</label>
            <input
              id="reg-tel"
              v-model="form.telefono"
              type="text"
              placeholder="+57 3001234567"
            />
          </div>

          <div class="field">
            <label for="reg-pass">Contraseña</label>
            <input
              id="reg-pass"
              v-model="form.password"
              type="password"
              required
              minlength="8"
              maxlength="64"
              placeholder="Mínimo 8 caracteres, mayúscula, minúscula y número"
            />
          </div>

          <div class="field">
            <label for="reg-pass2">Confirmar contraseña</label>
            <input
              id="reg-pass2"
              v-model="form.confirmar_password"
              type="password"
              required
              minlength="8"
              maxlength="64"
            />
          </div>

          <button
            type="submit"
            class="btn btn-primary"
            style="width: 100%; margin-top: 8px"
            :disabled="loading"
          >
            {{ loading ? 'Registrando...' : 'Crear cuenta' }}
          </button>
        </form>

        <p class="hint" style="margin-top: 14px; text-align: center">
          ¿Ya tienes una cuenta?
          <router-link to="/login">Inicia sesión</router-link>
        </p>
      </div>
    </div>
  </div>
</template>
