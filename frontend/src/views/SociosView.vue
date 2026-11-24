<script setup>
import { onMounted, reactive, ref } from 'vue'
import PaginationBar from '../components/PaginationBar.vue'
import { api } from '../services/api'
import { useAuth } from '../stores/auth'

const auth = useAuth()

const socios = ref([])
const total = ref(0)
const skip = ref(0)
const limit = 10
const filtroActivo = ref('')

const loading = ref(false)
const error = ref('')
const feedback = ref('')

const showModal = ref(false)
const editingId = ref(null)
const saving = ref(false)
const formError = ref('')
const form = reactive({
  nombre: '',
  email: '',
  telefono: '',
  activo: true,
})

const selectedSocio = ref(null)
const socioPrestamos = ref([])
const loadingPrestamos = ref(false)

async function loadSocios(newSkip = skip.value) {
  loading.value = true
  error.value = ''
  skip.value = newSkip
  try {
    const res = await api.socios.listar({
      skip: skip.value,
      limit,
      activo: filtroActivo.value === '' ? undefined : filtroActivo.value,
    })
    socios.value = res.items
    total.value = res.total
  } catch (err) {
    error.value = err.message
  } finally {
    loading.value = false
  }
}

function openCreate() {
  editingId.value = null
  formError.value = ''
  form.nombre = ''
  form.email = ''
  form.telefono = ''
  form.activo = true
  showModal.value = true
}

function openEdit(socio) {
  editingId.value = socio.id
  formError.value = ''
  form.nombre = socio.nombre
  form.email = socio.email
  form.telefono = socio.telefono || ''
  form.activo = socio.activo
  showModal.value = true
}

async function saveSocio() {
  formError.value = ''
  saving.value = true
  const payload = {
    nombre: form.nombre.trim(),
    email: form.email.trim(),
    telefono: form.telefono.trim() || null,
    activo: form.activo,
  }
  try {
    if (editingId.value) {
      await api.socios.actualizar(editingId.value, payload)
      feedback.value = 'Socio actualizado.'
    } else {
      await api.socios.crear(payload)
      feedback.value = 'Socio registrado.'
    }
    showModal.value = false
    await loadSocios(editingId.value ? skip.value : 0)
  } catch (err) {
    formError.value = err.message
  } finally {
    saving.value = false
  }
}

async function deleteSocio(socio) {
  if (!window.confirm(`¿Eliminar o dar de baja al socio "${socio.nombre}"?`)) return
  error.value = ''
  feedback.value = ''
  try {
    await api.socios.eliminar(socio.id)
    feedback.value = 'Operación completada sobre el socio.'
    await loadSocios(skip.value)
  } catch (err) {
    error.value = err.message
  }
}

async function viewPrestamos(socio) {
  selectedSocio.value = socio
  socioPrestamos.value = []
  loadingPrestamos.value = true
  try {
    socioPrestamos.value = await api.socios.prestamos(socio.id)
  } catch (err) {
    error.value = err.message
  } finally {
    loadingPrestamos.value = false
  }
}

onMounted(() => loadSocios(0))
</script>

<template>
  <div>
    <div class="page-header">
      <div>
        <h1 class="page-title">Socios</h1>
        <p class="page-subtitle">Administración de personas inscritas en la biblioteca.</p>
      </div>
      <div class="page-actions">
        <button type="button" class="btn btn-primary" @click="openCreate">+ Nuevo socio</button>
      </div>
    </div>

    <div v-if="feedback" class="alert alert-success">{{ feedback }}</div>
    <div v-if="error" class="alert alert-error">{{ error }}</div>

    <form class="filters-bar" @submit.prevent="loadSocios(0)">
      <div class="filter-field compact">
        <label for="fs-activo">Estado</label>
        <select id="fs-activo" v-model="filtroActivo">
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
      <div v-if="loading" class="empty-state">Cargando socios...</div>
      <div v-else-if="socios.length === 0" class="empty-state">No hay socios registrados.</div>
      <div v-else class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Nombre</th>
              <th>Correo</th>
              <th>Teléfono</th>
              <th>Estado</th>
              <th>Alta</th>
              <th>Acciones</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="socio in socios" :key="socio.id">
              <td>{{ socio.id }}</td>
              <td><strong>{{ socio.nombre }}</strong></td>
              <td>{{ socio.email }}</td>
              <td>{{ socio.telefono || '—' }}</td>
              <td>
                <span class="badge" :class="socio.activo ? 'badge-success' : 'badge-danger'">
                  {{ socio.activo ? 'Activo' : 'Inactivo' }}
                </span>
              </td>
              <td>{{ socio.fecha_alta?.slice(0, 10) }}</td>
              <td>
                <div class="actions-cell">
                  <button
                    type="button"
                    class="btn btn-secondary btn-sm"
                    @click="viewPrestamos(socio)"
                  >
                    Préstamos
                  </button>
                  <button type="button" class="btn btn-secondary btn-sm" @click="openEdit(socio)">
                    Editar
                  </button>
                  <button
                    v-if="auth.isAdmin.value"
                    type="button"
                    class="btn btn-danger btn-sm"
                    @click="deleteSocio(socio)"
                  >
                    Eliminar
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <PaginationBar :total="total" :skip="skip" :limit="limit" @change="loadSocios" />

    <!-- Modal préstamos del socio -->
    <div v-if="selectedSocio" class="modal-backdrop" @click.self="selectedSocio = null">
      <div class="modal">
        <div class="modal-header">
          <h2 class="card-title">Préstamos de {{ selectedSocio.nombre }}</h2>
          <button type="button" class="btn btn-ghost btn-sm" @click="selectedSocio = null">Cerrar</button>
        </div>
        <div class="modal-body">
          <div v-if="loadingPrestamos" class="empty-state">Cargando préstamos...</div>
          <div v-else-if="socioPrestamos.length === 0" class="empty-state">
            Este socio no registra préstamos.
          </div>
          <div v-else class="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Libro ID</th>
                  <th>Préstamo</th>
                  <th>Límite</th>
                  <th>Estado</th>
                  <th>Multa</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="p in socioPrestamos" :key="p.id">
                  <td>#{{ p.id }}</td>
                  <td>{{ p.libro_id }}</td>
                  <td>{{ p.fecha_prestamo }}</td>
                  <td>{{ p.fecha_limite }}</td>
                  <td><span class="badge">{{ p.estado }}</span></td>
                  <td>${{ p.multa }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>

    <!-- Modal Crear / Editar Socio -->
    <div v-if="showModal" class="modal-backdrop" @click.self="showModal = false">
      <div class="modal">
        <div class="modal-header">
          <h2 class="card-title">{{ editingId ? 'Editar socio' : 'Nuevo socio' }}</h2>
          <button type="button" class="btn btn-ghost btn-sm" @click="showModal = false">Cerrar</button>
        </div>
        <form @submit.prevent="saveSocio">
          <div class="modal-body">
            <div v-if="formError" class="alert alert-error">{{ formError }}</div>
            <div class="field">
              <label for="so-nombre">Nombre</label>
              <input id="so-nombre" v-model="form.nombre" type="text" required minlength="2" maxlength="100" />
            </div>
            <div class="field">
              <label for="so-email">Correo electrónico</label>
              <input id="so-email" v-model="form.email" type="email" required />
            </div>
            <div class="field">
              <label for="so-tel">Teléfono (opcional)</label>
              <input id="so-tel" v-model="form.telefono" type="text" placeholder="+57 3001234567" />
            </div>
            <div class="field">
              <label class="checkbox-item" style="width: fit-content">
                <input v-model="form.activo" type="checkbox" />
                <span>Socio activo</span>
              </label>
            </div>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" @click="showModal = false">Cancelar</button>
            <button type="submit" class="btn btn-primary" :disabled="saving">
              {{ saving ? 'Guardando...' : 'Guardar' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>
