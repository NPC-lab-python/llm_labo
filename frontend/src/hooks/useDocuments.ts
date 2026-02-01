import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getDocuments, deleteDocument, uploadPdf } from '../api/endpoints'

interface UseDocumentsParams {
  page?: number
  limit?: number
  search?: string
  status?: string
}

export function useDocuments(params: UseDocumentsParams = {}) {
  return useQuery({
    queryKey: ['documents', params],
    queryFn: () => getDocuments(params),
  })
}

export function useDeleteDocument() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: deleteDocument,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] })
      queryClient.invalidateQueries({ queryKey: ['health'] })
      queryClient.invalidateQueries({ queryKey: ['stats'] })
    },
  })
}

export function useUploadDocument() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: uploadPdf,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] })
      queryClient.invalidateQueries({ queryKey: ['health'] })
      queryClient.invalidateQueries({ queryKey: ['stats'] })
    },
  })
}
