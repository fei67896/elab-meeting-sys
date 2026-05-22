import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import '@shared/styles/base.css'
import './styles/voice.css'

createApp(App).use(router).mount('#app')
