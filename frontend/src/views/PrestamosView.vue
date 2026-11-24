<script setup>
import { onMounted, reactive, ref } from 'vue'
import PaginationBar from '../components/PaginationBar.vue'
import { api } from '../services/api'
import { useAuth } from '../stores/auth'

const auth = useAuth()

const prestamos = ref([])
const total = ref(0)
const skip = ref(0)
const limit = 10

const librosRef = ref([])
const sociosRef = ref([])

const loading = ref(false)
const error = ref('')
const feedback = ref('')

const filters = reactive({
  estado: '',
  socio_id: '',
  libro_id: '',
})

const detailPrestamo = ref(null)

// Modal crear préstamo
const showCreateModal = ref(false)
const saving = ref(false)
const formError = ref('')
const createForm = reactive({
  libro_id: '',
  socio_id: '',
  fecha_prestamo: '',
  dias: 14,
})

// Modal devolución
const returnTarget = ref(null)
const returnDate = ref('')
const returning = ref(false)
const returnError = ref('')

function estadoBadge(estado) {
  if (estado === 'devuelto') return 'badge-success'
  if (estado === 'vencido') return 'badge-danger'
  return 'badge-primary'
}

function formatMoney(val) {
  return `$${Number(val || 0).toLocaleString('es-CO', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
}

async function loadRefs() {
  if (!auth.isStaff.value) return
  try {
    const [lRes, sRes] = await Promise.all([
      api.libros.listar({ skip: 0, limit: 100 }),
      api.socios.listar({ skip: 0, limit: 100 }),
    ])
    librosRef.value = lRes.items
    sociosRef.value = sRes.items
  } catch {
    // Opcional
  }
}

async function loadPrestamos(newSkip = skip.value) {
  loading.value = true
  error.value = ''
  skip.value = newSkip
  try {
    const res = await api.prestamos.listar({
      skip: skip.value,
      limit,
      estado: filters.estado || undefined,
      socio_id: filters.socio_id || undefined,
      libro_id: filters.libro_id || undefined,
    })
    prestamos.value = res.items
    total.value = res.total
  } catch (err) {
    error.value = err.message
  } finally {
    loading.value = false
  }
}

function resetFilters() {
  filters.estado = ''
  filters.socio_id = ''
  filters.libro_id = ''
  loadPrestamos(0)
}

async function openDetail(id) {
  error.value = ''
  try {
    detailPrestamo.value = await api.prestamos.obtener(id)
  } catch (err) {
    error.value = err.message
  }
}

function openCreateModal() {
  formError.value = ''
  createForm.libro_id = librosRef.value[0]?.id || ''
  createForm.socio_id = sociosRef.value[0]?.id || ''
  createForm.fecha_prestamo = ''
  createForm.dias = 14
  showCreateModal.value = true
}

async function submitCreate() {
  formError.value = ''
  saving.value = true
  try {
    await api.prestamos.crear({
      libro_id: Number(createForm.libro_id),
      socio_id: Number(createForm.socio_id),
      fecha_prestamo: createForm.fecha_prestamo || null,
      dias: Number(createForm.dias),
    })
    showCreateModal.value = false
    feedback.value = 'Préstamo registrado correctamente.'
    await Promise.all([loadPrestamos(0), loadRefs()])
  } catch (err) {
    formError.value = err.message
  } finally {
    saving.value = false
  }
}

function openReturnModal(prestamo) {
  returnTarget.value = prestamo
  returnDate.value = new Date().toISOString().slice(0, 10)
  returnError.value = ''
}

async function submitReturn() {
  if (!returnTarget.value) return
  returnError.value = ''
  returning.value = true
  try {
    await api.prestamos.devolver(returnTarget.value.id, {
      fecha_devolucion: returnDate.value || null,
    })
    returnTarget.value = null
    feedback.value = 'Devolución registrada.'
    await Promise.all([loadPrestamos(skip.value), loadRefs()])
  } catch (err) {
    returnError.value = err.message
  } finally {
    returning.value = false
  }
}

async function handlePagarMulta(prestamo) {
  if (!window.confirm(`¿Registrar el pago de la multa (${formatMoney(prestamo.multa)}) del préstamo #${prestamo.id}?`)) {
    return
  }
  error.value = ''
  feedback.value = ''
  try {
    await api.prestamos.pagarMulta(prestamo.id)
    feedback.value = `Multa del préstamo #${prestamo.id} marcada como pagada.`
    await loadPrestamos(skip.value)
  } catch (err) {
    error.value = err.message
  }
}

onMounted(async () => {
  await Promise.all([loadRefs(), loadPrestamos(0)])
})
</script>

<template>
  <div>
    <div class="page-header">
      <div>
        <h1 class="page-title">Préstamos</h1>
        <p class="page-subtitle">
          {{ auth.isStaff.value ? 'Gestión de préstamos, devoluciones y cobro de multas.' : 'Historial y estado de tus préstamos personales.' }}
        </p>
      </div>
      <div class="page-actions">
        <button v-if="auth.isStaff.value" type="button" class="btn btn-primary" @click="openCreateModal">
          + Registrar préstamo
        </button>
      </div>
    </div>

    <div v-if="feedback" class="alert alert-success">{{ feedback }}</div>
    <div v-if="error" class="alert alert-error">{{ error }}</div>

    <form class="filters-bar" @submit.prevent="loadPrestamos(0)">
      <div class="filter-field compact">
        <label for="fp-estado">Estado</label>
        <select id="fp-estado" v-model="filters.estado">
          <option value="">Todos</option>
          <option value="activo">Activo</option>
          <option value="vencido">Vencido</option>
          <option value="devuelto">Devuelto</option>
        </select>
      </div>
      <div v-if="auth.isStaff.value" class="filter-field compact">
        <label for="fp-socio">ID Socio</label>
        <input id="fp-socio" v-model="filters.socio_id" type="number" min="1" placeholder="Todos" />
      </div>
      <div class="filter-field compact">
        <label for="fp-libro">ID Libro</label>
        <input id="fp-libro" v-model="filters.libro_id" type="number" min="1" placeholder="Todos" />
      </div>
      <div class="actions-cell">
        <button type="submit" class="btn btn-primary">Filtrar</button>
        <button type="button" class="btn btn-secondary" @click="resetFilters">Limpiar</button>
      </div>
    </form>

    <div class="card">
      <div v-if="loading" class="empty-state">Cargando préstamos...</div>
      <div v-else-if="prestamos.length === 0" class="empty-state">No hay préstamos para mostrar.</div>
      <div v-else class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Libro ID</th>
              <th>Socio ID</th>
              <th>Préstamo</th>
              <th>Límite</th>
              <th>Devolución</th>
              <th>Estado</th>
              <th>Multa</th>
              <th>Acciones</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="p in prestamos" :key="p.id">
              <td>#{{ p.id }}</td>
              <td>{{ p.libro_id }}</td>
              <td>{{ p.socio_id }}</td>
              <td>{{ p.fecha_prestamo }}</td>
              <td>{{ p.fecha_limite }}</td>
              <td>{{ p.fecha_devolucion || '—' }}</td>
              <td>
                <span class="badge" :class="estadoBadge(p.estado)">{{ p.estado }}</span>
              </td>
              <td>
                <template v-if="p.multa > 0">
                  <span>{{ formatMoney(p.multa) }}</span>
                  <span
                    class="badge"
                    :class="p.multa_pagada ? 'badge-success' : 'badge-warning'"
                    style="margin-left: 6px"
                  >
                    {{ p.multa_pagada ? 'Pagada' : 'Pendiente' }}
                  </span>
                </template>
                <span v-else>—</span>
              </td>
              <td>
                <div class="actions-cell">
                  <button type="button" class="btn btn-secondary btn-sm" @click="openDetail(p.id)">
                    Detalle
                  </button>
                  <button
                    v-if="auth.isStaff.value && !p.fecha_devolucion"
                    type="button"
                    class="btn btn-primary btn-sm"
                    @click="openReturnModal(p)"
                  >
                    Devolver
                  </button>
                  <button
                    v-if="auth.isStaff.value && p.multa > 0 && !p.multa_pagada"
                    type="button"
                    class="btn btn-secondary btn-sm"
                    @click="handlePagarMulta(p)"
                  >
                    Pagar multa
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <PaginationBar :total="total" :skip="skip" :limit="limit" @change="loadPrestamos" />

    <!-- Modal Detalle -->
    <div v-if="detailPrestamo" class="modal-backdrop" @click.self="detailPrestamo = null">
      <div class="modal">
        <div class="modal-header">
          <h2 class="card-title">Préstamo #{{ detailPrestamo.id }}</h2>
          <button type="button" class="btn btn-ghost btn-sm" @click="detailPrestamo = null">Cerrar</button>
        </div>
        <div class="modal-body">
          <dl class="detail-list">
            <dt>Libro</dt>
            <dd>{{ detailPrestamo.libro?.titulo }} (ISBN: {{ detailPrestamo.libro?.isbn }})</dd>
            <dt>Socio</dt>
            <dd>{{ detailPrestamo.socio?.nombre }} ({{ detailPrestamo.socio?.email }})</dd>
            <dt>Estado</dt>
            <dd><span class="badge" :class="estadoBadge(detailPrestamo.estado)">{{ detailPrestamo.estado }}</span></dd>
            <dt>Fecha préstamo</dt>
            <dd>{{ detailPrestamo.fecha_prestamo }}</dd>
            <dt>Fecha límite</dt>
            <dd>{{ detailPrestamo.fecha_limite }}</dd>
            <dt>Fecha devolución</dt>
            <dd>{{ detailPrestamo.fecha_devolucion || 'Pendiente' }}</dd>
            <dt>Multa</dt>
            <dd>
              {{ formatMoney(detailPrestamo.multa) }}
              <span v-if="detailPrestamo.multa > 0">
                ({{ detailPrestamo.multa_pagada ? 'Pagada' : 'Sin pagar' }})
              </span>
            </dd>
            <dt>Registrado por</dt>
            <dd>{{ detailPrestamo.registrado_por_id ? `Usuario #${detailPrestamo.registrado_por_id}` : '—' }}</dd>
          </dl>
        </div>
      </div>
    </div>

    <!-- Modal Crear Préstamo -->
    <div v-if="showCreateModal" class="modal-backdrop" @click.self="showCreateModal = false">
      <div class="modal">
        <div class="modal-header">
          <h2 class="card-title">Registrar préstamo</h2>
          <button type="button" class="btn btn-ghost btn-sm" @click="showCreateModal = false">Cerrar</button>
        </div>
        <form @submit.prevent="submitCreate">
          <div class="modal-body">
            <div v-if="formError" class="alert alert-error">{{ formError }}</div>

            <div class="field">
              <label for="pr-libro">Libro</label>
              <select id="pr-libro" v-model.number="createForm.libro_id" required>
                <option value="" disabled>Selecciona un libro</option>
                <option v-for="l in librosRef" :key="l.id" :value="l.id">
                  #{{ l.id }} · {{ l.titulo }} ({{ l.disponibles }} disp.)
                </option>
              </select>
            </div>

            <div class="field">
              <label for="pr-socio">Socio</label>
              <select id="pr-socio" v-model.number="createForm.socio_id" required>
                <option value="" disabled>Selecciona un socio</option>
                <option v-for="s in sociosRef" :key="s.id" :value="s.id">
                  #{{ s.id }} · {{ s.nombre }} ({{ s.email }})
                </option>
              </select>
            </div>

            <div class="form-grid">
              <div class="field">
                <label for="pr-fecha">Fecha préstamo (opcional)</label>
                <input id="pr-fecha" v-model="createForm.fecha_prestamo" type="date" />
              </div>
              <div class="field">
                <label for="pr-dias">Días de préstamo (1–30)</label>
                <input id="pr-dias" v-model.number="createForm.dias" type="number" min="1" max="30" required />
              </div>
            </div>
          </div>

          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" @click="showCreateModal = false">Cancelar</button>
            <button type="submit" class="btn btn-primary" :disabled="saving">
              {{ saving ? 'Registrando...' : 'Registrar' }}
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- Modal Devolución -->
    <div v-if="returnTarget" class="modal-backdrop" @click.self="returnTarget = null">
      <div class="modal">
        <div class="modal-header">
          <h2 class="card-title">Devolución préstamo #{{ returnTarget.id }}</h2>
          <button type="button" class="btn btn-ghost btn-sm" @click="returnTarget = null">Cerrar</button>
        </div>
        <form @submit.prevent="submitReturn">
          <div class="modal-body">
            <div v-if="returnError" class="alert alert-error">{{ returnError }}</div>
            <div class="field">
              <label for="dev-fecha">Fecha de devolución</label>
              <input id="dev-fecha" v-model="returnDate" type="date" />
              <span class="hint">Si se deja vacía, el backend usa la fecha actual.</span>
            </div>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" @click="returnTarget = null">Cancelar</button>
            <button type="submit" class="btn btn-primary" :disabled="returning">
              {{ returning ? 'Confirmando...' : 'Confirmar devolución' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>
