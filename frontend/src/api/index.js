import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 600000,
})

api.interceptors.response.use(
  (res) => res,
  (err) => {
    const message = err.response?.data?.detail || err.message || 'Unknown error'
    return Promise.reject(new Error(message))
  }
)

export function createSession() {
  return api.post('/session')
}

export function getState(threadId) {
  return api.get(`/state/${threadId}`)
}

export function startDebate(topic) {
  return api.post('/debate/start', { topic })
}

export function submitReview(threadId, researchDataA, researchDataB) {
  return api.post('/debate/review', {
    thread_id: threadId,
    research_data_a: researchDataA,
    research_data_b: researchDataB,
  })
}

export function submitFeedback(threadId, feedback) {
  return api.post('/debate/feedback', {
    thread_id: threadId,
    human_feedback: feedback,
  })
}
