import './style.css'
import { createApp, defineComponent, h } from 'vue'
import { createRouter, createWebHistory, RouterView } from 'vue-router'
import DocumentChecker from './DocumentChecker.vue'
import JsonReportViewer from './JsonReportViewer.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', component: DocumentChecker },
    { path: '/report', component: JsonReportViewer },
  ],
})

const App = defineComponent({ render: () => h(RouterView) })

createApp(App).use(router).mount('#app')