import { useState } from 'react'
import { useModel } from '../context/ModelContext'

const BASE_COLS = [
  { key: 'name',   label: 'Team',     sortable: true  },
  { key: 'played', label: 'P',        sortable: true  },
  { key: 'won',    label: 'W',        sortable: true  },
  { key: 'lost',   label: 'L',        sortable: true  },
  { key: 'points', label: 'Pts',      sortable: true  },
  { key: 'nrr',    label: 'NRR',      sortable: true  },
  { key: 'elo',    label: 'Elo Rtg',  sortable: true  },
  { key: 'form',   label: 'Form',     sortable: true  },
  { key: 'pct',    label: 'Playoff %',sortable: true  },
]

function PlayoffBar({ pct }) {
  const color = pct >= 60 ? '#22c55e' : pct >= 30 ? '#eab308' : '#ef4444'
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-2 rounded-full bg-[#2a2d3a] overflow-hidden min-w-[80px]">
        <div
          className="h-full rounded-full transition-all duration-500"
          style={{ width: `${Math.min(pct, 100)}%`, backgroundColor: color }}
        />
      </div>
      <span className="text-xs font-bold w-9 text-right tabular-nums" style={{ color }}>
        {pct}%
      </span>
    </div>
  )
}

export default function PlayoffOddsTable({ teams }) {
  const { model } = useModel()
  const [sortKey, setSortKey] = useState('pct')
  const [sortDir, setSortDir] = useState('desc')
  const [expanded, setExpanded] = useState(null)

  // Flatten model-specific fields for sorting/display
  const enriched = teams.map(t => ({
    ...t,
    pct:  t.models[model]?.playoff_pct ?? 0,
    elo:  t.factors?.elo_score   ?? 1000,
    form: t.factors?.form_score  ?? 0.5,
  }))

  const sorted = [...enriched].sort((a, b) => {
    const av = a[sortKey] ?? 0
    const bv = b[sortKey] ?? 0
    const cmp = typeof av === 'string' ? av.localeCompare(bv) : av - bv
    return sortDir === 'asc' ? cmp : -cmp
  })

  function handleSort(key) {
    if (sortKey === key) setSortDir(d => d === 'asc' ? 'desc' : 'asc')
    else { setSortKey(key); setSortDir('desc') }
  }

  return (
    <section className="max-w-7xl mx-auto px-4 py-8">
      <div className="flex items-center gap-3 mb-1">
        <h2 className="text-lg font-bold text-white">Pre-Season Playoff Odds</h2>
        <span className={`px-2 py-0.5 text-xs font-bold rounded-full ${
          model === 'elo'
            ? 'bg-[#FFD700]/20 text-[#FFD700] border border-[#FFD700]/30'
            : 'bg-blue-500/20 text-blue-300 border border-blue-500/30'
        }`}>
          {model === 'elo' ? 'Elo Model' : 'Form Model'}
        </span>
      </div>
      <p className="text-sm text-gray-400 mb-4">
        Projected top-4 finish probability from 100k simulations · Click row for key players
      </p>

      <div className="overflow-x-auto rounded-xl border border-[#2a2d3a]">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-[#2a2d3a]">
              {BASE_COLS.map(col => (
                <th
                  key={col.key}
                  onClick={() => col.sortable && handleSort(col.key)}
                  className={`px-3 py-3 text-left text-xs font-semibold uppercase tracking-wider
                    text-gray-500 bg-[#1a1d27] select-none whitespace-nowrap
                    ${col.sortable ? 'cursor-pointer hover:text-[#FFD700] transition-colors' : ''}
                    ${col.key === 'pct' ? 'min-w-[170px]' : ''}
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
                  onClick={() => setExpanded(expanded === team.short ? null : team.short)}
                  className={`border-b border-[#2a2d3a] cursor-pointer hover:bg-[#1e2130] transition-colors
                    ${i % 2 === 0 ? 'bg-[#0f1117]' : 'bg-[#13161f]'}`}
                >
                  {/* Team */}
                  <td className="px-3 py-3">
                    <div className="flex items-center gap-2.5">
                      <div
                        className="w-3.5 h-3.5 rounded-sm flex-shrink-0 ring-1 ring-white/10"
                        style={{ backgroundColor: team.color }}
                      />
                      <span className="font-medium text-white whitespace-nowrap">{team.name}</span>
                      <span className="text-xs text-gray-500 font-mono">{team.short}</span>
                      {team.pct < 2 && (
                        <span className="px-1.5 py-0.5 text-xs font-bold bg-red-500/20 text-red-400 rounded">ELIM</span>
                      )}
                    </div>
                  </td>
                  <td className="px-3 py-3 text-gray-500 text-center font-mono text-xs">—</td>
                  <td className="px-3 py-3 text-gray-500 text-center font-mono text-xs">—</td>
                  <td className="px-3 py-3 text-gray-500 text-center font-mono text-xs">—</td>
                  <td className="px-3 py-3 text-gray-500 text-center font-mono text-xs">—</td>
                  <td className="px-3 py-3 text-gray-500 text-center font-mono text-xs">—</td>
                  {/* Elo rating */}
                  <td className="px-3 py-3 text-center">
                    <span className="text-xs font-mono text-blue-300 tabular-nums">{team.elo}</span>
                  </td>
                  {/* Form score */}
                  <td className="px-3 py-3 text-center">
                    <span className={`text-xs font-mono tabular-nums ${
                      team.form >= 0.6 ? 'text-green-400' : team.form >= 0.4 ? 'text-yellow-400' : 'text-red-400'
                    }`}>
                      {(team.form * 100).toFixed(0)}%
                    </span>
                  </td>
                  {/* Playoff % bar */}
                  <td className="px-3 py-3 min-w-[170px]">
                    <PlayoffBar pct={team.pct} />
                  </td>
                </tr>
                {expanded === team.short && (
                  <tr
                    key={`${team.short}-exp`}
                    className={`border-b border-[#2a2d3a] ${i % 2 === 0 ? 'bg-[#0f1117]' : 'bg-[#13161f]'}`}
                  >
                    <td colSpan={9} className="px-5 py-2.5 pb-3">
                      <div className="flex flex-wrap gap-4 text-xs">
                        <div>
                          <span className="text-gray-500">Key players: </span>
                          <span className="text-gray-300">{team.key_players}</span>
                        </div>
                        <div>
                          <span className="text-gray-500">Home games: </span>
                          <span className="text-gray-300">{team.factors?.home_games_remaining ?? '—'}</span>
                        </div>
                        <div>
                          <span className="text-gray-500">Elo: </span>
                          <span className="text-blue-300 font-mono">{team.elo}</span>
                          <span className="text-gray-500 mx-2">·</span>
                          <span className="text-gray-500">Form: </span>
                          <span className={`font-mono ${
                            team.form >= 0.6 ? 'text-green-400' : team.form >= 0.4 ? 'text-yellow-400' : 'text-red-400'
                          }`}>{(team.form * 100).toFixed(0)}%</span>
                        </div>
                        <div>
                          <span className="text-gray-500">Elo playoff: </span>
                          <span className="text-white font-mono">{team.models?.elo?.playoff_pct}%</span>
                          <span className="text-gray-500 mx-2">·</span>
                          <span className="text-gray-500">Form playoff: </span>
                          <span className="text-white font-mono">{team.models?.form?.playoff_pct}%</span>
                        </div>
                      </div>
                    </td>
                  </tr>
                )}
              </>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  )
}
