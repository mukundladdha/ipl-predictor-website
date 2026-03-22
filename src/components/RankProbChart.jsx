import { useState } from 'react'
import {
  BarChart, Bar, XAxis, YAxis, ResponsiveContainer, Tooltip, Cell,
} from 'recharts'
import { useModel } from '../context/ModelContext'

const POSITIONS = ['1st', '2nd', '3rd', '4th', '5th', '6th', '7th', '8th', '9th', '10th']

function rankColor(hex, pos, total) {
  // pos 0 = 1st (vivid team color), pos 9 = 10th (near dark)
  const t = pos / (total - 1) // 0 → 1
  const r = parseInt(hex.slice(1, 3), 16)
  const g = parseInt(hex.slice(3, 5), 16)
  const b = parseInt(hex.slice(5, 7), 16)
  const bgR = 26, bgG = 29, bgB = 39  // #1a1d27
  return `rgb(${Math.round(r + (bgR - r) * t * 0.82)},${Math.round(g + (bgG - g) * t * 0.82)},${Math.round(b + (bgB - b) * t * 0.82)})`
}

const CustomTooltip = ({ active, payload }) => {
  if (!active || !payload?.length) return null
  return (
    <div style={{
      background: '#1a1d27',
      border: '0.5px solid #2a2d3a',
      borderRadius: 8,
      padding: '8px 12px',
      fontSize: 12,
    }}>
      {payload.map(p => (
        <div key={p.dataKey} style={{ color: '#888' }}>
          {p.dataKey}: <span style={{ color: '#fff', fontWeight: 600 }}>{p.value}%</span>
        </div>
      ))}
    </div>
  )
}

export default function RankProbChart({ teams }) {
  const { activeModel } = useModel()
  const [selectedShort, setSelectedShort] = useState(teams[0]?.short ?? '')

  const team = teams.find(t => t.short === selectedShort) ?? teams[0]
  const probs = team?.models[activeModel]?.rank_probs ?? []

  // One data row per position for a vertical bar chart
  const chartData = POSITIONS.map((pos, i) => ({
    pos,
    pct: probs[i] ?? 0,
  }))

  return (
    <div style={{ maxWidth: 900, margin: '0 auto', padding: '40px 24px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <div style={{
          fontSize: 11,
          color: '#FFD700',
          letterSpacing: '1.5px',
          textTransform: 'uppercase',
        }}>
          How likely is each finish?
        </div>
        <select
          value={selectedShort}
          onChange={e => setSelectedShort(e.target.value)}
          style={{
            background: '#1a1d27',
            border: '0.5px solid #2a2d3a',
            borderRadius: 8,
            color: '#ccc',
            fontSize: 13,
            padding: '6px 12px',
            cursor: 'pointer',
            outline: 'none',
          }}
        >
          {teams.map(t => (
            <option key={t.short} value={t.short}>{t.name}</option>
          ))}
        </select>
      </div>

      {/* Stacked horizontal bar (one row = the team, segments = each rank) */}
      <ResponsiveContainer width="100%" height={64}>
        <BarChart
          layout="vertical"
          data={[Object.fromEntries([['name', team.short], ...POSITIONS.map((p, i) => [p, probs[i] ?? 0])])]}
          margin={{ top: 0, right: 0, bottom: 0, left: 0 }}
          barSize={40}
        >
          <XAxis type="number" domain={[0, 100]} hide />
          <YAxis type="category" dataKey="name" hide />
          <Tooltip
            content={<CustomTooltip />}
            cursor={false}
          />
          {POSITIONS.map((pos, i) => (
            <Bar key={pos} dataKey={pos} stackId="a" fill={rankColor(team.color, i, POSITIONS.length)} />
          ))}
        </BarChart>
      </ResponsiveContainer>

      {/* Legend */}
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px 16px', marginTop: 16 }}>
        {POSITIONS.map((pos, i) => (
          <div key={pos} style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
            <div style={{
              width: 10,
              height: 10,
              borderRadius: 2,
              backgroundColor: rankColor(team.color, i, POSITIONS.length),
              flexShrink: 0,
            }} />
            <span style={{ fontSize: 11, color: '#444' }}>
              {pos}: {probs[i] ?? 0}%
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}
