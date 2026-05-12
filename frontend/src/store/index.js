import { defineStore } from 'pinia'

export const useAppStore = defineStore('app', {
  state: () => ({
    user: null,
    token: '',
    sidebarCollapsed: false,
  }),
  getters: {
    isLoggedIn: (state) => !!state.token,
    userName: (state) => state.user?.username || '未登录',
  },
  actions: {
    setToken(token) { this.token = token; localStorage.setItem('token', token) },
    setUser(user) { this.user = user },
    toggleSidebar() { this.sidebarCollapsed = !this.sidebarCollapsed },
    logout() { this.token = ''; this.user = null; localStorage.removeItem('token') },
  },
})
