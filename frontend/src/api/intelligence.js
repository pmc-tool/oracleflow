import service from './index'

// Sites
export const listSites = () => service.get('/api/sites/')
export const discoverSite = (url, maxPages = 100) =>
  service.post('/api/sites/', { url, max_pages: maxPages })
export const getSite = (id) => service.get(`/api/sites/${id}`)
export const deactivateSite = (id) => service.delete(`/api/sites/${id}`)

// Signals
export const listSignals = (params = {}) => service.get('/api/signals/', { params })
export const getSignal = (id) => service.get(`/api/signals/${id}`)
export const getQuotes = () => service.get('/api/signals/quotes')
export const analyzeSignal = (signalId) => service.post('/api/signals/analyze', { signal_id: signalId })

// Chaos
export const getChaos = () => service.get('/api/chaos/')
export const getChaosHistory = (days = 7) => service.get('/api/chaos/history', { params: { days } })

// Entities
export const listEntities = (params = {}) => service.get('/api/entities/', { params })
export const getEntity = (id) => service.get(`/api/entities/${id}`)

// Countries
export const listCountries = () => service.get('/api/countries/')
export const getCountry = (code) => service.get(`/api/countries/${code}`)
export const getCountryRisk = (code) => service.get(`/api/countries/${code}/risk`)
export const getCountryBrief = (code) => service.get(`/api/countries/${code}/brief`)
export const getCountryTrend = (code, days = 30) => service.get(`/api/countries/${code}/trend`, { params: { days } })

// Alerts
export const listAlertRules = () => service.get('/api/alerts/rules')
export const createAlertRule = (rule) => service.post('/api/alerts/rules', rule)

// World Brief
export const getWorldBrief = () => service.get('/api/countries/GLOBAL/brief')

// Displacement
export const getDisplacement = () => service.get('/api/signals/displacement')

// Simulations
export const listSimulations = () => service.get('/api/simulation/list')
export const getSimulationHistory = (limit = 50) => service.get('/api/simulation/history', { params: { limit } })

// Site Pages & Diffs
export const getSitePages = (siteId) => service.get(`/api/sites/${siteId}/pages`)
export const getPageDiffs = (siteId, pageId) => service.get(`/api/sites/${siteId}/pages/${pageId}/diffs`)
export const getDiffDetail = (siteId, pageId, diffId) => service.get(`/api/sites/${siteId}/pages/${pageId}/diffs/${diffId}`)

// Watchlist
export const getWatchlist = () => service.get('/api/watchlist/')
export const createWatchlistItem = (data) => service.post('/api/watchlist/', data)
export const getWatchlistItem = (id) => service.get(`/api/watchlist/${id}`)
export const getWatchlistSignals = (id, params = {}) => service.get(`/api/watchlist/${id}/signals`, { params })
export const getWatchlistSentiment = (id) => service.get(`/api/watchlist/${id}/sentiment`)
export const getWatchlistCompare = () => service.get('/api/watchlist/compare')
export const deleteWatchlistItem = (id) => service.delete(`/api/watchlist/${id}`)

// User Preferences
export const getUserPreferences = () => service.get('/api/auth/preferences')
export const updateUserPreferences = (data) => service.put('/api/auth/preferences', data)

// Notifications
export const getNotifications = (params = {}) => service.get('/api/alerts/notifications', { params })
export const getUnreadCount = () => service.get('/api/alerts/notifications/count')
export const markNotificationRead = (id) => service.put(`/api/alerts/notifications/${id}/read`)
export const markAllNotificationsRead = () => service.put('/api/alerts/notifications/read-all')
