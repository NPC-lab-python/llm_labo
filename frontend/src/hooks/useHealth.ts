import { useQuery } from '@tanstack/react-query'
import { getHealth } from '../api/endpoints'

export function useHealth() {
  return useQuery({
    queryKey: ['health'],
    queryFn: getHealth,
    refetchInterval: 30000, // Refresh toutes les 30 secondes
    retry: 1,
  })
}
