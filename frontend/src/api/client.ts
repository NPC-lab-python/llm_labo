import axios from 'axios'

// Client Axios configuré pour l'API RAG
export const apiClient = axios.create({
  baseURL: '/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 120000, // 2 minutes pour les requêtes longues (génération)
})

// Intercepteur pour logger les erreurs
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error.response?.data || error.message)
    return Promise.reject(error)
  }
)
