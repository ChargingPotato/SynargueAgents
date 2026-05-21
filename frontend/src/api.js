import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 120000,
})

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
