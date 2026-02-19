import axios from 'axios'

const baseURL = import.meta.env.VITE_API_BASE || ''

const client = axios.create({
  baseURL,
  timeout: 15000,
})

export default client
