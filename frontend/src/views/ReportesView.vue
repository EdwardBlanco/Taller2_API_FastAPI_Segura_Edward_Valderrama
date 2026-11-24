<script setup>
import { onMounted, ref } from 'vue'
import { api } from '../services/api'

const loading = ref(false)
const error = ref('')
const activeTab = ref('mas-prestados')
const limite = ref(5)

const resumen = ref(null)
const masPrestados = ref([])
const vencidos = ref([])
const sociosMultas = ref([])
const categorias = ref([])
const autores = ref([])

async function loadAll() {
  loading.value = true
  error.value = ''
  try {
    const [rRes, mpRes, vRes, smRes, cRes, aRes] = await Promise.all([
      api.reportes.resumen(),
      api.reportes.librosMasPrestados(limite.value),
      api.reportes.prestamosVencidos(),
      api.reportes.sociosConMultas(),
      api.reportes.categorias(),
      api.reportes.autores(),
    ])
    resumen.value = rRes
    masPrestados.value = mpRes
    vencidos.value = vRes
    sociosMultas.value = smRes
    categorias.value = cRes
    autores.value = aRes
  } catch (err) {
    error.value = err.message
  } finally {
    loading.value = false
  }
}

async function reloadMasPrestados() {
  try {
    masPrestados.value = await api.reportes.librosMasPrestados(limite.value)
  } catch (err) {
    error.value = err.message
  }
}

onMounted(loadAll)
</script>

<template>
  <div>
    <div class="page-header">
      <div>
        <h1 class="page-title">Reportes y Estadísticas</h1>
        <p class="page-subtitle">Indicadores generales de la biblioteca, vencimientos y multas.</p>
      </div>
      <div class="page-actions">
        <button type="button" class="btn btn-secondary" :disabled="loading" @click="loadAll">
          {{ loading ? 'Actualizando...' : 'Actualizar' }}
        </button>
      </div>
    </div>

    <div v-if="error" class="alert alert-error">{{ error }}</div>

    <div v-if="resumen" class="kpi-grid">
      <div class="kpi-card">
        <div class="kpi-label">Total de libros</div>
        <div class="kpi-value">{{ resumen.total_libros }}</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">Ejemplares totales</div>
        <div class="kpi-value">{{ resumen.total_ejemplares }}</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">Prestados actualmente</div>
        <div class="kpi-value">{{ resumen.total_prestados }}</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">Socios activos</div>
        <div class="kpi-value">{{ resumen.socios_activos }}</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">Préstamos vencidos</div>
        <div class="kpi-value">{{ resumen.prestamos_vencidos }}</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">Multas acumuladas</div>
        <div class="kpi-value">${{ Number(resumen.total_multas || 0).toFixed(2) }}</div>
      </div>
    </div>

    <div class="tabs">
      <button
        type="button"
        class="tab-btn"
        :class="{ active: activeTab === 'mas-prestados' }"
        @click="activeTab = 'mas-prestados'"
      >
        Más prestados
      </button>
      <button
        type="button"
        class="tab-btn"
        :class="{ active: activeTab === 'vencidos' }"
        @click="activeTab = 'vencidos'"
      >
        Préstamos vencidos ({{ vencidos.length }})
      </button>
      <button
        type="button"
        class="tab-btn"
        :class="{ active: activeTab === 'multas' }"
        @click="activeTab = 'multas'"
      >
        Socios con multas ({{ sociosMultas.length }})
      </button>
      <button
        type="button"
        class="tab-btn"
        :class="{ active: activeTab === 'categorias' }"
        @click="activeTab = 'categorias'"
      >
        Por categoría
      </button>
      <button
        type="button"
        class="tab-btn"
        :class="{ active: activeTab === 'autores' }"
        @click="activeTab = 'autores'"
      >
        Por autor
      </button>
    </div>

    <!-- Más prestados -->
    <section v-if="activeTab === 'mas-prestados'" class="card">
      <div class="card-header">
        <h2 class="card-title">Libros más prestados</h2>
        <div class="actions-cell">
          <label for="rep-limite" style="font-size: 12.5px">Límite:</label>
          <select id="rep-limite" v-model.number="limite" style="width: auto" @change="reloadMasPrestados">
            <option :value="5">Top 5</option>
            <option :value="10">Top 10</option>
            <option :value="20">Top 20</option>
          </select>
        </div>
      </div>
      <div v-if="masPrestados.length === 0" class="empty-state">Sin datos de préstamos todavía.</div>
      <div v-else class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Título</th>
              <th>Autor</th>
              <th>Total préstamos</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in masPrestados" :key="item.libro_id">
              <td>{{ item.libro_id }}</td>
              <td><strong>{{ item.titulo }}</strong></td>
              <td>{{ item.autor }}</td>
              <td>{{ item.total_prestamos }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <!-- Vencidos -->
    <section v-if="activeTab === 'vencidos'" class="card">
      <div class="card-header">
        <h2 class="card-title">Préstamos vencidos</h2>
      </div>
      <div v-if="vencidos.length === 0" class="empty-state">No hay préstamos vencidos.</div>
      <div v-else class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Préstamo</th>
              <th>Libro</th>
              <th>Socio</th>
              <th>Correo</th>
              <th>Límite</th>
              <th>Días retraso</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in vencidos" :key="item.prestamo_id">
              <td>#{{ item.prestamo_id }}</td>
              <td>{{ item.titulo }}</td>
              <td>{{ item.socio }}</td>
              <td>{{ item.email }}</td>
              <td>{{ item.fecha_limite }}</td>
              <td><span class="badge badge-danger">{{ item.dias_retraso }} días</span></td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <!-- Socios con multas -->
    <section v-if="activeTab === 'multas'" class="card">
      <div class="card-header">
        <h2 class="card-title">Socios con multas acumuladas</h2>
      </div>
      <div v-if="sociosMultas.length === 0" class="empty-state">No hay socios con multas registradas.</div>
      <div v-else class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>ID Socio</th>
              <th>Socio</th>
              <th>Préstamos con multa</th>
              <th>Total multas</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in sociosMultas" :key="item.socio_id">
              <td>{{ item.socio_id }}</td>
              <td><strong>{{ item.socio }}</strong></td>
              <td>{{ item.prestamos_con_multa }}</td>
              <td>${{ Number(item.total_multas || 0).toFixed(2) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <!-- Categorías -->
    <section v-if="activeTab === 'categorias'" class="card">
      <div class="card-header">
        <h2 class="card-title">Libros por categoría</h2>
      </div>
      <div v-if="categorias.length === 0" class="empty-state">Sin categorías registradas.</div>
      <div v-else class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Categoría</th>
              <th>Total libros</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in categorias" :key="item.categoria_id">
              <td>{{ item.categoria_id }}</td>
              <td><span class="badge">{{ item.nombre }}</span></td>
              <td>{{ item.total_libros }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <!-- Autores -->
    <section v-if="activeTab === 'autores'" class="card">
      <div class="card-header">
        <h2 class="card-title">Libros y préstamos por autor</h2>
      </div>
      <div v-if="autores.length === 0" class="empty-state">Sin autores registrados.</div>
      <div v-else class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Autor</th>
              <th>Libros</th>
              <th>Ejemplares</th>
              <th>Préstamos</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in autores" :key="item.autor_id">
              <td>{{ item.autor_id }}</td>
              <td><strong>{{ item.autor }}</strong></td>
              <td>{{ item.total_libros }}</td>
              <td>{{ item.total_ejemplares }}</td>
              <td>{{ item.total_prestamos }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
  </div>
</template>
