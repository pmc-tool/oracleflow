import service from './index'

export const login = (email, password) => service.post('/api/auth/login', { email, password })
export const register = (data) => service.post('/api/auth/register', data)
export const getMe = () => service.get('/api/auth/me')
export const updateProfile = (data) => service.put('/api/auth/profile', data)
