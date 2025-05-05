import { createStore } from 'vuex'
import { Host } from '@/types'

interface PaginatedHosts {
  results: Host[]
  count: number
  page: number
  page_size: number
  next: string | null
  previous: string | null
}

interface RootState {
  hosts: PaginatedHosts
}

export default createStore<RootState>({
  state: {
    hosts: {
      results: [],
      count: 0,
      page: 1,
      page_size: 10,
      next: null,
      previous: null
    }
  },

  getters: {
    getHosts: (state: RootState): Host[] => state.hosts.results,
    getTotalCount: (state: RootState): number => state.hosts.count,
    getCurrentPage: (state: RootState): number => state.hosts.page,
    getPageSize: (state: RootState): number => state.hosts.page_size,
    getNextPage: (state: RootState): string | null => state.hosts.next,
    getPreviousPage: (state: RootState): string | null => state.hosts.previous
  },

  mutations: {
    setHosts(state: RootState, payload: PaginatedHosts) {
      state.hosts = payload
    }
  },

  actions: {
    async fetchHosts({ commit }, { page = 1 } = {}) {
      try {
        const response = await fetch(`/api/hosts/?page=${page}`)
        if (!response.ok) {
          throw new Error('Network response was not ok')
        }
        const data: PaginatedHosts = await response.json()
        commit('setHosts', data)
      } catch (error) {
        console.error('Error fetching hosts:', error)
        throw error
      }
    },
    async searchHosts({ commit }, { query, page = 1 }: { query: string, page: number }) {
      try {
        const response = await fetch(`/api/search/?q=${encodeURIComponent(query)}&page=${page}&size=${100}`)
        if (!response.ok) {
          throw new Error('Network response was not ok')
        }
        const data: PaginatedHosts = await response.json()
        commit('setHosts', data)
      } catch (error) {
        console.error('Error searching hosts:', error)
        throw error
      }
    }
  },

  modules: {
  }
})
