import { useState } from 'react'

const columns = [
  { key: 'name', label: 'Team', sortable: true },
  { key: 'played', label: 'P', sortable: true },
  { key: 'won', label: 'W', sortable: true },
  { key: 'lost', label: 'L', sortable: true },
  { key: 'points', label: 'Pts', sortable: true },
  { key: 'nrr', label: 'NRR', sortable: true },
  { key: 'playoff_pct', label: 'Playoff %', sortable: true },
]

function PlayoffBar({ pct }) {
  const color = pct >= 60 ? '#22c55e' : pct >= 30 ? '#eab308' : '#ef4444'
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-2 rounded-full bg-[#2a2d3a] overflow-hidden min-w-[80px]">
        <div
          className="h-full rounded-full transition-all duration-500"
          style={{ width: `${pct}%`, backgroundColor: color }}
        />
      </div>
      <span className="text-xs font-bold w-8 text-right" style={{ color }}>{pct}%</span>
    </div>
  )
}

export default function PlayoffOddsTable({ teams }) {
  const [sortKey, setSortKey] = useState('playoff_pct')
  const [sortDir, setSortDir] = useState('desc')
  const [expandedTeam, setExpandedTeam] = useState(null)

  function handleSort(key) {
    if (sortKey === key) {
      setSortDir(d => d === 'asc' ? 'desc' : 'asc')
    } else {
      setSortKey(key)
      setSortDir('desc')
    }
  }

  const sorted = [...teams].sort((a, b) => {
    const av = a[sortKey] ?? 0
    const bv = b[sortKey] ?? 0
    const cmp = typeof av === 'string' ? av.localeCompare(bv) : av - bv
    return sortDir === 'asc' ? cmp : -cmp
  })

  return (
    <section className="max-w-7xl mx-auto px-4 py-8">
      <h2 className="text-lg font-bold text-white mb-1">Pre-Season Playoff Probabilities</h2>
      <p className="text-sm text-gray-400 mb-4">
        Projected chances of finishing top 4 — based on squad strength & ELO ratings before a ball is bowled
      </p>

      <div className="overflow-x-auto rounded-xl border border-[#2a2d3a]">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-[#2a2d3a]">
              {columns.map(col => (
                <th
                  key={col.key}
                  onClick={() => col.sortable && handleSort(col.key)}
                  className={`px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-500 bg-[#1a1d27] select-none
                    ${col.sortable ? 'cursor-pointer hover:text-[#FFD700] transition-colors' : ''}
                    ${col.key === 'playoff_pct' ? 'min-w-[180px]' : ''}
                  `}
                >
                  <span className="flex items-center gap-1">
                    {col.label}
                    {col.sortable && sortKey === col.key && (
                      <span className="text-[#FFD700]">{sortDir === 'asc' ? '↑' : '↓'}</span>
                    )}
                  </span>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {sorted.map((team, i) => (
              <>
                <tr
                  key={team.short}
                  onClick={() => setExpandedTeam(expandedTeam === team.short ? null : team.short)}
                  className={`border-b border-[#2a2d3a] transition-colors cursor-pointer hover:bg-[#1e2130]
                    ${i % 2 === 0 ? 'bg-[#0f1117]' : 'bg-[#13161f]'}`}
                >
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2.5">
                      <div
                        className="w-4 h-4 rounded-sm flex-shrink-0 ring-1 ring-white/10"
                        style={{ backgroundColor: team.color }}
                      />
                      <span className="font-medium text-white">{team.name}</span>
                      <span className="text-xs text-gray-500 font-mono">{team.short}</span>
                      {team.defending_champion && (
                        <span className="px-1.5 py-0.5 text-xs font-bold bg-yellow-500/20 text-yellow-400 rounded border border-yellow-500/30">
                          DEF
                        </span>
                      )}
                    </div>
                  </td>
                  <td className="px-4 py-3 text-gray-500 text-center font-mono">—</td>
                  <td className="px-4 py-3 text-gray-500 text-center font-mono">—</td>
                  <td className="px-4 py-3 text-gray-500 text-center font-mono">—</td>
                  <td className="px-4 py-3 text-gray-500 text-center font-mono">—</td>
                  <td className="px-4 py-3 text-gray-500 text-center font-mono text-xs">—</td>
                  <td className="px-4 py-3 min-w-[180px]">
                    <PlayoffBar pct={team.playoff_pct} />
                  </td>
                </tr>
                {expandedTeam === team.short && team.key_players && (
                  <tr
                    key={`${team.short}-detail`}
                    className={`border-b border-[#2a2d3a] ${i % 2 === 0 ? 'bg-[#0f1117]' : 'bg-[#13161f]'}`}
                  >
                    <td colSpan={7} className="px-6 py-2 pb-3">
                      <div className="flex items-start gap-2 text-xs">
                        <span className="text-gray-500 flex-shrink-0 pt-0.5">Key players:</span>
                        <span className="text-gray-300">{team.key_players}</span>
                      </div>
                    </td>
                  </tr>
                )}
              </>
            ))}
          </tbody>
        </table>
      </div>
      <p className="text-xs text-gray-600 mt-2 text-right">Click a row to see key players</p>
    </section>
  )
}
