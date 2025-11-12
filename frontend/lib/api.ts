import axios from 'axios'

// Create axios instance with interceptor to suppress 401 errors in console
const apiClient = axios.create()

// Request interceptor (optional, for future use)
apiClient.interceptors.request.use(
  (config) => config,
  (error) => Promise.reject(error)
)

// Response interceptor - no special handling needed
// We use validateStatus in requests to handle 401s gracefully
apiClient.interceptors.response.use(
  (response) => response,
  (error) => Promise.reject(error)
)

export default apiClient

