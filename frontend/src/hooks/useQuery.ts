import { useMutation } from '@tanstack/react-query'
import { postQuery } from '../api/endpoints'
import type { QueryRequest, QueryResponse } from '../api/types'

export function useRagQuery() {
  return useMutation<QueryResponse, Error, QueryRequest>({
    mutationFn: postQuery,
  })
}
