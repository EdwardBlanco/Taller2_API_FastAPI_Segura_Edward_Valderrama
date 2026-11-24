<script setup>
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../services/api'
import { useAuth } from '../stores/auth'

const auth = useAuth()
const router = useRouter()

const socioPerfil = ref(null)
const misPrestamos = ref([])
const misMultas = ref({ prestamos: [], total_adeudado: 0 })
const estadoFiltro = ref('')

const socioForm = reactive({
  nombre: '',
  telefono: '',
})
const savingPerfil = ref(false)
const perfilMsg = ref('')
const perfilErr = ref('')

const passForm = reactive({
  password_actual: '',
  password_nueva: '',
})
const savingPass = ref(false)
const passMsg = ref('')
const passErr = ref('')

async function loadSocioData() {
  if (!auth.isSocio.value) return
  try {
    const [perfil, prestamos, multas] = await Promise.all([
      api.socios.me(),
      api.socios.misPrestamos({ estado: estadoFiltro.value || undefined }),
      api.socios.misMultas(),
    ])
    socioPerfil.value = perfil
    socioForm.nombre = perfil.nombre
    socioForm.telefono = perfil.telefono || ''
    misPrestamos.value = prestamos
    misMultas.value = multas
  } catch (err) {
    perfilErr.value = err.message
  }
}

async function reloadMisPrestamos() {
  if (!auth.isSocio.value) return
  try {
    misPrestamos.value = await api.socios.misPrestamos({
      estado: estadoFiltro.value || undefined,
    })
  } catch (err) {
    perfilErr.value = err.message
  }
}

async function saveSocioPerfil() {
  perfilErr.value = ''
  perfilMsg.value = ''
  savingPerfil.value = true
  try {
    const updated = await api.socios.actualizarMe({
      nombre: socioForm.nombre.trim(),
      telefono: socioForm.telefono.trim() || null,
    })
    socioPerfil.value = updated
    await auth.refreshUser()
    perfilMsg.value = 'Datos de socio actualizados.'
  } catch (err) {
    perfilErr.value = err.message
  } finally {
    savingPerfil.value = false
  }
}

async function handleChangePassword() {
  passErr.value = ''
  passMsg.value = ''
  savingPass.value = true
  try {
    await api.auth.cambiarPassword({
      password_actual: passForm.password_actual,
      password_nueva: passForm.password_nueva,
    })
    passForm.password_actual = ''
    passForm.password_nueva = ''
    passMsg.value = 'Contraseña actualizada. Tus sesiones anteriores fueron revocadas; vuelve a iniciar sesión.'
    setTimeout(async () => {
      await auth.logout()
      router.push('/login')
    }, 1500)
  } catch (err) {
    passErr.value = err.message
  } finally {
    savingPass.value = false
  }
}

onMounted(loadSocioData)
</script>

<template>
  <div class="stack-md">
    <div class="page-header" style="margin-bottom: 0">
      <div>
        <h1 class="page-title">Mi cuenta</h1>
        <p class="page-subtitle">Información de usuario, cambio de contraseña y resumen personal.</p>
      </div>
    </div>

    <div class="two-col">
      <!-- Info de usuario -->
      <section class="card">
        <div class="card-header">
          <h2 class="card-title">Perfil de usuario</h2>
        </div>
        <div class="card-body">
          <dl class="detail-list">
            <dt>Nombre</dt>
            <dd>{{ auth.user.value?.nombre }}</dd>
            <dt>Correo</dt>
            <dd>{{ auth.user.value?.email }}</dd>
            <dt>Rol</dt>
            <dd><span class="badge badge-primary">{{ auth.user.value?.rol }}</span></dd>
            <dt>Estado</dt>
            <dd>
              <span class="badge" :class="auth.user.value?.activo ? 'badge-success' : 'badge-danger'">
                {{ auth.user.value?.activo ? 'Activo' : 'Inactivo' }}
              </span>
            </dd>
            <dt>Creado</dt>
            <dd>{{ auth.user.value?.creado_en?.slice(0, 10) }}</dd>
          </dl>
        </div>
      </section>

      <!-- Cambiar contraseña -->
      <section class="card">
        <div class="card-header">
          <h2 class="card-title">Cambiar contraseña</h2>
        </div>
        <div class="card-body">
          <div v-if="passErr" class="alert alert-error">{{ passErr }}</div>
          <div v-if="passMsg" class="alert alert-success">{{ passMsg }}</div>
          <form @submit.prevent="handleChangePassword">
            <div class="field">
              <label for="pw-actual">Contraseña actual</label>
              <input id="pw-actual" v-model="passForm.password_actual" type="password" required />
            </div>
            <div class="field">
              <label for="pw-nueva">Nueva contraseña</label>
              <input
                id="pw-nueva"
                v-model="passForm.password_nueva"
                type="password"
                required
                minlength="8"
                maxlength="64"
                placeholder="Mayúscula, minúscula y número"
              />
            </div>
            <button type="submit" class="btn btn-primary" :disabled="savingPass">
              {{ savingPass ? 'Actualizando...' : 'Actualizar contraseña' }}
            </button>
          </form>
        </div>
      </section>
    </div>

    <!-- Sección exclusiva para rol socio -->
    <template v-if="auth.isSocio.value">
      <div class="two-col">
        <section class="card">
          <div class="card-header">
            <h2 class="card-title">Mis datos de socio</h2>
          </div>
          <div class="card-body">
            <div v-if="perfilErr" class="alert alert-error">{{ perfilErr }}</div>
            <div v-if="perfilMsg" class="alert alert-success">{{ perfilMsg }}</div>
            <form @submit.prevent="saveSocioPerfil">
              <div class="field">
                <label for="mp-nombre">Nombre</label>
                <input id="mp-nombre" v-model="socioForm.nombre" type="text" required minlength="2" maxlength="100" />
              </div>
              <div class="field">
                <label for="mp-tel">Teléfono</label>
                <input id="mp-tel" v-model="socioForm.telefono" type="text" placeholder="+57 3001234567" />
              </div>
              <button type="submit" class="btn btn-primary" :disabled="savingPerfil">
                {{ savingPerfil ? 'Guardando...' : 'Guardar cambios' }}
              </button>
            </form>
          </div>
        </section>

        <section class="card">
          <div class="card-header">
            <h2 class="card-title">Mis multas pendientes</h2>
            <span class="badge" :class="misMultas.total_adeudado > 0 ? 'badge-warning' : 'badge-success'">
              Total adeudado: ${{ Number(misMultas.total_adeudado || 0).toFixed(2) }}
            </span>
          </div>
          <div class="card-body">
            <div v-if="misMultas.prestamos.length === 0" class="empty-state" style="padding: 16px">
              No tienes multas pendientes.
            </div>
            <div v-else class="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Préstamo</th>
                    <th>Libro ID</th>
                    <th>Límite</th>
                    <th>Multa</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="m in misMultas.prestamos" :key="m.id">
                    <td>#{{ m.id }}</td>
                    <td>{{ m.libro_id }}</td>
                    <td>{{ m.fecha_limite }}</td>
                    <td>${{ m.multa }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </section>
      </div>

      <section class="card">
        <div class="card-header">
          <h2 class="card-title">Mis préstamos</h2>
          <select
            v-model="estadoFiltro"
            style="width: auto"
            @change="reloadMisPrestamos"
          >
            <option value="">Todos los estados</option>
            <option value="activo">Activos</option>
            <option value="vencido">Vencidos</option>
            <option value="devuelto">Devueltos</option>
          </select>
        </div>
        <div v-if="misPrestamos.length === 0" class="empty-state">No registras préstamos en este estado.</div>
        <div v-else class="table-wrap">
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>Libro ID</th>
                <th>Préstamo</th>
                <th>Límite</th>
                <th>Devolución</th>
                <th>Estado</th>
                <th>Multa</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="p in misPrestamos" :key="p.id">
                <td>#{{ p.id }}</td>
                <td>{{ p.libro_id }}</td>
                <td>{{ p.fecha_prestamo }}</td>
                <td>{{ p.fecha_limite }}</td>
                <td>{{ p.fecha_devolucion || '—' }}</td>
                <td><span class="badge">{{ p.estado }}</span></td>
                <td>{{ p.multa > 0 ? `$${p.multa}` : '—' }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>
    </template>
  </div>
</template>
