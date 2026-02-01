import { BarChart, Bar, XAxis, YAxis, ResponsiveContainer, Tooltip, Cell } from 'recharts'
import type { MetadataQualityStats } from '../../api/types'
import Card, { CardHeader, CardTitle, CardContent } from '../ui/Card'

interface MissingFieldsChartProps {
  stats: MetadataQualityStats
}

const FIELD_LABELS: Record<string, string> = {
  title: 'Titre',
  authors: 'Auteurs',
  year: 'Année',
  abstract: 'Résumé',
  keywords: 'Mots-clés',
  doi: 'DOI',
}

const COLORS = ['#ef4444', '#f97316', '#f59e0b', '#84cc16', '#22c55e', '#06b6d4']

export default function MissingFieldsChart({ stats }: MissingFieldsChartProps) {
  const data = Object.entries(stats.missing_fields)
    .map(([field, count]) => ({
      field: FIELD_LABELS[field] || field,
      count,
    }))
    .sort((a, b) => b.count - a.count)
    .slice(0, 6)

  if (data.length === 0 || data.every((d) => d.count === 0)) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Champs Manquants</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-64 flex items-center justify-center text-gray-400">
            Tous les champs sont renseignés
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Champs Manquants</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={data} layout="vertical" margin={{ left: 20, right: 20 }}>
              <XAxis type="number" />
              <YAxis
                type="category"
                dataKey="field"
                width={80}
                tick={{ fontSize: 12 }}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: 'white',
                  borderRadius: '8px',
                  border: '1px solid #e5e7eb',
                }}
                formatter={(value: number) => [`${value} documents`, 'Manquant']}
              />
              <Bar dataKey="count" radius={[0, 4, 4, 0]}>
                {data.map((_, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  )
}
