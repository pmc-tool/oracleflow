import service from './index'

export const createCheckout = (plan) => service.post('/api/billing/create-checkout', { plan })
export const createPortal = () => service.post('/api/billing/portal')
export const getSubscription = () => service.get('/api/billing/subscription')
export const getUsage = () => service.get('/api/billing/usage')
