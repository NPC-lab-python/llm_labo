import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts'
import type { MetadataQualityStats } from '../../api/types'
import Card, { CardHeader, CardTitle, CardContent } from '../ui/Card'

interface QualityChartProps {
  stats: MetadataQualityStats
}

const COLORS: Record<string, string> = {
  excellent: '#22c55e',
  Excellent: '#22c55e',
  good: '#3b82f6',
  Good: '#3b82f6',
  fair: '#f59e0b',
  Fair: '#f59e0b',
  poor: '#ef4444',
  Poor: '#ef4444',
}

const LABELS: Record<string, string> = {
  excellent: 'Excellent',
  Excellent: 'Excellent',
  good: 'Bon',
  Good: 'Bon',
  fair: 'Moyen',
  Fair: 'Moyen',
  poor: 'Faible',
  Poor: 'Faible',
}

export default function QualityChart({ stats }: QualityChartProps) {
  const data = Object.entries(stats.score_distribution)
    .filter(([_, value]) => value > 0)
    .map(([name, value]) => ({
      name: LABELS[name] || name,
      value,
      color: COLORS[name] || '#9ca3af',
    }))

  if (data.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Distribution de la Qualité</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-64 flex items-center justify-center text-gray-400">
            Aucune donnée disponible
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Distribution de la Qualité</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={data}
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={80}
                paddingAngle={5}
                dataKey="value"
              >
                {data.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{
                  backgroundColor: 'var(--tw-bg-opacity, 1)',
                  borderColor: 'var(--tw-border-opacity, 1)',
                  borderRadius: '8px',
                }}
                formatter={(value: number) => [`${value} documents`, '']}
              />
              <Legend
                verticalAlign="bottom"
                height={36}
                formatter={(value) => (
                  <span className="text-sm text-gray-600 dark:text-gray-400">{value}</span>
                )}
              />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  )
}
