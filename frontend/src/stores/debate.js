import { defineStore } from 'pinia'
import * as api from '../api/index.js'

export const useDebateStore = defineStore('debate', {
  state: () => ({
    threadId: null,
    phase: 'input',
    activePhase: 'input',
    availablePhases: ['input'],
    state: {},
    loading: false,
    loadingMessage: '',
    error: null,
  }),

  getters: {
    topic: (s) => s.state.topic || '',
    sides: (s) => s.state.sides || {},
    researchA: (s) => s.state.research_data_a || [],
    researchB: (s) => s.state.research_data_b || [],
    arguments: (s) => s.state.arguments || {},
    rebuttals: (s) => s.state.rebuttals || {},
    finalSummary: (s) => s.state.final_summary || '',
    tendencyScore: (s) => s.state.tendency_score || { side_a: 0.5, side_b: 0.5 },
    isAtBreakpoint: (s) => ['review_research', 'provide_feedback', 'results'].includes(s.phase),
    progressMessage: (s) => s.state.progress_message || s.loadingMessage || '',
    errorTraceback: (s) => s.state._error_traceback || '',
  },

  actions: {
    _addPhase(phase) {
      if (!this.availablePhases.includes(phase)) {
        this.availablePhases.push(phase)
      }
      this.activePhase = phase
      this.phase = phase
    },

    setActivePhase(phase) {
      if (this.availablePhases.includes(phase)) {
        this.activePhase = phase
      }
    },

    _stopPolling() {
      if (this._pollTimer != null) {
        clearTimeout(this._pollTimer)
        this._pollTimer = null
      }
    },

    async startDebate(topic) {
      this.loading = true
      this.loadingMessage = 'Agent A 与 Agent B 正在交替进行全网深度调查，请耐心等待...'
      this.error = null
      try {
        const { data } = await api.startDebate(topic)
        this.threadId = data.thread_id
        this.phase = data.phase
        this.state = data.state
        if (data.phase === 'researching') {
          this._startPolling()
        } else {
          this.loading = false
          this._addPhase(data.phase)
        }
      } catch (err) {
        this.error = err.response?.data?.detail || err.message
        this.loading = false
      }
    },

    _startPolling() {
      this._stopPolling()
      const POLL_INTERVAL = 2000
      const MAX_POLLS = 200
      let count = 0

      const poll = async () => {
        if (count >= MAX_POLLS) {
          this.error = '辩论调研超时 (超过最大轮询次数)，请重试'
          this.loading = false
          this._stopPolling()
          return
        }
        count++
        try {
          const { data } = await api.getState(this.threadId)
          this.phase = data.phase
          this.state = data.state
          if (data.state?.progress_message) {
            this.loadingMessage = data.state.progress_message
          }
          if (data.phase === 'researching') {
            this._pollTimer = setTimeout(poll, POLL_INTERVAL)
          } else if (data.phase === 'error') {
            const errMsg = data.state?._error || '辩论执行过程中发生错误'
            const errType = data.state?._error_type || ''
            const errTrace = data.state?._error_traceback || ''
            this.error = errType ? `[${errType}] ${errMsg}` : errMsg
            if (errTrace) {
              console.error('=== 错误堆栈 ===\n' + errTrace)
            }
            this.loading = false
            this._stopPolling()
          } else {
            this.loading = false
            this._stopPolling()
            this._addPhase(data.phase)
          }
        } catch (err) {
          this.error = `[网络错误] ${err.response?.data?.detail || err.message}`
          this.loading = false
          this._stopPolling()
        }
      }
      this._pollTimer = setTimeout(poll, POLL_INTERVAL)
    },

    async submitReview(dataA, dataB) {
      this.loading = true
      this.loadingMessage = '双方辩手正在立论与交叉反驳...'
      this.error = null
      try {
        const { data } = await api.submitReview(this.threadId, dataA, dataB)
        this.phase = data.phase
        this.state = data.state
        this._addPhase(data.phase)
      } catch (err) {
        this.error = err.response?.data?.detail || err.message
      } finally {
        this.loading = false
      }
    },

    async submitFeedback(feedback) {
      this.loading = true
      this.loadingMessage = '双方正在吸收反馈修补漏洞，裁判正在撰写最终报告...'
      this.error = null
      try {
        const { data } = await api.submitFeedback(this.threadId, feedback)
        this.phase = data.phase
        this.state = data.state
        this._addPhase(data.phase)
      } catch (err) {
        this.error = err.response?.data?.detail || err.message
      } finally {
        this.loading = false
      }
    },

    async fetchState() {
      if (!this.threadId) return
      try {
        const { data } = await api.getState(this.threadId)
        this.phase = data.phase
        this.state = data.state
      } catch (err) {
        this.error = err.response?.data?.detail || err.message
      }
    },

    reset() {
      this._stopPolling()
      this.threadId = null
      this.phase = 'input'
      this.activePhase = 'input'
      this.availablePhases = ['input']
      this.state = {}
      this.loading = false
      this.error = null
    },
  },
})
