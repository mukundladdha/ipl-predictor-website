import { useState } from 'react'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  Cell, ResponsiveContainer, LabelList
} from 'recharts'

function hexToRgb(hex) {
  const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex)
  return result
    ? { r: parseInt(result[1], 16), g: parseInt(result[2], 16), b: parseInt(result[3], 16) }
    : { r: 100, g: 100, b: 255 }
}

function shadeColor(hex, factor) {
  const { r, g, b } = hexToRgb(hex)
  return `rgba(${Math.round(r * factor)},${Math.round(g * factor)},${Math.round(b * factor)},${0.4 + factor * 0.6})`
}

const ORDINALS = ['1st', '2nd', '3rd', '4th', '5th', '6th', '7th', '8th']

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null
  return (
    <div className="bg-[#1a1d27] border border-[#2a2d3a] rounded-lg p-3 shadow-2xl text-xs">
      <div className="text-gray-400 mb-1">Finish {label}</div>
      <div className="font-bold text-white text-base">{payload[0].value}%</div>
      <div className="text-gray-500">probability</div>
    </div>
  )
}

export default function RankProbabilityChart({ teams }) {
  const [selectedShort, setSelectedShort] = useState(teams[0].short)
  const team = teams.find(t => t.short === selectedShort) || teams[0]

  const data = team.rank_probs.map((pct, i) => ({
    rank: ORDINALS[i],
    pct,
  }))

  const factors = [1.0, 0.88, 0.76, 0.64, 0.52, 0.42, 0.34, 0.28]

  return (
    <section className="max-w-7xl mx-auto px-4 py-8">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
        <div>
          <h2 className="text-lg font-bold text-white mb-1">Final Rank Probabilities</h2>
          <p className="text-sm text-gray-400">Likelihood of finishing in each position at season end</p>
        </div>

        <select
          value={selectedShort}
          onChange={e => setSelectedShort(e.target.value)}
          className="bg-[#1a1d27] border border-[#2a2d3a] text-white text-sm rounded-lg px-3 py-2 focus:outline-none focus:border-[#FFD700] cursor-pointer"
        >
          {teams.map(t => (
            <option key={t.short} value={t.short}>{t.name}</option>
          ))}
        </select>
      </div>

      <div className="bg-[#1a1d27] rounded-xl border border-[#2a2d3a] p-4 md:p-6">
        <div className="flex items-center gap-2 mb-4">
          <div className="w-3 h-3 rounded-sm" style={{ backgroundColor: team.color }} />
          <span className="text-sm font-semibold text-white">{team.name}</span>
          <span className="text-xs text-gray-500">({team.short})</span>
          <span className="ml-auto text-xs text-[#FFD700] font-medium">{team.playoff_pct}% playoff chance</span>
        </div>

        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={data} margin={{ top: 20, right: 10, left: 0, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#2a2d3a" vertical={false} />
            <XAxis
              dataKey="rank"
              tick={{ fill: '#6b7280', fontSize: 11 }}
              axisLine={{ stroke: '#2a2d3a' }}
              tickLine={false}
            />
            <YAxis
              domain={[0, Math.max(...data.map(d => d.pct)) + 5]}
              tick={{ fill: '#6b7280', fontSize: 11 }}
              axisLine={{ stroke: '#2a2d3a' }}
              tickLine={false}
              tickFormatter={v => `${v}%`}
              width={40}
            />
            <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(255,255,255,0.04)' }} />
            <Bar dataKey="pct" radius={[4, 4, 0, 0]}>
              {data.map((entry, i) => (
                <Cell
                  key={i}
                  fill={shadeColor(team.color, factors[i])}
                />
              ))}
              <LabelList
                dataKey="pct"
                position="top"
                formatter={v => `${v}%`}
                style={{ fill: '#9ca3af', fontSize: '10px' }}
              />
            </Bar>
          </BarChart>
        </ResponsiveContainer>

        <div className="mt-4 grid grid-cols-4 sm:grid-cols-8 gap-2">
          {data.map((d, i) => (
            <div key={i} className="text-center">
              <div className="text-xs text-gray-500">{d.rank}</div>
              <div
                className="text-sm font-bold"
                style={{ color: shadeColor(team.color, factors[i]) }}
              >
                {d.pct}%
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
