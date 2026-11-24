<script setup>
import { onMounted, reactive, ref } from 'vue'
import PaginationBar from '../components/PaginationBar.vue'
import { api } from '../services/api'
import { useAuth } from '../stores/auth'

const auth = useAuth()

const autores = ref([])
const total = ref(0)
const skip = ref(0)
const limit = 10
const nacionalidad = ref('')

const loading = ref(false)
const error = ref('')
const feedback = ref('')

const showModal = ref(false)
const editingId = ref(null)
const saving = ref(false)
const formError = ref('')
const form = reactive({
  nombre: '',
  nacionalidad: '',
  anio_nacimiento: '',
})

const selectedAutor = ref(null)
const autorLibros = ref([])
const loadingLibros = ref(false)

async function loadAutores(newSkip = skip.value) {
  loading.value = true
  error.value = ''
  skip.value = newSkip
  try {
    const res = await api.autores.listar({
      skip: skip.value,
      limit,
      nacionalidad: nacionalidad.value.trim() || undefined,
    })
    autores.value = res.items
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
  form.nacionalidad = ''
  form.anio_nacimiento = ''
  showModal.value = true
}

function openEdit(autor) {
  editingId.value = autor.id
  formError.value = ''
  form.nombre = autor.nombre
  form.nacionalidad = autor.nacionalidad || ''
  form.anio_nacimiento = autor.anio_nacimiento || ''
  showModal.value = true
}

async function saveAutor() {
  formError.value = ''
  saving.value = true
  const payload = {
    nombre: form.nombre.trim(),
    nacionalidad: form.nacionalidad.trim() || null,
    anio_nacimiento: form.anio_nacimiento ? Number(form.anio_nacimiento) : null,
  }
  try {
    if (editingId.value) {
      await api.autores.actualizar(editingId.value, payload)
      feedback.value = 'Autor actualizado.'
    } else {
      await api.autores.crear(payload)
      feedback.value = 'Autor creado.'
    }
    showModal.value = false
    await loadAutores(editingId.value ? skip.value : 0)
  } catch (err) {
    formError.value = err.message
  } finally {
    saving.value = false
  }
}

async function deleteAutor(autor) {
  if (!window.confirm(`¿Eliminar al autor "${autor.nombre}"?`)) return
  error.value = ''
  feedback.value = ''
  try {
    await api.autores.eliminar(autor.id)
    feedback.value = 'Autor eliminado.'
    await loadAutores(skip.value)
  } catch (err) {
    error.value = err.message
  }
}

async function viewAutorLibros(autor) {
  selectedAutor.value = autor
  autorLibros.value = []
  loadingLibros.value = true
  try {
    autorLibros.value = await api.autores.libros(autor.id)
  } catch (err) {
    error.value = err.message
  } finally {
    loadingLibros.value = false
  }
}

onMounted(() => loadAutores(0))
</script>

<template>
  <div>
    <div class="page-header">
      <div>
        <h1 class="page-title">Autores</h1>
        <p class="page-subtitle">Listado de autores registrados y sus obras en la biblioteca.</p>
      </div>
      <div class="page-actions">
        <button v-if="auth.isStaff.value" type="button" class="btn btn-primary" @click="openCreate">
          + Nuevo autor
        </button>
      </div>
    </div>

    <div v-if="feedback" class="alert alert-success">{{ feedback }}</div>
    <div v-if="error" class="alert alert-error">{{ error }}</div>

    <form class="filters-bar" @submit.prevent="loadAutores(0)">
      <div class="filter-field">
        <label for="f-nac">Filtrar por nacionalidad</label>
        <input id="f-nac" v-model="nacionalidad" type="text" placeholder="Ej. Colombiana" />
      </div>
      <div class="actions-cell">
        <button type="submit" class="btn btn-primary">Buscar</button>
        <button
          type="button"
          class="btn btn-secondary"
          @click="nacionalidad = ''; loadAutores(0)"
        >
          Limpiar
        </button>
      </div>
    </form>

    <div class="card">
      <div v-if="loading" class="empty-state">Cargando autores...</div>
      <div v-else-if="autores.length === 0" class="empty-state">No hay autores registrados.</div>
      <div v-else class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Nombre</th>
              <th>Nacionalidad</th>
              <th>Año nacimiento</th>
              <th>Acciones</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="autor in autores" :key="autor.id">
              <td>{{ autor.id }}</td>
              <td><strong>{{ autor.nombre }}</strong></td>
              <td>{{ autor.nacionalidad || '—' }}</td>
              <td>{{ autor.anio_nacimiento || '—' }}</td>
              <td>
                <div class="actions-cell">
                  <button
                    type="button"
                    class="btn btn-secondary btn-sm"
                    @click="viewAutorLibros(autor)"
                  >
                    Libros
                  </button>
                  <button
                    v-if="auth.isStaff.value"
                    type="button"
                    class="btn btn-secondary btn-sm"
                    @click="openEdit(autor)"
                  >
                    Editar
                  </button>
                  <button
                    v-if="auth.isAdmin.value"
                    type="button"
                    class="btn btn-danger btn-sm"
                    @click="deleteAutor(autor)"
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

    <PaginationBar :total="total" :skip="skip" :limit="limit" @change="loadAutores" />

    <!-- Modal libros del autor -->
    <div v-if="selectedAutor" class="modal-backdrop" @click.self="selectedAutor = null">
      <div class="modal">
        <div class="modal-header">
          <h2 class="card-title">Libros de {{ selectedAutor.nombre }}</h2>
          <button type="button" class="btn btn-ghost btn-sm" @click="selectedAutor = null">Cerrar</button>
        </div>
        <div class="modal-body">
          <div v-if="loadingLibros" class="empty-state">Cargando libros...</div>
          <div v-else-if="autorLibros.length === 0" class="empty-state">
            Este autor no tiene libros asociados.
          </div>
          <div v-else class="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Título</th>
                  <th>Año</th>
                  <th>ISBN</th>
                  <th>Disp.</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="libro in autorLibros" :key="libro.id">
                  <td>{{ libro.titulo }}</td>
                  <td>{{ libro.anio_publicacion }}</td>
                  <td>{{ libro.isbn }}</td>
                  <td>{{ libro.disponibles }} / {{ libro.ejemplares }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>

    <!-- Modal Crear / Editar -->
    <div v-if="showModal" class="modal-backdrop" @click.self="showModal = false">
      <div class="modal">
        <div class="modal-header">
          <h2 class="card-title">{{ editingId ? 'Editar autor' : 'Nuevo autor' }}</h2>
          <button type="button" class="btn btn-ghost btn-sm" @click="showModal = false">Cerrar</button>
        </div>
        <form @submit.prevent="saveAutor">
          <div class="modal-body">
            <div v-if="formError" class="alert alert-error">{{ formError }}</div>
            <div class="field">
              <label for="au-nombre">Nombre</label>
              <input id="au-nombre" v-model="form.nombre" type="text" required minlength="2" maxlength="100" />
            </div>
            <div class="field">
              <label for="au-nac">Nacionalidad</label>
              <input id="au-nac" v-model="form.nacionalidad" type="text" maxlength="60" />
            </div>
            <div class="field">
              <label for="au-anio">Año de nacimiento</label>
              <input
                id="au-anio"
                v-model="form.anio_nacimiento"
                type="number"
                min="1000"
                :max="new Date().getFullYear()"
              />
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
