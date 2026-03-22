import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  Legend, ResponsiveContainer, ReferenceLine
} from 'recharts'
import { useModel } from '../context/ModelContext'

const PHASE_LABELS = ['Pre-season', 'MD 3', 'MD 6', 'MD 9', 'MD 12', 'MD 14']

function buildChartData(teams, model) {
  const maxLen = Math.max(...teams.map(t => (t.history?.[model] ?? []).length))
  if (maxLen === 0) return []
  return Array.from({ length: maxLen }, (_, i) => {
    const point = { day: PHASE_LABELS[i] ?? `MD ${i}` }
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
    <div className="bg-[#1a1d27] border border-[#2a2d3a] rounded-lg p-3 shadow-2xl text-xs min-w-[140px]">
      <div className="text-gray-400 mb-2 font-medium">{label}</div>
      {sorted.map(e => (
        <div key={e.dataKey} className="flex items-center justify-between gap-3 py-0.5">
          <div className="flex items-center gap-1.5">
            <div className="w-2 h-2 rounded-full" style={{ backgroundColor: e.color }} />
            <span className="text-gray-300">{e.dataKey}</span>
          </div>
          <span className="font-bold tabular-nums" style={{ color: e.color }}>{e.value}%</span>
        </div>
      ))}
    </div>
  )
}

export default function BumpsChart({ teams }) {
  const { model } = useModel()
  const data = buildChartData(teams, model)
  const isPreSeason = data.length <= 1

  return (
    <section className="max-w-7xl mx-auto px-4 py-8">
      <div className="flex items-center gap-3 mb-1">
        <h2 className="text-lg font-bold text-white">Playoff % Over Time</h2>
        <span className={`px-2 py-0.5 text-xs font-bold rounded-full ${
          model === 'elo'
            ? 'bg-[#FFD700]/20 text-[#FFD700] border border-[#FFD700]/30'
            : 'bg-blue-500/20 text-blue-300 border border-blue-500/30'
        }`}>
          {model === 'elo' ? 'Elo' : 'Form'}
        </span>
      </div>
      <p className="text-sm text-gray-400 mb-6">
        {isPreSeason
          ? 'Pre-season snapshot — chart populates with live data once season begins Mar 28'
          : 'Playoff % evolution across match days · toggle Elo / Form above to compare models'}
      </p>

      <div className="bg-[#1a1d27] rounded-xl border border-[#2a2d3a] p-4 md:p-6">
        {isPreSeason ? (
          <div>
            <div className="space-y-2.5">
              {[...teams]
                .sort((a, b) => (b.models?.[model]?.playoff_pct ?? 0) - (a.models?.[model]?.playoff_pct ?? 0))
                .map(team => {
                  const pct = team.models?.[model]?.playoff_pct ?? 0
                  return (
                    <div key={team.short} className="flex items-center gap-3">
                      <div className="w-12 text-xs text-gray-500 text-right font-mono flex-shrink-0">{team.short}</div>
                      <div className="flex-1 h-6 bg-[#2a2d3a] rounded overflow-hidden">
                        <div
                          className="h-full rounded transition-all duration-700"
                          style={{ width: `${pct}%`, backgroundColor: team.color, opacity: 0.85 }}
                        />
                      </div>
                      <div
                        className="w-9 text-xs font-bold text-right flex-shrink-0 tabular-nums"
                        style={{ color: pct >= 60 ? '#22c55e' : pct >= 30 ? '#eab308' : '#ef4444' }}
                      >
                        {pct}%
                      </div>
                    </div>
                  )
                })}
            </div>
            <div className="mt-5 pt-4 border-t border-[#2a2d3a] flex items-center gap-2 text-xs text-gray-500">
              <svg className="w-4 h-4 text-[#FFD700] flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              Line chart activates after first match day · Updated after each game
            </div>
          </div>
        ) : (
          <ResponsiveContainer width="100%" height={380}>
            <LineChart data={data} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#2a2d3a" />
              <XAxis dataKey="day" tick={{ fill: '#6b7280', fontSize: 11 }}
                axisLine={{ stroke: '#2a2d3a' }} tickLine={false} />
              <YAxis domain={[0, 100]}
                tick={{ fill: '#6b7280', fontSize: 11 }}
                axisLine={{ stroke: '#2a2d3a' }} tickLine={false}
                tickFormatter={v => `${v}%`} width={40} />
              <Tooltip content={<CustomTooltip />} />
              <ReferenceLine y={50} stroke="#2a2d3a" strokeDasharray="4 4" />
              <Legend wrapperStyle={{ paddingTop: '16px' }}
                formatter={v => <span style={{ color: '#9ca3af', fontSize: '11px' }}>{v}</span>} />
              {teams.map(t => (
                <Line key={t.short} type="monotone" dataKey={t.short}
                  stroke={t.color} strokeWidth={2}
                  dot={{ r: 4, fill: t.color, strokeWidth: 0 }}
                  activeDot={{ r: 6, strokeWidth: 2, stroke: '#fff' }}
                  connectNulls />
              ))}
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>
    </section>
  )
}
