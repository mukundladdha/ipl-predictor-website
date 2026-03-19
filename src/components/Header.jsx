import { useState } from 'react'

export default function Header({ lastUpdated, seasonStart, defendingChampion }) {
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

      <div className="max-w-7xl mx-auto px-4 py-6 md:py-8">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3">
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
              Pre-season playoff probability estimates based on squad strength, auction analysis & historical ELO ratings
            </p>
          </div>

          <div className="flex items-center gap-4 ml-11 md:ml-0">
            <div className="text-right">
              <div className="text-xs text-gray-500 uppercase tracking-wider">Projections As Of</div>
              <div className="text-sm font-medium text-[#FFD700]">{lastUpdated}</div>
            </div>

            <div className="relative">
              <button
                onMouseEnter={() => setShowTooltip(true)}
                onMouseLeave={() => setShowTooltip(false)}
                onClick={() => setShowTooltip(!showTooltip)}
                className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-gray-400 border border-[#2a2d3a] rounded-full hover:border-[#FFD700] hover:text-[#FFD700] transition-colors"
              >
                <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                Methodology
              </button>

              {showTooltip && (
                <div className="absolute right-0 top-9 z-50 w-80 bg-[#1a1d27] border border-[#2a2d3a] rounded-lg p-4 shadow-2xl text-left">
                  <h3 className="text-sm font-semibold text-white mb-2">How We Forecast</h3>
                  <ul className="text-xs text-gray-400 space-y-1.5 list-disc list-inside">
                    <li>10,000 Monte Carlo simulations of the full 74-game league stage</li>
                    <li>Win probabilities from team ELO ratings seeded with auction & squad analysis</li>
                    <li>Home advantage factored at +4% per match</li>
                    <li>NRR modeled as stochastic variable for tiebreaker resolution</li>
                    <li>Updated after every match day once season begins</li>
                  </ul>
                  <div className="mt-3 pt-3 border-t border-[#2a2d3a] text-xs text-gray-500">
                    Inspired by FiveThirtyEight's sports forecasting methodology
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
