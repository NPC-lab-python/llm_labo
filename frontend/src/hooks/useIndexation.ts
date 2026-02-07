import { useMutation, useQueryClient } from '@tanstack/react-query'
import { indexBatch, reindexEmbeddings, resetDatabases } from '../api/endpoints'

export function useIndexBatch() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: indexBatch,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] })
      queryClient.invalidateQueries({ queryKey: ['health'] })
      queryClient.invalidateQueries({ queryKey: ['stats'] })
    },
  })
}

export function useReindexEmbeddings() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: reindexEmbeddings,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] })
      queryClient.invalidateQueries({ queryKey: ['stats'] })
    },
  })
}

export function useResetDatabases() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: resetDatabases,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] })
      queryClient.invalidateQueries({ queryKey: ['health'] })
      queryClient.invalidateQueries({ queryKey: ['stats'] })
    },
  })
}
