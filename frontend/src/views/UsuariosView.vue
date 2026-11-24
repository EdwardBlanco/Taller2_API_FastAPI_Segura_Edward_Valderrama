<script setup>
import { onMounted, reactive, ref } from 'vue'
import PaginationBar from '../components/PaginationBar.vue'
import { api } from '../services/api'
import { useAuth } from '../stores/auth'

const auth = useAuth()

const usuarios = ref([])
const total = ref(0)
const skip = ref(0)
const limit = 10

const filters = reactive({
  rol: '',
  activo: '',
})

const loading = ref(false)
const error = ref('')
const feedback = ref('')

const showModal = ref(false)
const saving = ref(false)
const formError = ref('')
const form = reactive({
  nombre: '',
  email: '',
  password: '',
  rol: 'bibliotecario',
})

async function loadUsuarios(newSkip = skip.value) {
  loading.value = true
  error.value = ''
  skip.value = newSkip
  try {
    const res = await api.usuarios.listar({
      skip: skip.value,
      limit,
      rol: filters.rol || undefined,
      activo: filters.activo === '' ? undefined : filters.activo,
    })
    usuarios.value = res.items
    total.value = res.total
  } catch (err) {
    error.value = err.message
  } finally {
    loading.value = false
  }
}

function openCreate() {
  formError.value = ''
  form.nombre = ''
  form.email = ''
  form.password = ''
  form.rol = 'bibliotecario'
  showModal.value = true
}

async function createUsuario() {
  formError.value = ''
  saving.value = true
  try {
    await api.usuarios.crear({
      nombre: form.nombre.trim(),
      email: form.email.trim(),
      password: form.password,
      rol: form.rol,
    })
    showModal.value = false
    feedback.value = 'Usuario creado correctamente.'
    await loadUsuarios(0)
  } catch (err) {
    formError.value = err.message
  } finally {
    saving.value = false
  }
}

async function handleRoleChange(usuario, nuevoRol) {
  if (usuario.rol === nuevoRol) return
  error.value = ''
  feedback.value = ''
  try {
    await api.usuarios.cambiarRol(usuario.id, nuevoRol)
    feedback.value = `Rol de ${usuario.nombre} actualizado a ${nuevoRol}.`
    await loadUsuarios(skip.value)
  } catch (err) {
    error.value = err.message
    await loadUsuarios(skip.value)
  }
}

async function handleToggleActivo(usuario) {
  error.value = ''
  feedback.value = ''
  try {
    await api.usuarios.cambiarActivo(usuario.id, !usuario.activo)
    feedback.value = `Usuario ${usuario.nombre} ${!usuario.activo ? 'activado' : 'desactivado'}.`
    await loadUsuarios(skip.value)
  } catch (err) {
    error.value = err.message
  }
}

onMounted(() => loadUsuarios(0))
</script>

<template>
  <div>
    <div class="page-header">
      <div>
        <h1 class="page-title">Usuarios y Roles</h1>
        <p class="page-subtitle">Administración de cuentas de personal, roles y estado de acceso.</p>
      </div>
      <div class="page-actions">
        <button type="button" class="btn btn-primary" @click="openCreate">+ Nuevo personal</button>
      </div>
    </div>

    <div v-if="feedback" class="alert alert-success">{{ feedback }}</div>
    <div v-if="error" class="alert alert-error">{{ error }}</div>

    <form class="filters-bar" @submit.prevent="loadUsuarios(0)">
      <div class="filter-field compact">
        <label for="fu-rol">Rol</label>
        <select id="fu-rol" v-model="filters.rol">
          <option value="">Todos</option>
          <option value="admin">Admin</option>
          <option value="bibliotecario">Bibliotecario</option>
          <option value="socio">Socio</option>
        </select>
      </div>
      <div class="filter-field compact">
        <label for="fu-activo">Estado</label>
        <select id="fu-activo" v-model="filters.activo">
          <option value="">Todos</option>
          <option value="true">Activos</option>
          <option value="false">Inactivos</option>
        </select>
      </div>
      <div class="actions-cell">
        <button type="submit" class="btn btn-primary">Filtrar</button>
      </div>
    </form>

    <div class="card">
      <div v-if="loading" class="empty-state">Cargando usuarios...</div>
      <div v-else-if="usuarios.length === 0" class="empty-state">No hay usuarios que coincidan.</div>
      <div v-else class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Nombre</th>
              <th>Correo</th>
              <th>Rol</th>
              <th>Estado</th>
              <th>Acciones</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="u in usuarios" :key="u.id">
              <td>{{ u.id }}</td>
              <td><strong>{{ u.nombre }}</strong></td>
              <td>{{ u.email }}</td>
              <td>
                <select
                  :value="u.rol"
                  :disabled="u.id === auth.user.value?.id"
                  style="width: auto"
                  @change="handleRoleChange(u, $event.target.value)"
                >
                  <option value="socio">socio</option>
                  <option value="bibliotecario">bibliotecario</option>
                  <option value="admin">admin</option>
                </select>
              </td>
              <td>
                <span class="badge" :class="u.activo ? 'badge-success' : 'badge-danger'">
                  {{ u.activo ? 'Activo' : 'Inactivo' }}
                </span>
              </td>
              <td>
                <button
                  type="button"
                  class="btn btn-sm"
                  :class="u.activo ? 'btn-danger' : 'btn-secondary'"
                  :disabled="u.id === auth.user.value?.id"
                  @click="handleToggleActivo(u)"
                >
                  {{ u.activo ? 'Desactivar' : 'Activar' }}
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <PaginationBar :total="total" :skip="skip" :limit="limit" @change="loadUsuarios" />

    <div v-if="showModal" class="modal-backdrop" @click.self="showModal = false">
      <div class="modal">
        <div class="modal-header">
          <h2 class="card-title">Crear usuario de personal</h2>
          <button type="button" class="btn btn-ghost btn-sm" @click="showModal = false">Cerrar</button>
        </div>
        <form @submit.prevent="createUsuario">
          <div class="modal-body">
            <div v-if="formError" class="alert alert-error">{{ formError }}</div>
            <div class="field">
              <label for="us-nombre">Nombre</label>
              <input id="us-nombre" v-model="form.nombre" type="text" required minlength="3" maxlength="100" />
            </div>
            <div class="field">
              <label for="us-email">Correo electrónico</label>
              <input id="us-email" v-model="form.email" type="email" required />
            </div>
            <div class="field">
              <label for="us-pass">Contraseña</label>
              <input
                id="us-pass"
                v-model="form.password"
                type="password"
                required
                minlength="8"
                maxlength="64"
                placeholder="Mayúscula, minúscula y número"
              />
            </div>
            <div class="field">
              <label for="us-rol">Rol</label>
              <select id="us-rol" v-model="form.rol" required>
                <option value="bibliotecario">Bibliotecario</option>
                <option value="admin">Administrador</option>
              </select>
            </div>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" @click="showModal = false">Cancelar</button>
            <button type="submit" class="btn btn-primary" :disabled="saving">
              {{ saving ? 'Creando...' : 'Crear usuario' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>
