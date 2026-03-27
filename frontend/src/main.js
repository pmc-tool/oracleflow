import { createApp } from 'vue'
import App from './App.vue'
import router from './router'

const app = createApp(App)

app.use(router)

app.config.errorHandler = (err, instance, info) => {
  console.error('Global Vue error:', err, info)
}

app.mount('#app')
