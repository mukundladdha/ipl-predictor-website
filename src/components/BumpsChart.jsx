import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  Legend, ResponsiveContainer, ReferenceLine
} from 'recharts'

const PHASE_LABELS = ['Pre-season', 'Early (MD3)', 'MD5', 'MD7', 'Pre-break (MD9)', 'Late (MD12)', 'Final (MD14)']

function buildChartData(teams) {
  const maxLen = Math.max(...teams.map(t => t.history.length))
  return Array.from({ length: maxLen }, (_, i) => {
    const point = { day: PHASE_LABELS[i] || `MD ${i + 1}` }
    teams.forEach(t => {
      if (t.history[i] !== undefined) point[t.short] = t.history[i]
    })
    return point
  })
}

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null
  const sorted = [...payload].sort((a, b) => b.value - a.value)
  return (
    <div className="bg-[#1a1d27] border border-[#2a2d3a] rounded-lg p-3 shadow-2xl text-xs">
      <div className="text-gray-400 mb-2 font-medium">{label}</div>
      {sorted.map(entry => (
        <div key={entry.dataKey} className="flex items-center justify-between gap-4 py-0.5">
          <div className="flex items-center gap-1.5">
            <div className="w-2 h-2 rounded-full" style={{ backgroundColor: entry.color }} />
            <span className="text-gray-300">{entry.dataKey}</span>
          </div>
          <span className="font-bold" style={{ color: entry.color }}>{entry.value}%</span>
        </div>
      ))}
    </div>
  )
}

export default function BumpsChart({ teams, seasonStart }) {
  const data = buildChartData(teams)
  const isPreSeason = data.length <= 1

  return (
    <section className="max-w-7xl mx-auto px-4 py-8">
      <h2 className="text-lg font-bold text-white mb-1">Playoff % Over Time</h2>
      <p className="text-sm text-gray-400 mb-6">
        {isPreSeason
          ? 'Pre-season projections — chart will populate with live data once the season begins on Mar 28'
          : 'How each team\'s playoff chances have evolved across match days'}
      </p>

      <div className="bg-[#1a1d27] rounded-xl border border-[#2a2d3a] p-4 md:p-6">
        {isPreSeason ? (
          <div>
            {/* Pre-season bar chart substitute */}
            <div className="space-y-2.5">
              {[...teams]
                .sort((a, b) => b.playoff_pct - a.playoff_pct)
                .map(team => (
                  <div key={team.short} className="flex items-center gap-3">
                    <div className="w-12 text-xs text-gray-500 text-right font-mono flex-shrink-0">{team.short}</div>
                    <div className="flex-1 h-6 bg-[#2a2d3a] rounded overflow-hidden relative">
                      <div
                        className="h-full rounded transition-all duration-700 flex items-center justify-end pr-2"
                        style={{ width: `${team.playoff_pct}%`, backgroundColor: team.color, opacity: 0.85 }}
                      />
                    </div>
                    <div
                      className="w-10 text-xs font-bold text-right flex-shrink-0"
                      style={{ color: team.playoff_pct >= 60 ? '#22c55e' : team.playoff_pct >= 30 ? '#eab308' : '#ef4444' }}
                    >
                      {team.playoff_pct}%
                    </div>
                  </div>
                ))}
            </div>
            <div className="mt-5 pt-4 border-t border-[#2a2d3a] flex items-center gap-2 text-xs text-gray-500">
              <svg className="w-4 h-4 text-[#FFD700]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              Line chart will show playoff % evolution once matches begin — first update after Mar 28
            </div>
          </div>
        ) : (
          <ResponsiveContainer width="100%" height={380}>
            <LineChart data={data} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#2a2d3a" />
              <XAxis
                dataKey="day"
                tick={{ fill: '#6b7280', fontSize: 11 }}
                axisLine={{ stroke: '#2a2d3a' }}
                tickLine={false}
              />
              <YAxis
                domain={[0, 100]}
                tick={{ fill: '#6b7280', fontSize: 11 }}
                axisLine={{ stroke: '#2a2d3a' }}
                tickLine={false}
                tickFormatter={v => `${v}%`}
                width={40}
              />
              <Tooltip content={<CustomTooltip />} />
              <ReferenceLine y={50} stroke="#2a2d3a" strokeDasharray="4 4" />
              <Legend
                wrapperStyle={{ paddingTop: '16px' }}
                formatter={(value) => (
                  <span style={{ color: '#9ca3af', fontSize: '11px' }}>{value}</span>
                )}
              />
              {teams.map(team => (
                <Line
                  key={team.short}
                  type="monotone"
                  dataKey={team.short}
                  stroke={team.color}
                  strokeWidth={2}
                  dot={{ r: 4, fill: team.color, strokeWidth: 0 }}
                  activeDot={{ r: 6, strokeWidth: 2, stroke: '#fff' }}
                  connectNulls
                />
              ))}
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>
    </section>
  )
}
