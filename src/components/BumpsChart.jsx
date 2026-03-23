import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  Legend, ResponsiveContainer,
} from 'recharts'
import { useModel } from '../context/ModelContext'

function buildChartData(teams, model) {
  const maxLen = Math.max(...teams.map(t => (t.history?.[model] ?? []).length))
  if (maxLen === 0) return []
  return Array.from({ length: maxLen }, (_, i) => {
    const point = { md: `MD ${i + 1}` }
    teams.forEach(t => {
      const val = t.history?.[model]?.[i]
      if (val !== undefined) point[t.short] = val
    })
    return point
  })
}

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null
  const sorted = [...payload].sort((a, b) => b.value - a.value)
  return (
    <div style={{
      background: '#1a1d27',
      border: '0.5px solid #2a2d3a',
      borderRadius: 8,
      padding: '10px 14px',
      fontSize: 12,
      minWidth: 140,
    }}>
      <div style={{ color: '#aaa', marginBottom: 8, fontSize: 11 }}>{label}</div>
      {sorted.map(e => (
        <div key={e.dataKey} style={{ display: 'flex', justifyContent: 'space-between', gap: 16, padding: '2px 0' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <div style={{ width: 8, height: 8, borderRadius: '50%', backgroundColor: e.color, flexShrink: 0 }} />
            <span style={{ color: '#888' }}>{e.dataKey}</span>
          </div>
          <span style={{ fontWeight: 500, color: e.color, fontVariantNumeric: 'tabular-nums' }}>
            {e.value}%
          </span>
        </div>
      ))}
    </div>
  )
}

export default function BumpsChart({ teams }) {
  const { activeModel } = useModel()
  const data = buildChartData(teams, activeModel)

  return (
    <div style={{
      background: '#0d0f16',
      borderTop: '0.5px solid #1e2130',
      borderBottom: '0.5px solid #1e2130',
    }}>
      <div className="sec" style={{ paddingTop: 40, paddingBottom: 40 }}>
        <div style={{
          fontSize: 11,
          color: '#FFD700',
          letterSpacing: '2px',
          textTransform: 'uppercase',
          marginBottom: 24,
        }}>
          Playoff odds over the season
        </div>

        <ResponsiveContainer width="100%" height={340}>
          <LineChart data={data} margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e2130" />
            <XAxis
              dataKey="md"
              tick={{ fill: '#888', fontSize: 11 }}
              axisLine={{ stroke: '#2a2d3a' }}
              tickLine={false}
            />
            <YAxis
              domain={[0, 100]}
              tick={{ fill: '#888', fontSize: 11 }}
              axisLine={false}
              tickLine={false}
              tickFormatter={v => `${v}%`}
              width={36}
            />
            <Tooltip content={<CustomTooltip />} />
            <Legend
              wrapperStyle={{ paddingTop: 20 }}
              formatter={v => (
                <span style={{ color: '#aaa', fontSize: 11 }}>{v}</span>
              )}
              iconType="circle"
              iconSize={8}
            />
            {teams.map(t => (
              <Line
                key={t.short}
                type="monotone"
                dataKey={t.short}
                stroke={t.color}
                strokeWidth={2}
                dot={{ r: 3, fill: t.color, strokeWidth: 0 }}
                activeDot={{ r: 5, strokeWidth: 2, stroke: '#fff' }}
                connectNulls={false}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}
