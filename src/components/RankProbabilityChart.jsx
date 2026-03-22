import { useState } from 'react'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  Cell, ResponsiveContainer, LabelList
} from 'recharts'
import { useModel } from '../context/ModelContext'

const ORDINALS = ['1st','2nd','3rd','4th','5th','6th','7th','8th','9th','10th']

function hexToRgb(hex) {
  const r = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex)
  return r ? { r: parseInt(r[1],16), g: parseInt(r[2],16), b: parseInt(r[3],16) } : {r:100,g:100,b:255}
}

function shadeColor(hex, factor) {
  const { r, g, b } = hexToRgb(hex)
  return `rgba(${Math.round(r*factor)},${Math.round(g*factor)},${Math.round(b*factor)},${0.35 + factor*0.65})`
}

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null
  return (
    <div className="bg-[#1a1d27] border border-[#2a2d3a] rounded-lg p-3 shadow-2xl text-xs">
      <div className="text-gray-400 mb-1">Finish {label}</div>
      <div className="font-bold text-white text-base tabular-nums">{payload[0].value}%</div>
    </div>
  )
}

export default function RankProbabilityChart({ teams }) {
  const { model } = useModel()
  const [selectedShort, setSelectedShort] = useState(teams[0].short)

  const team = teams.find(t => t.short === selectedShort) ?? teams[0]
  const rankProbs = team.models?.[model]?.rank_probs ?? []
  const data = rankProbs.map((pct, i) => ({ rank: ORDINALS[i], pct }))
  const factors = [1.0, 0.88, 0.76, 0.64, 0.52, 0.42, 0.34, 0.28, 0.22, 0.18]

  return (
    <section className="max-w-7xl mx-auto px-4 py-8">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
        <div>
          <div className="flex items-center gap-3 mb-1">
            <h2 className="text-lg font-bold text-white">Final Rank Probabilities</h2>
            <span className={`px-2 py-0.5 text-xs font-bold rounded-full ${
              model === 'elo'
                ? 'bg-[#FFD700]/20 text-[#FFD700] border border-[#FFD700]/30'
                : 'bg-blue-500/20 text-blue-300 border border-blue-500/30'
            }`}>
              {model === 'elo' ? 'Elo' : 'Form'}
            </span>
          </div>
          <p className="text-sm text-gray-400">Probability of finishing each league position at season end</p>
        </div>

        <select
          value={selectedShort}
          onChange={e => setSelectedShort(e.target.value)}
          className="bg-[#1a1d27] border border-[#2a2d3a] text-white text-sm rounded-lg px-3 py-2
                     focus:outline-none focus:border-[#FFD700] cursor-pointer"
        >
          {teams.map(t => (
            <option key={t.short} value={t.short}>{t.name}</option>
          ))}
        </select>
      </div>

      <div className="bg-[#1a1d27] rounded-xl border border-[#2a2d3a] p-4 md:p-6">
        <div className="flex items-center justify-between mb-5">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-sm" style={{ backgroundColor: team.color }} />
            <span className="text-sm font-semibold text-white">{team.name}</span>
            <span className="text-xs text-gray-500">({team.short})</span>
          </div>
          <span className="text-xs text-[#FFD700] font-medium">
            {team.models?.[model]?.playoff_pct ?? 0}% playoff chance
          </span>
        </div>

        <ResponsiveContainer width="100%" height={320}>
          <BarChart
            data={data}
            layout="vertical"
            margin={{ top: 0, right: 60, left: 10, bottom: 0 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#2a2d3a" horizontal={false} />
            <XAxis
              type="number"
              domain={[0, Math.max(...data.map(d => d.pct)) + 5]}
              tick={{ fill: '#6b7280', fontSize: 11 }}
              axisLine={{ stroke: '#2a2d3a' }}
              tickLine={false}
              tickFormatter={v => `${v}%`}
            />
            <YAxis
              type="category"
              dataKey="rank"
              tick={{ fill: '#9ca3af', fontSize: 11 }}
              axisLine={false}
              tickLine={false}
              width={36}
            />
            <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(255,255,255,0.04)' }} />
            <Bar dataKey="pct" radius={[0, 4, 4, 0]}>
              {data.map((_, i) => (
                <Cell key={i} fill={shadeColor(team.color, factors[i] ?? 0.18)} />
              ))}
              <LabelList
                dataKey="pct"
                position="right"
                formatter={v => `${v}%`}
                style={{ fill: '#9ca3af', fontSize: '11px' }}
              />
            </Bar>
          </BarChart>
        </ResponsiveContainer>

        <div className="mt-4 pt-4 border-t border-[#2a2d3a] grid grid-cols-5 sm:grid-cols-10 gap-2">
          {data.map((d, i) => (
            <div key={i} className="text-center">
              <div className="text-xs text-gray-500">{d.rank}</div>
              <div className="text-xs font-bold tabular-nums" style={{ color: shadeColor(team.color, factors[i] ?? 0.18) }}>
                {d.pct}%
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
