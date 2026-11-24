<script setup>
import { onMounted, reactive, ref } from 'vue'
import PaginationBar from '../components/PaginationBar.vue'
import { api } from '../services/api'
import { useAuth } from '../stores/auth'

const auth = useAuth()

const categorias = ref([])
const total = ref(0)
const skip = ref(0)
const limit = 10

const loading = ref(false)
const error = ref('')
const feedback = ref('')

const showModal = ref(false)
const editingId = ref(null)
const saving = ref(false)
const formError = ref('')
const form = reactive({
  nombre: '',
  descripcion: '',
})

async function loadCategorias(newSkip = skip.value) {
  loading.value = true
  error.value = ''
  skip.value = newSkip
  try {
    const res = await api.categorias.listar({ skip: skip.value, limit })
    categorias.value = res.items
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
  form.descripcion = ''
  showModal.value = true
}

function openEdit(cat) {
  editingId.value = cat.id
  formError.value = ''
  form.nombre = cat.nombre
  form.descripcion = cat.descripcion || ''
  showModal.value = true
}

async function saveCategoria() {
  formError.value = ''
  saving.value = true
  const payload = {
    nombre: form.nombre.trim(),
    descripcion: form.descripcion.trim() || null,
  }
  try {
    if (editingId.value) {
      await api.categorias.actualizar(editingId.value, payload)
      feedback.value = 'Categoría actualizada.'
    } else {
      await api.categorias.crear(payload)
      feedback.value = 'Categoría creada.'
    }
    showModal.value = false
    await loadCategorias(editingId.value ? skip.value : 0)
  } catch (err) {
    formError.value = err.message
  } finally {
    saving.value = false
  }
}

async function deleteCategoria(cat) {
  if (!window.confirm(`¿Eliminar la categoría "${cat.nombre}"?`)) return
  error.value = ''
  feedback.value = ''
  try {
    await api.categorias.eliminar(cat.id)
    feedback.value = 'Categoría eliminada.'
    await loadCategorias(skip.value)
  } catch (err) {
    error.value = err.message
  }
}

onMounted(() => loadCategorias(0))
</script>

<template>
  <div>
    <div class="page-header">
      <div>
        <h1 class="page-title">Categorías</h1>
        <p class="page-subtitle">Clasificación temática del catálogo bibliográfico.</p>
      </div>
      <div class="page-actions">
        <button v-if="auth.isStaff.value" type="button" class="btn btn-primary" @click="openCreate">
          + Nueva categoría
        </button>
      </div>
    </div>

    <div v-if="feedback" class="alert alert-success">{{ feedback }}</div>
    <div v-if="error" class="alert alert-error">{{ error }}</div>

    <div class="card">
      <div v-if="loading" class="empty-state">Cargando categorías...</div>
      <div v-else-if="categorias.length === 0" class="empty-state">No hay categorías registradas.</div>
      <div v-else class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Nombre</th>
              <th>Descripción</th>
              <th v-if="auth.isStaff.value">Acciones</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="cat in categorias" :key="cat.id">
              <td>{{ cat.id }}</td>
              <td><span class="badge">{{ cat.nombre }}</span></td>
              <td>{{ cat.descripcion || '—' }}</td>
              <td v-if="auth.isStaff.value">
                <div class="actions-cell">
                  <button type="button" class="btn btn-secondary btn-sm" @click="openEdit(cat)">
                    Editar
                  </button>
                  <button
                    v-if="auth.isAdmin.value"
                    type="button"
                    class="btn btn-danger btn-sm"
                    @click="deleteCategoria(cat)"
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

    <PaginationBar :total="total" :skip="skip" :limit="limit" @change="loadCategorias" />

    <div v-if="showModal" class="modal-backdrop" @click.self="showModal = false">
      <div class="modal">
        <div class="modal-header">
          <h2 class="card-title">{{ editingId ? 'Editar categoría' : 'Nueva categoría' }}</h2>
          <button type="button" class="btn btn-ghost btn-sm" @click="showModal = false">Cerrar</button>
        </div>
        <form @submit.prevent="saveCategoria">
          <div class="modal-body">
            <div v-if="formError" class="alert alert-error">{{ formError }}</div>
            <div class="field">
              <label for="cat-nombre">Nombre (3–50 caracteres)</label>
              <input id="cat-nombre" v-model="form.nombre" type="text" required minlength="3" maxlength="50" />
            </div>
            <div class="field">
              <label for="cat-desc">Descripción</label>
              <textarea id="cat-desc" v-model="form.descripcion" maxlength="200" />
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
