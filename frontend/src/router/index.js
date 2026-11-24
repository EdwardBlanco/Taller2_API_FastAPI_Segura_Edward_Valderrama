import { createRouter, createWebHistory } from 'vue-router'
import { useAuth } from '../stores/auth'

import AutoresView from '../views/AutoresView.vue'
import CategoriasView from '../views/CategoriasView.vue'
import LibrosView from '../views/LibrosView.vue'
import LoginView from '../views/LoginView.vue'
import MiCuentaView from '../views/MiCuentaView.vue'
import PrestamosView from '../views/PrestamosView.vue'
import RegistroView from '../views/RegistroView.vue'
import ReportesView from '../views/ReportesView.vue'
import SociosView from '../views/SociosView.vue'
import UsuariosView from '../views/UsuariosView.vue'

const routes = [
  { path: '/', redirect: '/libros' },
  { path: '/libros', name: 'libros', component: LibrosView },
  { path: '/autores', name: 'autores', component: AutoresView },
  { path: '/categorias', name: 'categorias', component: CategoriasView },
  { path: '/login', name: 'login', component: LoginView, meta: { guestOnly: true } },
  { path: '/registro', name: 'registro', component: RegistroView, meta: { guestOnly: true } },
  { path: '/prestamos', name: 'prestamos', component: PrestamosView, meta: { requiresAuth: true } },
  { path: '/mi-cuenta', name: 'mi-cuenta', component: MiCuentaView, meta: { requiresAuth: true } },
  {
    path: '/socios',
    name: 'socios',
    component: SociosView,
    meta: { requiresAuth: true, roles: ['admin', 'bibliotecario'] },
  },
  {
    path: '/reportes',
    name: 'reportes',
    component: ReportesView,
    meta: { requiresAuth: true, roles: ['admin', 'bibliotecario'] },
  },
  {
    path: '/usuarios',
    name: 'usuarios',
    component: UsuariosView,
    meta: { requiresAuth: true, roles: ['admin'] },
  },
  { path: '/:pathMatch(.*)*', redirect: '/libros' },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach(async (to) => {
  const auth = useAuth()
  if (!auth.state.initialized) {
    await auth.init()
  }

  if (to.meta.guestOnly && auth.isAuthenticated.value) {
    return '/libros'
  }

  if (to.meta.requiresAuth && !auth.isAuthenticated.value) {
    return { name: 'login', query: { redirect: to.fullPath } }
  }

  if (to.meta.roles && !to.meta.roles.includes(auth.role.value)) {
    return '/libros'
  }

  return true
})

export default router
