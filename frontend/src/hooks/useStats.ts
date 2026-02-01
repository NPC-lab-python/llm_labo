import { useQuery } from '@tanstack/react-query'
import { getStats } from '../api/endpoints'

export function useStats() {
  return useQuery({
    queryKey: ['stats'],
    queryFn: getStats,
    staleTime: 1000 * 60 * 5, // 5 minutes
  })
}
