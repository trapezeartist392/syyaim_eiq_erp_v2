import { create } from 'zustand'
export const useAuth = create((set) => ({
  user: JSON.parse(localStorage.getItem('miq_user') || 'null'),
  token: localStorage.getItem('miq_token'),
  login: (user, token) => {
    localStorage.setItem('miq_token', token)
    localStorage.setItem('miq_user', JSON.stringify(user))
    set({ user, token })
  },
  logout: () => {
    localStorage.removeItem('miq_token')
    localStorage.removeItem('miq_user')
    set({ user: null, token: null })
  }
}))
