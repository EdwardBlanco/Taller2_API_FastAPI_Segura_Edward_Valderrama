<script setup>
import { onMounted, reactive, ref } from 'vue'
import PaginationBar from '../components/PaginationBar.vue'
import { api } from '../services/api'
import { useAuth } from '../stores/auth'

const auth = useAuth()

const libros = ref([])
const total = ref(0)
const skip = ref(0)
const limit = 12

const autores = ref([])
const categorias = ref([])

const loading = ref(false)
const error = ref('')
const feedback = ref('')

const filters = reactive({
  buscar: '',
  autor: '',
  categoria_id: '',
  desde: '',
  hasta: '',
  orden: '',
})

// Modal detalle
const detailBook = ref(null)
const coverUploading = ref(false)
const coverError = ref('')

// Modal crear/editar
const showFormModal = ref(false)
const editingId = ref(null)
const saving = ref(false)
const formError = ref('')
const coverFile = ref(null)

const form = reactive({
  titulo: '',
  isbn: '',
  anio_publicacion: new Date().getFullYear(),
  ejemplares: 1,
  autor_id: '',
  categoria_ids: [],
})

async function loadCatalogRefs() {
  try {
    const [aRes, cRes] = await Promise.all([
      api.autores.listar({ skip: 0, limit: 100 }),
      api.categorias.listar({ skip: 0, limit: 100 }),
    ])
    autores.value = aRes.items
    categorias.value = cRes.items
  } catch {
    // Referencias opcionales para filtros
  }
}

async function loadLibros(newSkip = skip.value) {
  loading.value = true
  error.value = ''
  skip.value = newSkip
  try {
    const res = await api.libros.listar({
      skip: skip.value,
      limit,
      buscar: filters.buscar.trim() || undefined,
      autor: filters.autor.trim() || undefined,
      categoria_id: filters.categoria_id || undefined,
      desde: filters.desde || undefined,
      hasta: filters.hasta || undefined,
      orden: filters.orden || undefined,
    })
    libros.value = res.items
    total.value = res.total
  } catch (err) {
    error.value = err.message
  } finally {
    loading.value = false
  }
}

function resetFilters() {
  filters.buscar = ''
  filters.autor = ''
  filters.categoria_id = ''
  filters.desde = ''
  filters.hasta = ''
  filters.orden = ''
  loadLibros(0)
}

function openCreateModal() {
  editingId.value = null
  formError.value = ''
  coverFile.value = null
  form.titulo = ''
  form.isbn = ''
  form.anio_publicacion = new Date().getFullYear()
  form.ejemplares = 1
  form.autor_id = autores.value[0]?.id || ''
  form.categoria_ids = categorias.value[0] ? [categorias.value[0].id] : []
  showFormModal.value = true
}

function openEditModal(libro) {
  editingId.value = libro.id
  formError.value = ''
  coverFile.value = null
  form.titulo = libro.titulo
  form.isbn = libro.isbn
  form.anio_publicacion = libro.anio_publicacion
  form.ejemplares = libro.ejemplares
  form.autor_id = libro.autor?.id || ''
  form.categoria_ids = (libro.categorias || []).map((c) => c.id)
  showFormModal.value = true
}

function handleFileSelect(event) {
  coverFile.value = event.target.files?.[0] || null
}

async function saveLibro() {
  formError.value = ''
  if (!form.categoria_ids.length) {
    formError.value = 'Selecciona al menos una categoría.'
    return
  }

  saving.value = true
  try {
    if (editingId.value) {
      await api.libros.actualizar(editingId.value, {
        titulo: form.titulo.trim(),
        isbn: form.isbn.trim(),
        anio_publicacion: Number(form.anio_publicacion),
        ejemplares: Number(form.ejemplares),
        autor_id: Number(form.autor_id),
        categoria_ids: form.categoria_ids.map(Number),
      })
      feedback.value = 'Libro actualizado correctamente.'
    } else if (coverFile.value) {
      const fd = new FormData()
      fd.append('titulo', form.titulo.trim())
      fd.append('isbn', form.isbn.trim())
      fd.append('anio_publicacion', String(form.anio_publicacion))
      fd.append('ejemplares', String(form.ejemplares))
      fd.append('autor_id', String(form.autor_id))
      fd.append('categoria_ids', JSON.stringify(form.categoria_ids.map(Number)))
      fd.append('portada', coverFile.value)
      await api.libros.crearConPortada(fd)
      feedback.value = 'Libro creado con portada correctamente.'
    } else {
      await api.libros.crear({
        titulo: form.titulo.trim(),
        isbn: form.isbn.trim(),
        anio_publicacion: Number(form.anio_publicacion),
        ejemplares: Number(form.ejemplares),
        autor_id: Number(form.autor_id),
        categoria_ids: form.categoria_ids.map(Number),
      })
      feedback.value = 'Libro creado correctamente.'
    }
    showFormModal.value = false
    await loadLibros(editingId.value ? skip.value : 0)
  } catch (err) {
    formError.value = err.message
  } finally {
    saving.value = false
  }
}

async function openDetail(libroId) {
  coverError.value = ''
  try {
    detailBook.value = await api.libros.obtener(libroId)
  } catch (err) {
    error.value = err.message
  }
}

async function handleUploadCover(event) {
  const file = event.target.files?.[0]
  if (!file || !detailBook.value) return
  coverError.value = ''
  coverUploading.value = true
  try {
    await api.libros.subirPortada(detailBook.value.id, file)
    detailBook.value = await api.libros.obtener(detailBook.value.id)
    feedback.value = 'Portada actualizada.'
    await loadLibros(skip.value)
  } catch (err) {
    coverError.value = err.message
  } finally {
    coverUploading.value = false
    event.target.value = ''
  }
}

async function handleDeleteCover() {
  if (!detailBook.value) return
  coverError.value = ''
  coverUploading.value = true
  try {
    await api.libros.eliminarPortada(detailBook.value.id)
    detailBook.value = await api.libros.obtener(detailBook.value.id)
    feedback.value = 'Portada eliminada.'
    await loadLibros(skip.value)
  } catch (err) {
    coverError.value = err.message
  } finally {
    coverUploading.value = false
  }
}

async function handleDeleteLibro(libro) {
  if (!window.confirm(`¿Eliminar el libro "${libro.titulo}"?`)) return
  error.value = ''
  feedback.value = ''
  try {
    await api.libros.eliminar(libro.id)
    feedback.value = 'Libro eliminado.'
    if (detailBook.value?.id === libro.id) detailBook.value = null
    await loadLibros(skip.value)
  } catch (err) {
    error.value = err.message
  }
}

onMounted(async () => {
  await Promise.all([loadCatalogRefs(), loadLibros(0)])
})
</script>

<template>
  <div>
    <div class="page-header">
      <div>
        <h1 class="page-title">Catálogo de Libros</h1>
        <p class="page-subtitle">Explora los ejemplares disponibles, filtra por autor, categoría o año.</p>
      </div>
      <div class="page-actions">
        <button v-if="auth.isStaff.value" type="button" class="btn btn-primary" @click="openCreateModal">
          + Nuevo libro
        </button>
      </div>
    </div>

    <div v-if="feedback" class="alert alert-success">{{ feedback }}</div>
    <div v-if="error" class="alert alert-error">{{ error }}</div>

    <form class="filters-bar" @submit.prevent="loadLibros(0)">
      <div class="filter-field">
        <label for="f-buscar">Título</label>
        <input id="f-buscar" v-model="filters.buscar" type="search" placeholder="Buscar título..." />
      </div>
      <div class="filter-field">
        <label for="f-autor">Autor</label>
        <input id="f-autor" v-model="filters.autor" type="text" placeholder="Nombre del autor" />
      </div>
      <div class="filter-field">
        <label for="f-cat">Categoría</label>
        <select id="f-cat" v-model="filters.categoria_id">
          <option value="">Todas</option>
          <option v-for="cat in categorias" :key="cat.id" :value="cat.id">
            {{ cat.nombre }}
          </option>
        </select>
      </div>
      <div class="filter-field compact">
        <label for="f-desde">Desde</label>
        <input id="f-desde" v-model="filters.desde" type="number" min="1450" placeholder="Año" />
      </div>
      <div class="filter-field compact">
        <label for="f-hasta">Hasta</label>
        <input id="f-hasta" v-model="filters.hasta" type="number" min="1450" placeholder="Año" />
      </div>
      <div class="filter-field compact">
        <label for="f-orden">Orden</label>
        <select id="f-orden" v-model="filters.orden">
          <option value="">Por defecto</option>
          <option value="titulo">Título (A–Z)</option>
          <option value="anio">Año (asc)</option>
          <option value="-anio">Año (desc)</option>
        </select>
      </div>
      <div class="actions-cell">
        <button type="submit" class="btn btn-primary">Filtrar</button>
        <button type="button" class="btn btn-secondary" @click="resetFilters">Limpiar</button>
      </div>
    </form>

    <div v-if="loading" class="card empty-state">Cargando catálogo...</div>

    <div v-else-if="libros.length === 0" class="card empty-state">
      No se encontraron libros con los criterios seleccionados.
    </div>

    <div v-else class="books-grid">
      <article v-for="libro in libros" :key="libro.id" class="book-card">
        <div class="book-cover-box">
          <img
            v-if="libro.miniatura_url || libro.portada_url"
            :src="libro.miniatura_url || libro.portada_url"
            :alt="`Portada de ${libro.titulo}`"
          />
          <div v-else class="book-cover-placeholder">Sin portada</div>
        </div>

        <div class="book-body">
          <h2 class="book-title">{{ libro.titulo }}</h2>
          <p class="book-meta">{{ libro.autor?.nombre }} · {{ libro.anio_publicacion }}</p>
          <p class="book-meta">ISBN: {{ libro.isbn }}</p>
          <div class="book-tags">
            <span v-for="cat in libro.categorias" :key="cat.id" class="badge">
              {{ cat.nombre }}
            </span>
          </div>
        </div>

        <div class="book-footer">
          <span
            class="badge"
            :class="libro.disponibles > 0 ? 'badge-success' : 'badge-danger'"
          >
            {{ libro.disponibles }} / {{ libro.ejemplares }} disp.
          </span>
          <div class="actions-cell">
            <button type="button" class="btn btn-secondary btn-sm" @click="openDetail(libro.id)">
              Ver
            </button>
            <button
              v-if="auth.isStaff.value"
              type="button"
              class="btn btn-secondary btn-sm"
              @click="openEditModal(libro)"
            >
              Editar
            </button>
            <button
              v-if="auth.isAdmin.value"
              type="button"
              class="btn btn-danger btn-sm"
              @click="handleDeleteLibro(libro)"
            >
              Eliminar
            </button>
          </div>
        </div>
      </article>
    </div>

    <PaginationBar :total="total" :skip="skip" :limit="limit" @change="loadLibros" />

    <!-- Modal Detalle y Portada -->
    <div v-if="detailBook" class="modal-backdrop" @click.self="detailBook = null">
      <div class="modal">
        <div class="modal-header">
          <h2 class="card-title">{{ detailBook.titulo }}</h2>
          <button type="button" class="btn btn-ghost btn-sm" @click="detailBook = null">Cerrar</button>
        </div>
        <div class="modal-body stack-md">
          <div v-if="coverError" class="alert alert-error">{{ coverError }}</div>

          <div
            v-if="detailBook.portada_url"
            style="text-align: center; background: var(--surface-subtle); padding: 12px; border-radius: 6px"
          >
            <img
              :src="detailBook.portada_url"
              :alt="detailBook.titulo"
              style="max-height: 240px; max-width: 100%; border-radius: 4px"
            />
          </div>

          <dl class="detail-list">
            <dt>Autor</dt>
            <dd>{{ detailBook.autor?.nombre }}</dd>
            <dt>ISBN</dt>
            <dd>{{ detailBook.isbn }}</dd>
            <dt>Año publicación</dt>
            <dd>{{ detailBook.anio_publicacion }}</dd>
            <dt>Ejemplares</dt>
            <dd>{{ detailBook.disponibles }} disponibles de {{ detailBook.ejemplares }}</dd>
            <dt>Categorías</dt>
            <dd>
              <span
                v-for="c in detailBook.categorias"
                :key="c.id"
                class="badge"
                style="margin-right: 4px"
              >
                {{ c.nombre }}
              </span>
            </dd>
          </dl>

          <div v-if="auth.isStaff.value" style="border-top: 1px solid var(--border); padding-top: 12px">
            <p class="field-label" style="margin-bottom: 8px">Gestión de portada (Cloudinary)</p>
            <div class="actions-cell">
              <label class="btn btn-secondary btn-sm" style="cursor: pointer">
                {{ coverUploading ? 'Subiendo...' : detailBook.portada_url ? 'Reemplazar portada' : 'Subir portada' }}
                <input
                  type="file"
                  accept="image/jpeg,image/png,image/webp"
                  style="display: none"
                  :disabled="coverUploading"
                  @change="handleUploadCover"
                />
              </label>
              <button
                v-if="detailBook.portada_url"
                type="button"
                class="btn btn-danger btn-sm"
                :disabled="coverUploading"
                @click="handleDeleteCover"
              >
                Quitar portada
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Modal Crear / Editar Libro -->
    <div v-if="showFormModal" class="modal-backdrop" @click.self="showFormModal = false">
      <div class="modal">
        <div class="modal-header">
          <h2 class="card-title">{{ editingId ? 'Editar libro' : 'Nuevo libro' }}</h2>
          <button type="button" class="btn btn-ghost btn-sm" @click="showFormModal = false">Cerrar</button>
        </div>
        <form @submit.prevent="saveLibro">
          <div class="modal-body">
            <div v-if="formError" class="alert alert-error">{{ formError }}</div>

            <div class="field">
              <label for="lb-titulo">Título</label>
              <input id="lb-titulo" v-model="form.titulo" type="text" required maxlength="150" />
            </div>

            <div class="form-grid">
              <div class="field">
                <label for="lb-isbn">ISBN (13 dígitos)</label>
                <input
                  id="lb-isbn"
                  v-model="form.isbn"
                  type="text"
                  required
                  pattern="\d{13}"
                  placeholder="9788437604947"
                />
              </div>
              <div class="field">
                <label for="lb-anio">Año de publicación</label>
                <input
                  id="lb-anio"
                  v-model.number="form.anio_publicacion"
                  type="number"
                  required
                  min="1450"
                  :max="new Date().getFullYear()"
                />
              </div>
            </div>

            <div class="form-grid">
              <div class="field">
                <label for="lb-ejemplares">Ejemplares (1–50)</label>
                <input
                  id="lb-ejemplares"
                  v-model.number="form.ejemplares"
                  type="number"
                  required
                  min="1"
                  max="50"
                />
              </div>
              <div class="field">
                <label for="lb-autor">Autor</label>
                <select id="lb-autor" v-model.number="form.autor_id" required>
                  <option value="" disabled>Selecciona un autor</option>
                  <option v-for="autor in autores" :key="autor.id" :value="autor.id">
                    {{ autor.nombre }}
                  </option>
                </select>
              </div>
            </div>

            <div class="field">
              <span class="field-label">Categorías (1 a 5)</span>
              <div class="checkbox-list">
                <label v-for="cat in categorias" :key="cat.id" class="checkbox-item">
                  <input v-model="form.categoria_ids" type="checkbox" :value="cat.id" />
                  <span>{{ cat.nombre }}</span>
                </label>
              </div>
            </div>

            <div v-if="!editingId" class="field">
              <label for="lb-portada">Portada (opcional · JPEG, PNG, WebP)</label>
              <input
                id="lb-portada"
                type="file"
                accept="image/jpeg,image/png,image/webp"
                @change="handleFileSelect"
              />
              <span class="hint">Si adjuntas imagen se usará el endpoint multipart /libros/con-portada.</span>
            </div>
          </div>

          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" @click="showFormModal = false">
              Cancelar
            </button>
            <button type="submit" class="btn btn-primary" :disabled="saving">
              {{ saving ? 'Guardando...' : 'Guardar' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>
