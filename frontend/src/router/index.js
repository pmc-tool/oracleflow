import { createRouter, createWebHistory } from 'vue-router'
import LandingView from '../views/LandingView.vue'
import Process from '../views/MainView.vue'
import SimulationRunView from '../views/SimulationRunView.vue'
import ReportView from '../views/ReportView.vue'
import InteractionView from '../views/InteractionView.vue'
import NewSimulationView from '../views/NewSimulationView.vue'
import SitesView from '../views/SitesView.vue'
import SiteDetailView from '../views/SiteDetailView.vue'
import SignalsView from '../views/SignalsView.vue'
import EntitiesView from '../views/EntitiesView.vue'
import EntityDetailView from '../views/EntityDetailView.vue'
import CountriesView from '../views/CountriesView.vue'
import CountryDetailView from '../views/CountryDetailView.vue'
import IntelView from '../views/IntelView.vue'
import LoginView from '../views/LoginView.vue'
import RegisterView from '../views/RegisterView.vue'
import TermsView from '../views/TermsView.vue'
import PrivacyView from '../views/PrivacyView.vue'
import AdminDashboardView from '../views/admin/AdminDashboardView.vue'
import SettingsView from '../views/SettingsView.vue'

const routes = [
  {
    path: '/',
    name: 'Landing',
    component: LandingView
  },
  {
    path: '/login',
    name: 'Login',
    component: LoginView
  },
  {
    path: '/register',
    name: 'Register',
    component: RegisterView
  },
  {
    path: '/onboarding',
    name: 'Onboarding',
    component: () => import('../views/InterestPicker.vue')
  },
  {
    path: '/simulations',
    name: 'Simulations',
    component: () => import('../views/SimulationsView.vue')
  },
  {
    path: '/simulate',
    name: 'NewSimulation',
    component: NewSimulationView
  },
  {
    path: '/process/:projectId',
    name: 'Process',
    component: Process,
    props: true
  },
  {
    path: '/simulation/:simulationId/start',
    name: 'SimulationRun',
    component: SimulationRunView,
    props: true
  },
  {
    path: '/report/:reportId',
    name: 'Report',
    component: ReportView,
    props: true
  },
  {
    path: '/interaction/:reportId',
    name: 'Interaction',
    component: InteractionView,
    props: true
  },
  {
    path: '/dashboard',
    redirect: '/intel'
  },
  {
    path: '/sites',
    name: 'Sites',
    component: SitesView
  },
  {
    path: '/sites/:siteId',
    name: 'SiteDetail',
    component: SiteDetailView,
    props: true
  },
  {
    path: '/signals',
    name: 'Signals',
    component: SignalsView
  },
  {
    path: '/entities',
    name: 'Entities',
    component: EntitiesView
  },
  {
    path: '/entities/:entityId',
    name: 'EntityDetail',
    component: EntityDetailView,
    props: true
  },
  {
    path: '/countries',
    name: 'Countries',
    component: CountriesView
  },
  {
    path: '/countries/:code',
    name: 'CountryDetail',
    component: CountryDetailView,
    props: true
  },
  {
    path: '/intel',
    name: 'Intel',
    component: IntelView
  },
  {
    path: '/terms',
    name: 'Terms',
    component: TermsView
  },
  {
    path: '/privacy',
    name: 'Privacy',
    component: PrivacyView
  },
  {
    path: '/admin',
    name: 'Admin',
    component: AdminDashboardView
  },
  {
    path: '/settings',
    name: 'Settings',
    component: SettingsView
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('../views/NotFoundView.vue')
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

const PUBLIC_ROUTES = ['Login', 'Register', 'Landing', 'Terms', 'Privacy', 'NotFound']

function getUserRoleFromToken(token) {
  try {
    const payload = JSON.parse(atob(token.split('.')[1]))
    return payload.role || null
  } catch {
    return null
  }
}

router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('of_token')
  if (!PUBLIC_ROUTES.includes(to.name) && !token) {
    next({ name: 'Login' })
  } else if (to.name === 'Login' && token) {
    next({ path: '/intel' })
  } else if (to.path.startsWith('/admin') && token) {
    const role = getUserRoleFromToken(token) || localStorage.getItem('of_user_role')
    if (role !== 'admin') {
      next({ path: '/intel' })
    } else {
      next()
    }
  } else {
    next()
  }
})

export default router
