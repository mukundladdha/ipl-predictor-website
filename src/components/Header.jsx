import { useState } from 'react'
import { useModel } from '../context/ModelContext'

export default function Header({ lastUpdated, seasonStart, defendingChampion }) {
  const { model, setModel } = useModel()
  const [showTooltip, setShowTooltip] = useState(false)

  const daysUntilStart = seasonStart
    ? Math.ceil((new Date(seasonStart) - new Date()) / (1000 * 60 * 60 * 24))
    : null

  return (
    <header className="border-b border-[#2a2d3a] bg-[#0f1117]">
      {daysUntilStart !== null && daysUntilStart > 0 && (
        <div className="w-full py-2 text-center text-xs font-semibold text-black bg-[#FFD700] tracking-wide">
          🏏 Season starts in {daysUntilStart} day{daysUntilStart !== 1 ? 's' : ''} — Mar 28, 2026 · Defending Champions: {defendingChampion}
        </div>
      )}

      <div className="max-w-7xl mx-auto px-4 py-5">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">

          {/* Title */}
          <div>
            <div className="flex items-center gap-3 mb-1">
              <span className="text-2xl">🏏</span>
              <h1 className="text-2xl md:text-3xl font-bold text-white tracking-tight">
                IPL 2026 Forecast
              </h1>
              <span className="px-2 py-0.5 text-xs font-bold bg-[#FFD700]/20 text-[#FFD700] rounded border border-[#FFD700]/30">
                PRE-SEASON
              </span>
            </div>
            <p className="text-sm text-gray-400 ml-11">
              Pre-season playoff probabilities · 100k Monte Carlo simulations · Cricsheet data
            </p>
          </div>

          {/* Controls row */}
          <div className="flex items-center gap-3 ml-11 md:ml-0 flex-wrap">

            {/* Model toggle */}
            <div className="flex items-center bg-[#1a1d27] border border-[#2a2d3a] rounded-full p-1 gap-1">
              <button
                onClick={() => setModel('elo')}
                className={`px-3 py-1 text-xs font-semibold rounded-full transition-all ${
                  model === 'elo'
                    ? 'bg-[#FFD700] text-black shadow'
                    : 'text-gray-400 hover:text-white'
                }`}
              >
                Elo
              </button>
              <button
                onClick={() => setModel('form')}
                className={`px-3 py-1 text-xs font-semibold rounded-full transition-all ${
                  model === 'form'
                    ? 'bg-[#FFD700] text-black shadow'
                    : 'text-gray-400 hover:text-white'
                }`}
              >
                Form
              </button>
            </div>

            {/* Last updated */}
            <div className="text-right">
              <div className="text-xs text-gray-500 uppercase tracking-wider">Updated</div>
              <div className="text-xs font-medium text-[#FFD700]">{lastUpdated}</div>
            </div>

            {/* Methodology tooltip */}
            <div className="relative">
              <button
                onMouseEnter={() => setShowTooltip(true)}
                onMouseLeave={() => setShowTooltip(false)}
                onClick={() => setShowTooltip(v => !v)}
                className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-gray-400 border border-[#2a2d3a] rounded-full hover:border-[#FFD700] hover:text-[#FFD700] transition-colors"
              >
                <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                    d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                How it works
              </button>

              {showTooltip && (
                <div className="absolute right-0 top-9 z-50 w-80 bg-[#1a1d27] border border-[#2a2d3a] rounded-xl p-4 shadow-2xl text-left">
                  <h3 className="text-sm font-semibold text-white mb-3">Two forecast models</h3>

                  <div className="space-y-3">
                    <div className="flex gap-2">
                      <span className={`mt-0.5 px-2 py-0.5 text-xs font-bold rounded-full flex-shrink-0 ${
                        model === 'elo' ? 'bg-[#FFD700] text-black' : 'bg-[#2a2d3a] text-gray-400'
                      }`}>Elo</span>
                      <p className="text-xs text-gray-400">
                        Long-run strength rating from all 1,100+ historical IPL matches (K=32).
                        Tracks franchise quality over years — stable, history-weighted.
                      </p>
                    </div>
                    <div className="flex gap-2">
                      <span className={`mt-0.5 px-2 py-0.5 text-xs font-bold rounded-full flex-shrink-0 ${
                        model === 'form' ? 'bg-[#FFD700] text-black' : 'bg-[#2a2d3a] text-gray-400'
                      }`}>Form</span>
                      <p className="text-xs text-gray-400">
                        Last 8 matches with exponential decay (0.5ⁱ weights). Captures
                        hot/cold streaks — volatile, short-memory.
                      </p>
                    </div>
                  </div>

                  <div className="mt-3 pt-3 border-t border-[#2a2d3a] text-xs text-gray-500">
                    Both models run 100,000 Monte Carlo simulations of the remaining
                    74-game season. Home advantage +30 Elo pts / +4% form.
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </header>
  )
}
