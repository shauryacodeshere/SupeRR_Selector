import React, { useState, useMemo } from 'react';
import analyticsData from './data/pressure_analytics.json';
import { 
  Trophy, Flame, ShieldAlert, Award, TrendingUp, Users, DollarSign, 
  CheckCircle, AlertTriangle, ArrowUpDown, Search, Filter, RefreshCw,
  Zap, Crosshair, BarChart2, BookOpen, ExternalLink, HelpCircle
} from 'lucide-react';

export default function App() {
  const [activeTab, setActiveTab] = useState('auction'); // 'auction', 'batters', 'bowlers', 'compare', 'methodology'
  
  // Auction Simulator State
  const INITIAL_PURSE = 27.05;
  const INITIAL_SLOTS = 6;
  const INITIAL_OVERSEAS = 3;
  const [shortlist, setShortlist] = useState([]);
  const [auctionFilter, setAuctionFilter] = useState('all'); // 'all', 'overseas', 'indian', 'pacer', 'finisher'
  const [auctionSearch, setAuctionSearch] = useState('');
  
  // Head to Head State
  const [comparePlayer1, setComparePlayer1] = useState(analyticsData.rr_auction_targets[0]?.player_name || '');
  const [comparePlayer2, setComparePlayer2] = useState(analyticsData.rr_auction_targets[1]?.player_name || '');

  // Purse calculations
  const spentPurse = shortlist.reduce((sum, p) => sum + p.estimated_price_cr, 0);
  const remainingPurse = Math.max(0, INITIAL_PURSE - spentPurse);
  const remainingSlots = Math.max(0, INITIAL_SLOTS - shortlist.length);
  const overseasPicked = shortlist.filter(p => p.is_overseas).length;
  const remainingOverseas = Math.max(0, INITIAL_OVERSEAS - overseasPicked);

  const toggleShortlist = (player) => {
    const exists = shortlist.find(p => p.player_name === player.player_name);
    if (exists) {
      setShortlist(shortlist.filter(p => p.player_name !== player.player_name));
    } else {
      if (shortlist.length >= INITIAL_SLOTS) {
        alert("Maximum squad slots (6) reached!");
        return;
      }
      if (player.is_overseas && remainingOverseas <= 0) {
        alert("Maximum overseas slots (3) reached!");
        return;
      }
      if (player.estimated_price_cr > remainingPurse) {
        alert("Insufficient remaining purse for this target!");
        return;
      }
      setShortlist([...shortlist, player]);
    }
  };

  // Filtered Auction Targets
  const filteredAuctionTargets = useMemo(() => {
    return analyticsData.rr_auction_targets.filter(p => {
      const matchSearch = p.player_name.toLowerCase().includes(auctionSearch.toLowerCase()) ||
                          p.released_by.toLowerCase().includes(auctionSearch.toLowerCase()) ||
                          p.tactical_category.toLowerCase().includes(auctionSearch.toLowerCase());
      if (!matchSearch) return false;
      if (auctionFilter === 'overseas') return p.is_overseas;
      if (auctionFilter === 'indian') return !p.is_overseas;
      if (auctionFilter === 'pacer') return p.primary_role === 'Bowler' && p.tactical_category.includes('Pacer');
      if (auctionFilter === 'finisher') return p.tactical_category.includes('Finisher') || p.tactical_category.includes('Hetmyer');
      return true;
    });
  }, [auctionFilter, auctionSearch]);

  // Selected compare players
  const p1Data = analyticsData.rr_auction_targets.find(p => p.player_name === comparePlayer1) || 
                 analyticsData.top10_batters.find(p => p.striker_name === comparePlayer1) ||
                 analyticsData.top10_bowlers.find(p => p.bowler_name === comparePlayer1);
                 
  const p2Data = analyticsData.rr_auction_targets.find(p => p.player_name === comparePlayer2) || 
                 analyticsData.top10_batters.find(p => p.striker_name === comparePlayer2) ||
                 analyticsData.top10_bowlers.find(p => p.bowler_name === comparePlayer2);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      
      {/* Top Rajasthan Royals Brand Banner */}
      <header className="border-b border-slate-800 bg-slate-900/90 backdrop-blur sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-20">
            
            {/* Logo & Project Title */}
            <div className="flex items-center space-x-4">
              <div className="w-12 h-12 rounded-xl bg-gradient-to-tr from-rr-blue to-rr-pink flex items-center justify-center p-0.5 shadow-lg shadow-pink-500/20">
                <div className="w-full h-full bg-slate-950 rounded-[10px] flex items-center justify-center">
                  <span className="font-teko text-2xl font-bold tracking-wider text-rr-pink">RR</span>
                </div>
              </div>
              <div>
                <div className="flex items-center space-x-2">
                  <span className="font-teko text-2xl tracking-wide uppercase font-bold text-white">SupeRR Selector</span>
                  <span className="bg-rr-pink/20 text-rr-pink text-[11px] font-bold px-2 py-0.5 rounded-full border border-rr-pink/30">
                    SEASON 2
                  </span>
                </div>
                <p className="text-xs text-slate-400 font-medium">Rajasthan Royals • Pressure Intelligence & Auction War Room</p>
              </div>
            </div>

            {/* Quick Context Chips */}
            <div className="hidden lg:flex items-center space-x-3 text-xs">
              <div className="bg-slate-800/80 px-3 py-1.5 rounded-lg border border-slate-700/60 flex items-center space-x-1.5">
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
                <span className="text-slate-300">200,999 Deliveries</span>
              </div>
              <div className="bg-slate-800/80 px-3 py-1.5 rounded-lg border border-slate-700/60 text-slate-300">
                867 Matches (2022–2026)
              </div>
              <div className="bg-pink-950/40 px-3 py-1.5 rounded-lg border border-rr-pink/30 text-rr-pink font-semibold">
                Purse: ₹27.05 Cr (6 Slots)
              </div>
            </div>

          </div>

          {/* Navigation Tabs */}
          <div className="flex space-x-1 overflow-x-auto pb-2 scrollbar-none border-t border-slate-800/60 pt-2">
            {[
              { id: 'auction', label: '🎯 RR Auction War Room', highlight: true },
              { id: 'batters', label: '🏏 Top 10 Batters (Global)', count: '10' },
              { id: 'bowlers', label: '⚡ Top 10 Bowlers (Global)', count: '10' },
              { id: 'compare', label: '⚔️ Head-to-Head Compare' },
              { id: 'methodology', label: '📊 5-Dimension Framework' }
            ].map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`px-4 py-2 text-xs md:text-sm font-semibold rounded-lg transition-all duration-150 flex items-center space-x-2 whitespace-nowrap ${
                  activeTab === tab.id
                    ? tab.highlight 
                      ? 'bg-rr-pink text-white shadow-lg shadow-pink-500/25'
                      : 'bg-slate-800 text-white border border-slate-700'
                    : 'text-slate-400 hover:text-white hover:bg-slate-800/50'
                }`}
              >
                <span>{tab.label}</span>
                {tab.count && (
                  <span className={`text-[10px] px-1.5 py-0.2 rounded-full ${
                    activeTab === tab.id ? 'bg-black/30 text-white' : 'bg-slate-800 text-slate-400'
                  }`}>
                    {tab.count}
                  </span>
                )}
              </button>
            ))}
          </div>

        </div>
      </header>

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">

        {/* ========================================================= */}
        {/* TAB 1: RAJASTHAN ROYALS AUCTION WAR ROOM                  */}
        {/* ========================================================= */}
        {activeTab === 'auction' && (
          <div className="space-y-6">
            
            {/* War Room Alert & Constraints Banner */}
            <div className="bg-gradient-to-r from-rr-blue via-slate-900 to-rr-blue p-5 rounded-2xl border border-rr-pink/30 shadow-xl relative overflow-hidden">
              <div className="absolute right-0 top-0 bottom-0 w-96 bg-radial from-pink-500/10 to-transparent pointer-events-none"></div>
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 relative z-10">
                <div>
                  <div className="flex items-center space-x-2">
                    <span className="px-2.5 py-0.5 bg-rr-pink text-white text-[11px] font-bold rounded-full uppercase tracking-wider">
                      Target Intelligence
                    </span>
                    <span className="text-xs text-slate-300">IPL 2026/27 Mega Auction State</span>
                  </div>
                  <h2 className="text-xl sm:text-2xl font-bold mt-1 text-white">
                    Rajasthan Royals Squad Rebuild & Target Strategy
                  </h2>
                  <p className="text-xs sm:text-sm text-slate-300 max-w-3xl mt-1">
                    RR retained 19 players (Jaiswal, Parag, Jurel, Sandeep, Shami, Archer) and released 9 players including 
                    <strong className="text-rr-pink font-semibold"> Shimron Hetmyer </strong> 
                    and the fast bowling reserves (Deshpande, Sen, Maphaka, Milne).
                  </p>
                </div>

                {/* Exclusions Notice */}
                <div className="bg-amber-500/10 border border-amber-500/30 px-3.5 py-2.5 rounded-xl flex items-center space-x-3 text-amber-300 text-xs shrink-0">
                  <AlertTriangle className="w-5 h-5 text-amber-400 shrink-0" />
                  <div>
                    <span className="font-semibold block">Auction Constraints Active:</span>
                    <span>Excluded: Travis Head (Unavailable) • Ajinkya Rahane & MS Dhoni (Retired)</span>
                  </div>
                </div>
              </div>

              {/* Tactical Void Cards */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mt-4 pt-4 border-t border-slate-800">
                <div className="bg-slate-950/60 p-3 rounded-xl border border-slate-800">
                  <div className="text-[11px] font-semibold text-rr-pink flex items-center space-x-1">
                    <Flame className="w-3.5 h-3.5" />
                    <span>PRIORITY 1: THE HETMYER REPLACEMENT</span>
                  </div>
                  <p className="text-xs text-slate-300 mt-1">
                    Need a death-over finisher (Overs 17–20, high RRR chases). Top targets: <strong className="text-white">Nehal Wadhera, Shahrukh Khan</strong>.
                  </p>
                </div>
                <div className="bg-slate-950/60 p-3 rounded-xl border border-slate-800">
                  <div className="text-[11px] font-semibold text-emerald-400 flex items-center space-x-1">
                    <ShieldAlert className="w-3.5 h-3.5" />
                    <span>PRIORITY 2: ELITE DEATH PACER</span>
                  </div>
                  <p className="text-xs text-slate-300 mt-1">
                    Partner for Sandeep Sharma. Target: <strong className="text-white">Matheesha Pathirana (#2 Global Pressure Bowler)</strong> or Mitchell Starc.
                  </p>
                </div>
                <div className="bg-slate-950/60 p-3 rounded-xl border border-slate-800">
                  <div className="text-[11px] font-semibold text-blue-400 flex items-center space-x-1">
                    <Users className="w-3.5 h-3.5" />
                    <span>PRIORITY 3: DOMESTIC PACE / SPIN DEPTH</span>
                  </div>
                  <p className="text-xs text-slate-300 mt-1">
                    Budget-friendly Indian options with clutch wickets: <strong className="text-white">Akash Madhwal, Deepak Chahar, Mahipal Lomror</strong>.
                  </p>
                </div>
              </div>
            </div>

            {/* Live Interactive Auction Purse & Shortlist Tracker */}
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4 sm:p-5">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-4">
                <div>
                  <h3 className="text-base font-bold text-white flex items-center space-x-2">
                    <DollarSign className="w-4 h-4 text-emerald-400" />
                    <span>RR Auction Budget & Slot Simulator</span>
                  </h3>
                  <p className="text-xs text-slate-400">Click any target to shortlist and simulate purse consumption in real time.</p>
                </div>
                
                {shortlist.length > 0 && (
                  <button 
                    onClick={() => setShortlist([])}
                    className="text-xs text-slate-400 hover:text-white flex items-center space-x-1 self-start sm:self-auto bg-slate-800 px-2.5 py-1 rounded-lg border border-slate-700"
                  >
                    <RefreshCw className="w-3 h-3" />
                    <span>Reset Shortlist</span>
                  </button>
                )}
              </div>

              {/* Progress Gauges */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <div className="bg-slate-950 p-3.5 rounded-xl border border-slate-800">
                  <span className="text-[11px] text-slate-400 block">Remaining Purse</span>
                  <div className="text-xl font-bold text-emerald-400 mt-0.5">
                    ₹{remainingPurse.toFixed(2)} Cr
                  </div>
                  <span className="text-[10px] text-slate-500">Initial: ₹27.05 Cr</span>
                </div>

                <div className="bg-slate-950 p-3.5 rounded-xl border border-slate-800">
                  <span className="text-[11px] text-slate-400 block">Slots Remaining</span>
                  <div className="text-xl font-bold text-white mt-0.5">
                    {remainingSlots} <span className="text-xs font-normal text-slate-500">/ 6 max</span>
                  </div>
                  <span className="text-[10px] text-slate-500">{shortlist.length} selected</span>
                </div>

                <div className="bg-slate-950 p-3.5 rounded-xl border border-slate-800">
                  <span className="text-[11px] text-slate-400 block">Overseas Slots</span>
                  <div className={`text-xl font-bold mt-0.5 ${remainingOverseas > 0 ? 'text-blue-400' : 'text-amber-400'}`}>
                    {remainingOverseas} <span className="text-xs font-normal text-slate-500">/ 3 max</span>
                  </div>
                  <span className="text-[10px] text-slate-500">{overseasPicked} overseas picked</span>
                </div>

                <div className="bg-slate-950 p-3.5 rounded-xl border border-slate-800">
                  <span className="text-[11px] text-slate-400 block">Avg. Price Per Slot</span>
                  <div className="text-xl font-bold text-rr-pink mt-0.5">
                    ₹{remainingSlots > 0 ? (remainingPurse / remainingSlots).toFixed(2) : '0.00'} Cr
                  </div>
                  <span className="text-[10px] text-slate-500">Target safe limit</span>
                </div>
              </div>

              {/* Shortlist Pills */}
              {shortlist.length > 0 && (
                <div className="mt-4 pt-3 border-t border-slate-800/80 flex flex-wrap items-center gap-2">
                  <span className="text-xs font-semibold text-slate-400">Shortlisted:</span>
                  {shortlist.map(p => (
                    <div 
                      key={p.player_name}
                      className="bg-slate-800 border border-slate-700 text-white text-xs pl-2.5 pr-1.5 py-1 rounded-lg flex items-center space-x-2"
                    >
                      <span>{p.player_name} (₹{p.estimated_price_cr} Cr)</span>
                      <button 
                        onClick={() => toggleShortlist(p)}
                        className="w-4 h-4 rounded-full bg-slate-700 hover:bg-rose-500 text-slate-300 hover:text-white flex items-center justify-center text-[10px]"
                      >
                        ×
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Filter & Search Bar */}
            <div className="flex flex-col md:flex-row items-stretch md:items-center justify-between gap-3">
              <div className="flex flex-wrap items-center gap-1.5">
                {[
                  { id: 'all', label: 'All Released' },
                  { id: 'overseas', label: '✈️ Overseas (3 Max)' },
                  { id: 'indian', label: '🇮🇳 Indian Core' },
                  { id: 'pacer', label: '⚡ Death Pacers' },
                  { id: 'finisher', label: '💥 Finishers (Hetmyer Void)' }
                ].map(f => (
                  <button
                    key={f.id}
                    onClick={() => setAuctionFilter(f.id)}
                    className={`px-3 py-1.5 rounded-lg text-xs font-medium transition ${
                      auctionFilter === f.id
                        ? 'bg-rr-pink text-white font-semibold'
                        : 'bg-slate-900 text-slate-400 hover:text-white border border-slate-800'
                    }`}
                  >
                    {f.label}
                  </button>
                ))}
              </div>

              <div className="relative min-w-[260px]">
                <Search className="w-4 h-4 absolute left-3 top-2.5 text-slate-400" />
                <input
                  type="text"
                  placeholder="Search player, team, category..."
                  value={auctionSearch}
                  onChange={(e) => setAuctionSearch(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-800 rounded-lg pl-9 pr-3 py-1.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-rr-pink"
                />
              </div>
            </div>

            {/* Target Recommendation Cards Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {filteredAuctionTargets.map((target, idx) => {
                const isSelected = shortlist.some(p => p.player_name === target.player_name);
                return (
                  <div 
                    key={target.player_name}
                    className={`rounded-2xl p-4 transition-all duration-200 border flex flex-col justify-between ${
                      isSelected 
                        ? 'bg-gradient-to-b from-pink-950/40 to-slate-900 border-rr-pink shadow-lg shadow-pink-500/15' 
                        : 'bg-slate-900/90 border-slate-800 hover:border-slate-700'
                    }`}
                  >
                    <div>
                      {/* Top Badges */}
                      <div className="flex items-start justify-between gap-2">
                        <div>
                          <span className="text-[10px] font-semibold text-slate-400 block">
                            Released by {target.released_by}
                          </span>
                          <h4 className="text-base font-bold text-white flex items-center space-x-1.5 mt-0.5">
                            <span>{target.player_name}</span>
                            <span className="text-xs font-normal">
                              {target.is_overseas ? '✈️' : '🇮🇳'}
                            </span>
                          </h4>
                        </div>
                        <div className="text-right">
                          <span className="text-[10px] text-slate-400 block">RR Fit Score</span>
                          <span className="text-base font-extrabold text-rr-pink">
                            {target.rr_fit_score}
                          </span>
                        </div>
                      </div>

                      {/* Tactical Role Tag */}
                      <div className="mt-2.5">
                        <span className="inline-block text-[11px] font-semibold bg-slate-800 text-pink-300 border border-pink-500/20 px-2.5 py-0.5 rounded-full">
                          {target.tactical_category}
                        </span>
                      </div>

                      {/* Key Pressure Metrics Box */}
                      <div className="grid grid-cols-3 gap-2 mt-3 pt-3 border-t border-slate-800/80 text-center">
                        <div className="bg-slate-950/70 p-2 rounded-lg">
                          <span className="text-[10px] text-slate-400 block">HP Sample</span>
                          <span className="text-xs font-bold text-slate-200">
                            {target.primary_role === 'Bowler' ? target.bowl_hp_balls : target.bat_hp_balls} balls
                          </span>
                        </div>

                        <div className="bg-slate-950/70 p-2 rounded-lg">
                          <span className="text-[10px] text-slate-400 block">
                            {target.primary_role === 'Bowler' ? 'HP Economy' : 'HP Strike Rate'}
                          </span>
                          <span className="text-xs font-bold text-emerald-400">
                            {target.primary_role === 'Bowler' ? `${target.bowl_hp_econ}` : `${target.bat_hp_sr}`}
                          </span>
                        </div>

                        <div className="bg-slate-950/70 p-2 rounded-lg">
                          <span className="text-[10px] text-slate-400 block">Pressure PAE</span>
                          <span className={`text-xs font-bold ${
                            (target.primary_role === 'Bowler' ? target.bowl_hp_pae : target.bat_hp_pae) >= 0 
                              ? 'text-rr-pink' 
                              : 'text-rose-400'
                          }`}>
                            {target.primary_role === 'Bowler' ? `+${target.bowl_hp_pae}` : `+${target.bat_hp_pae}`}
                          </span>
                        </div>
                      </div>
                    </div>

                    {/* Bottom Action & Price Bar */}
                    <div className="mt-4 pt-3 border-t border-slate-800 flex items-center justify-between">
                      <div>
                        <span className="text-[10px] text-slate-400 block">Est. Auction Price</span>
                        <span className="text-sm font-bold text-white">₹{target.estimated_price_cr} Cr</span>
                      </div>

                      <button
                        onClick={() => toggleShortlist(target)}
                        className={`text-xs font-semibold px-3 py-1.5 rounded-lg transition flex items-center space-x-1.5 ${
                          isSelected
                            ? 'bg-rose-500 hover:bg-rose-600 text-white'
                            : 'bg-rr-pink hover:bg-pink-600 text-white'
                        }`}
                      >
                        {isSelected ? (
                          <><span>Remove</span></>
                        ) : (
                          <><span>+ Shortlist Target</span></>
                        )}
                      </button>
                    </div>

                  </div>
                );
              })}
            </div>

          </div>
        )}

        {/* ========================================================= */}
        {/* TAB 2: GLOBAL TOP 10 BATTERS UNDER PRESSURE               */}
        {/* ========================================================= */}
        {activeTab === 'batters' && (
          <div className="space-y-6">
            
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5">
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
                <div>
                  <div className="flex items-center space-x-2">
                    <Trophy className="w-5 h-5 text-rr-gold" />
                    <h2 className="text-xl font-bold text-white">Ranked Top 10 Batters Under Pressure (2022–2026)</h2>
                  </div>
                  <p className="text-xs text-slate-400 mt-1 max-w-2xl">
                    Ranked via <strong>Performance Above Expectation (PAE)</strong> under high pressure ($P \ge 0.60$), 
                    calibrated with Empirical Bayesian shrinkage ($K=75$) to reward sustained clutch performance over small-sample flukes.
                  </p>
                </div>
                <div className="bg-slate-950 px-3.5 py-2 rounded-xl border border-slate-800 text-xs text-slate-300">
                  <span className="text-slate-500 block text-[10px]">Qualifying Baseline</span>
                  <span className="font-semibold">Minimum 150 High-Pressure Balls</span>
                </div>
              </div>
            </div>

            {/* Leaderboard Cards */}
            <div className="space-y-3">
              {analyticsData.top10_batters.map((batter, idx) => {
                const isTop3 = idx < 3;
                return (
                  <div 
                    key={batter.striker_id}
                    className={`bg-slate-900/90 border rounded-2xl p-4 sm:p-5 transition hover:border-slate-700 ${
                      idx === 0 ? 'border-amber-500/40 bg-gradient-to-r from-amber-950/20 via-slate-900 to-slate-900' :
                      idx === 1 ? 'border-slate-400/40' :
                      idx === 2 ? 'border-amber-700/40' :
                      'border-slate-800'
                    }`}
                  >
                    <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
                      
                      {/* Left: Rank & Player Identity */}
                      <div className="flex items-center space-x-4">
                        <div className={`w-10 h-10 rounded-xl flex items-center justify-center font-bold text-sm shrink-0 ${
                          idx === 0 ? 'bg-gradient-to-br from-amber-400 to-amber-600 text-slate-950 font-extrabold shadow-lg shadow-amber-500/20' :
                          idx === 1 ? 'bg-gradient-to-br from-slate-200 to-slate-400 text-slate-950 font-bold' :
                          idx === 2 ? 'bg-gradient-to-br from-amber-700 to-amber-900 text-white font-bold' :
                          'bg-slate-800 text-slate-300'
                        }`}>
                          #{idx + 1}
                        </div>

                        <div>
                          <div className="flex items-center space-x-2">
                            <h3 className="text-lg font-bold text-white">{batter.striker_name}</h3>
                            {idx === 0 && (
                              <span className="bg-amber-400/20 text-amber-300 border border-amber-400/30 text-[10px] font-bold px-2 py-0.5 rounded-full">
                                World #1 Clutch Batter
                              </span>
                            )}
                            {batter.striker_name === 'Rinku Singh' && (
                              <span className="bg-pink-500/20 text-pink-300 border border-pink-500/30 text-[10px] font-bold px-2 py-0.5 rounded-full">
                                Premier Chase Finisher
                              </span>
                            )}
                          </div>
                          <span className="text-xs text-slate-400">
                            {batter.matches_played} Matches • {batter.hp_balls} High Pressure Balls Faced
                          </span>
                        </div>
                      </div>

                      {/* Right: Key Performance Stats */}
                      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-center sm:text-right">
                        <div className="bg-slate-950/60 p-2.5 rounded-xl border border-slate-800">
                          <span className="text-[10px] text-slate-400 block">Clutch Rating</span>
                          <span className="text-base font-extrabold text-rr-pink">
                            {batter.bat_clutch_rating.toFixed(1)} <span className="text-xs text-slate-500">/ 100</span>
                          </span>
                        </div>

                        <div className="bg-slate-950/60 p-2.5 rounded-xl border border-slate-800">
                          <span className="text-[10px] text-slate-400 block">HP Strike Rate</span>
                          <span className="text-base font-bold text-emerald-400">
                            {batter.hp_strike_rate.toFixed(1)}
                          </span>
                        </div>

                        <div className="bg-slate-950/60 p-2.5 rounded-xl border border-slate-800">
                          <span className="text-[10px] text-slate-400 block">Total Pressure PAE</span>
                          <span className="text-base font-bold text-white">
                            +{batter.hp_pae_total.toFixed(1)}
                          </span>
                        </div>

                        <div className="bg-slate-950/60 p-2.5 rounded-xl border border-slate-800">
                          <span className="text-[10px] text-slate-400 block">Boundary %</span>
                          <span className="text-base font-bold text-blue-400">
                            {batter.hp_boundary_pct.toFixed(1)}%
                          </span>
                        </div>
                      </div>

                    </div>

                    {/* Specialization Breakdown Bar */}
                    <div className="mt-3 pt-3 border-t border-slate-800/80 flex flex-wrap items-center gap-4 text-xs text-slate-400">
                      <span><strong>Chase PAE:</strong> <span className="text-slate-200">+{batter.chase_pae}</span></span>
                      <span><strong>Death Overs PAE:</strong> <span className="text-slate-200">+{batter.death_bat_pae}</span></span>
                      <span><strong>Collapse Rescue PAE:</strong> <span className="text-slate-200">+{batter.collapse_bat_pae}</span></span>
                    </div>

                  </div>
                );
              })}
            </div>

          </div>
        )}

        {/* ========================================================= */}
        {/* TAB 3: GLOBAL TOP 10 BOWLERS UNDER PRESSURE               */}
        {/* ========================================================= */}
        {activeTab === 'bowlers' && (
          <div className="space-y-6">
            
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5">
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
                <div>
                  <div className="flex items-center space-x-2">
                    <Zap className="w-5 h-5 text-emerald-400" />
                    <h2 className="text-xl font-bold text-white">Ranked Top 10 Bowlers Under Pressure (2022–2026)</h2>
                  </div>
                  <p className="text-xs text-slate-400 mt-1 max-w-2xl">
                    Evaluated by runs saved below contextual expected baselines and clutch wickets taken in tight finishes. 
                    Run-outs are strictly excluded from bowler attribution for statistical fairness.
                  </p>
                </div>
                <div className="bg-slate-950 px-3.5 py-2 rounded-xl border border-slate-800 text-xs text-slate-300">
                  <span className="text-slate-500 block text-[10px]">Qualifying Baseline</span>
                  <span className="font-semibold">Minimum 150 High-Pressure Balls</span>
                </div>
              </div>
            </div>

            {/* Leaderboard Cards */}
            <div className="space-y-3">
              {analyticsData.top10_bowlers.map((bowler, idx) => {
                return (
                  <div 
                    key={bowler.bowler_id}
                    className={`bg-slate-900/90 border rounded-2xl p-4 sm:p-5 transition hover:border-slate-700 ${
                      idx === 0 ? 'border-amber-500/40 bg-gradient-to-r from-amber-950/20 via-slate-900 to-slate-900' :
                      idx === 1 ? 'border-slate-400/40' :
                      idx === 2 ? 'border-amber-700/40' :
                      'border-slate-800'
                    }`}
                  >
                    <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
                      
                      {/* Left: Rank & Bowler Identity */}
                      <div className="flex items-center space-x-4">
                        <div className={`w-10 h-10 rounded-xl flex items-center justify-center font-bold text-sm shrink-0 ${
                          idx === 0 ? 'bg-gradient-to-br from-amber-400 to-amber-600 text-slate-950 font-extrabold shadow-lg shadow-amber-500/20' :
                          idx === 1 ? 'bg-gradient-to-br from-slate-200 to-slate-400 text-slate-950 font-bold' :
                          idx === 2 ? 'bg-gradient-to-br from-amber-700 to-amber-900 text-white font-bold' :
                          'bg-slate-800 text-slate-300'
                        }`}>
                          #{idx + 1}
                        </div>

                        <div>
                          <div className="flex items-center space-x-2">
                            <h3 className="text-lg font-bold text-white">{bowler.bowler_name}</h3>
                            {idx === 0 && (
                              <span className="bg-amber-400/20 text-amber-300 border border-amber-400/30 text-[10px] font-bold px-2 py-0.5 rounded-full">
                                Undisputed #1 Pressure Bowler
                              </span>
                            )}
                            {bowler.bowler_name === 'Matheesha Pathirana' && (
                              <span className="bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 text-[10px] font-bold px-2 py-0.5 rounded-full">
                                World #1 Death Yorker Weapon (Auction Target!)
                              </span>
                            )}
                          </div>
                          <span className="text-xs text-slate-400">
                            {bowler.matches_played} Matches • {bowler.hp_balls} High Pressure Balls Bowled
                          </span>
                        </div>
                      </div>

                      {/* Right: Key Performance Stats */}
                      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-center sm:text-right">
                        <div className="bg-slate-950/60 p-2.5 rounded-xl border border-slate-800">
                          <span className="text-[10px] text-slate-400 block">Clutch Rating</span>
                          <span className="text-base font-extrabold text-rr-pink">
                            {bowler.bowl_clutch_rating.toFixed(1)} <span className="text-xs text-slate-500">/ 100</span>
                          </span>
                        </div>

                        <div className="bg-slate-950/60 p-2.5 rounded-xl border border-slate-800">
                          <span className="text-[10px] text-slate-400 block">HP Economy</span>
                          <span className="text-base font-bold text-emerald-400">
                            {bowler.hp_economy.toFixed(2)}
                          </span>
                        </div>

                        <div className="bg-slate-950/60 p-2.5 rounded-xl border border-slate-800">
                          <span className="text-[10px] text-slate-400 block">Clutch Wickets</span>
                          <span className="text-base font-bold text-white">
                            {bowler.hp_wickets}
                          </span>
                        </div>

                        <div className="bg-slate-950/60 p-2.5 rounded-xl border border-slate-800">
                          <span className="text-[10px] text-slate-400 block">Dot Ball %</span>
                          <span className="text-base font-bold text-blue-400">
                            {bowler.hp_dot_pct.toFixed(1)}%
                          </span>
                        </div>
                      </div>

                    </div>

                    {/* Specialization Breakdown Bar */}
                    <div className="mt-3 pt-3 border-t border-slate-800/80 flex flex-wrap items-center gap-4 text-xs text-slate-400">
                      <span><strong>Total Pressure PAE:</strong> <span className="text-emerald-300 font-semibold">+{bowler.hp_pae_total}</span></span>
                      <span><strong>Death Overs PAE:</strong> <span className="text-slate-200">+{bowler.death_bowl_pae}</span></span>
                    </div>

                  </div>
                );
              })}
            </div>

          </div>
        )}

        {/* ========================================================= */}
        {/* TAB 4: HEAD-TO-HEAD PRESSURE SIMULATOR                    */}
        {/* ========================================================= */}
        {activeTab === 'compare' && (
          <div className="space-y-6">
            
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5">
              <h2 className="text-xl font-bold text-white flex items-center space-x-2">
                <Crosshair className="w-5 h-5 text-rr-pink" />
                <span>Head-to-Head Pressure & Auction Matchup</span>
              </h2>
              <p className="text-xs text-slate-400 mt-1">
                Directly compare any two players under pressure to resolve auction decisions (e.g. Matheesha Pathirana vs Mitchell Starc at the death).
              </p>

              {/* Selector Dropdowns */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
                <div>
                  <label className="text-xs text-slate-400 font-semibold block mb-1">Select Player 1</label>
                  <select 
                    value={comparePlayer1}
                    onChange={(e) => setComparePlayer1(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-sm text-white focus:outline-none focus:border-rr-pink"
                  >
                    {analyticsData.rr_auction_targets.map(p => (
                      <option key={p.player_name} value={p.player_name}>
                        {p.player_name} ({p.tactical_category})
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="text-xs text-slate-400 font-semibold block mb-1">Select Player 2</label>
                  <select 
                    value={comparePlayer2}
                    onChange={(e) => setComparePlayer2(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-sm text-white focus:outline-none focus:border-rr-pink"
                  >
                    {analyticsData.rr_auction_targets.map(p => (
                      <option key={p.player_name} value={p.player_name}>
                        {p.player_name} ({p.tactical_category})
                      </option>
                    ))}
                  </select>
                </div>
              </div>
            </div>

            {/* Comparison Cards */}
            {p1Data && p2Data && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {[
                  { data: p1Data, label: 'Candidate A' },
                  { data: p2Data, label: 'Candidate B' }
                ].map((item, i) => (
                  <div key={i} className="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-4">
                    <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                      <div>
                        <span className="text-[10px] text-rr-pink font-bold uppercase">{item.label}</span>
                        <h3 className="text-xl font-bold text-white">{item.data.player_name || item.data.striker_name || item.data.bowler_name}</h3>
                        <span className="text-xs text-slate-400">{item.data.tactical_category || 'Global Top 10 Performer'}</span>
                      </div>
                      <div className="text-right">
                        <span className="text-[10px] text-slate-400 block">Fit / Clutch Score</span>
                        <span className="text-2xl font-black text-rr-pink">
                          {item.data.rr_fit_score || item.data.bat_clutch_rating || item.data.bowl_clutch_rating}
                        </span>
                      </div>
                    </div>

                    <div className="space-y-2 text-xs">
                      <div className="flex justify-between py-1.5 border-b border-slate-800/60">
                        <span className="text-slate-400">Primary Role</span>
                        <span className="text-white font-semibold">{item.data.primary_role || 'Specialist'}</span>
                      </div>
                      <div className="flex justify-between py-1.5 border-b border-slate-800/60">
                        <span className="text-slate-400">Estimated Auction Cost</span>
                        <span className="text-emerald-400 font-bold">₹{item.data.estimated_price_cr || 'N/A'} Cr</span>
                      </div>
                      <div className="flex justify-between py-1.5 border-b border-slate-800/60">
                        <span className="text-slate-400">High-Pressure Balls</span>
                        <span className="text-white">{item.data.bowl_hp_balls || item.data.bat_hp_balls || item.data.hp_balls} balls</span>
                      </div>
                      <div className="flex justify-between py-1.5 border-b border-slate-800/60">
                        <span className="text-slate-400">Total Pressure PAE</span>
                        <span className="text-white font-semibold">+{item.data.bowl_hp_pae || item.data.bat_hp_pae || item.data.hp_pae_total}</span>
                      </div>
                      <div className="flex justify-between py-1.5">
                        <span className="text-slate-400">Death Overs Impact PAE</span>
                        <span className="text-rr-pink font-semibold">+{item.data.death_bowl_pae || item.data.death_bat_pae || 0}</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}

          </div>
        )}

        {/* ========================================================= */}
        {/* TAB 5: 5-DIMENSIONS METHODOLOGY                           */}
        {/* ========================================================= */}
        {activeTab === 'methodology' && (
          <div className="space-y-6">
            
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5">
              <h2 className="text-xl font-bold text-white flex items-center space-x-2">
                <BookOpen className="w-5 h-5 text-rr-pink" />
                <span>The Five Dimensions of Pressure Intelligence</span>
              </h2>
              <p className="text-xs text-slate-400 mt-1 max-w-3xl">
                A reproducible, statistically defensible framework created for Rajasthan Royals SupeRR Selector Season 2.
                Replaces simplistic strike rates and arbitrary weighted sums with situational expected baselines.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              
              {/* Dimension A */}
              <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-2">
                <div className="flex items-center space-x-2 text-rr-pink">
                  <Flame className="w-4 h-4" />
                  <h3 className="font-bold text-white text-sm">Dimension A: Continuous Pressure Intensity (P)</h3>
                </div>
                <p className="text-xs text-slate-300 leading-relaxed">
                  Pressure is continuous, bounded in $[0.05, 1.0]$. In chases, it is dynamically derived from Required Run Rate (RRR), 
                  balls remaining, and wickets in hand. In 1st innings, it measures collapse resource deficit and death acceleration.
                </p>
                <div className="bg-slate-950 p-2.5 rounded-lg border border-slate-800 font-mono text-[11px] text-pink-300">
                  P = σ( 0.55 · (RRR / 8.5) + 0.45 · ((10 - W) / 9) ) · PhaseFactor
                </div>
              </div>

              {/* Dimension B */}
              <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-2">
                <div className="flex items-center space-x-2 text-emerald-400">
                  <TrendingUp className="w-4 h-4" />
                  <h3 className="font-bold text-white text-sm">Dimension B: Performance Above Expectation (PAE)</h3>
                </div>
                <p className="text-xs text-slate-300 leading-relaxed">
                  Compares actual runs and dismissals to contextual expected baselines calibrated across 200,999 deliveries. 
                  A wicket carries an empirical run value penalty of 4.5 runs.
                </p>
                <div className="bg-slate-950 p-2.5 rounded-lg border border-slate-800 font-mono text-[11px] text-emerald-300">
                  PAE = (Actual - E[Runs|State]) ± 4.5 · (Dismissal - E[Wkt|State])
                </div>
              </div>

              {/* Dimension C */}
              <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-2">
                <div className="flex items-center space-x-2 text-blue-400">
                  <ShieldAlert className="w-4 h-4" />
                  <h3 className="font-bold text-white text-sm">Dimension C: Bayesian Shrinkage & Reliability</h3>
                </div>
                <p className="text-xs text-slate-300 leading-relaxed">
                  Protects against small-sample variance. Players with heroic 3-match samples are shrunk towards population averages ($K=75$ balls), 
                  ensuring only reliable, sustained pressure performers top the leaderboard.
                </p>
                <div className="bg-slate-950 p-2.5 rounded-lg border border-slate-800 font-mono text-[11px] text-blue-300">
                  PAE_shrunk = (N / (N + K)) · PAE_player + (K / (N + K)) · μ_pop
                </div>
              </div>

              {/* Dimension D & E */}
              <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-2">
                <div className="flex items-center space-x-2 text-rr-gold">
                  <Award className="w-4 h-4" />
                  <h3 className="font-bold text-white text-sm">Dimensions D & E: Specialization & Match Stakes</h3>
                </div>
                <p className="text-xs text-slate-300 leading-relaxed">
                  Deconstructs players into 4 distinct archetypes: Chase Finishers, Death Over Specialists, Collapse Rescuers, and Powerplay Enforcers. 
                  Playoff knockout matches receive a 1.15x existential pressure multiplier.
                </p>
                <div className="bg-slate-950 p-2.5 rounded-lg border border-slate-800 font-mono text-[11px] text-amber-300">
                  Final Clutch Rating = PAE_shrunk · √N (Scaled 0 to 100)
                </div>
              </div>

            </div>

            {/* Critical Data Discovery Box */}
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5">
              <h3 className="text-sm font-bold text-white flex items-center space-x-2">
                <CheckCircle className="w-4 h-4 text-emerald-400" />
                <span>Critical Forensic Audit Discoveries Handled</span>
              </h3>
              <ul className="mt-2 space-y-1.5 text-xs text-slate-300 list-disc list-inside">
                <li><strong className="text-white">The extras1_runs Enum Trap:</strong> Discovered that `extras1_runs` is a coded ID (1=Overstep, 2=wide, 6=normal ball), preventing severe data corruption.</li>
                <li><strong className="text-white">Strict Legal Ball Accounting:</strong> Overs 1 to 20 precisely track legal deliveries, excluding wides/no-balls to compute true balls remaining.</li>
                <li><strong className="text-white">Accurate Bowler Credit:</strong> Run-outs, retired hurt, and obstructing field are excluded from bowler wickets, but correctly counted towards team pressure state.</li>
              </ul>
            </div>

          </div>
        )}

      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800/80 bg-slate-950 py-6 text-center text-xs text-slate-500">
        <p>SupeRR Selector Season 2 — Rajasthan Royals Analytics Hackathon • Built with React, Tailwind & Python Engine</p>
      </footer>

    </div>
  );
}
