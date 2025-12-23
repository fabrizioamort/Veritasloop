import React from 'react';
import { Settings, Globe, Type, Search, Database, Shield, Feather, Zap, Flame } from 'lucide-react';

const ConfigPanel = ({
    maxIterations,
    setMaxIterations,
    maxSearches,
    setMaxSearches,
    inputType,
    setInputType,
    language,
    setLanguage,
    proPersonality,
    setProPersonality,
    contraPersonality,
    setContraPersonality,
    isProcessing
}) => {
    return (
        <div
            className="flex flex-wrap items-center justify-center gap-6 p-4 mb-6 bg-black/40 backdrop-blur-xl border border-white/10 rounded-2xl shadow-2xl mx-auto max-w-4xl transition-all hover:border-white/20"
            role="region"
            aria-label="Verification configuration settings"
        >

            {/* Group 1: Numerical Settings */}
            <div
                className="flex items-center gap-4 py-2 px-4 bg-white/5 rounded-xl border border-white/5"
                role="group"
                aria-labelledby="numerical-settings-label"
            >
                <span id="numerical-settings-label" className="sr-only">Numerical settings</span>
                <div className="flex flex-col">
                    <label
                        htmlFor="max-iterations-input"
                        className="flex items-center gap-1.5 text-[10px] uppercase tracking-widest text-gray-400 font-bold mb-1.5"
                    >
                        <Settings size={10} className="text-accent" aria-hidden="true" />
                        <span>Iterations</span>
                    </label>
                    <input
                        id="max-iterations-input"
                        type="number"
                        min="1"
                        max="10"
                        value={maxIterations}
                        onChange={e => setMaxIterations(parseInt(e.target.value) || 1)}
                        className="w-20 bg-black/20 border border-white/10 rounded-lg px-3 py-1.5 text-center text-sm font-mono focus:outline-none focus:border-accent focus:ring-1 focus:ring-accent/50 transition-all hover:bg-white/5"
                        disabled={isProcessing}
                        aria-label="Maximum debate iterations (1-10)"
                        aria-describedby="iterations-description"
                    />
                    <span id="iterations-description" className="sr-only">Number of debate rounds between agents</span>
                </div>

                <div className="w-px h-8 bg-white/10 mx-2"></div>

                <div className="flex flex-col">
                    <label
                        htmlFor="max-searches-input"
                        className="flex items-center gap-1.5 text-[10px] uppercase tracking-widest text-gray-400 font-bold mb-1.5"
                    >
                        <Database size={10} className="text-accent" aria-hidden="true" />
                        <span>Max Search</span>
                    </label>
                    <div className="relative">
                        <input
                            id="max-searches-input"
                            type="number"
                            min="-1"
                            max="20"
                            value={maxSearches}
                            onChange={e => setMaxSearches(parseInt(e.target.value) || -1)}
                            className="w-20 bg-black/20 border border-white/10 rounded-lg px-3 py-1.5 text-center text-sm font-mono focus:outline-none focus:border-accent focus:ring-1 focus:ring-accent/50 transition-all hover:bg-white/5"
                            disabled={isProcessing}
                            aria-label="Maximum search results (-1 for unlimited)"
                            aria-describedby="searches-description"
                        />
                        {maxSearches === -1 && (
                            <span className="absolute right-8 top-1/2 -translate-y-1/2 text-[10px] text-gray-500 pointer-events-none" aria-hidden="true">
                                ∞
                            </span>
                        )}
                    </div>
                    <span id="searches-description" className="sr-only">Maximum number of web searches per agent, -1 for unlimited</span>
                </div>
            </div>

            {/* Group 2: Input Type & Language */}
            <div className="flex items-center gap-4" role="group" aria-labelledby="input-language-label">
                <span id="input-language-label" className="sr-only">Input type and language settings</span>

                <div className="flex flex-col">
                    <label
                        htmlFor="input-type-select"
                        className="flex items-center gap-1.5 text-[10px] uppercase tracking-widest text-gray-400 font-bold mb-1.5 ml-1"
                    >
                        <Type size={10} className="text-accent" aria-hidden="true" />
                        <span>Input Type</span>
                    </label>
                    <div className="relative">
                        <select
                            id="input-type-select"
                            value={inputType}
                            onChange={e => setInputType(e.target.value)}
                            className="appearance-none bg-black/20 border border-white/10 rounded-lg pl-3 pr-8 py-1.5 text-sm focus:outline-none focus:border-accent focus:ring-1 focus:ring-accent/50 transition-all hover:bg-white/5 cursor-pointer min-w-[100px]"
                            disabled={isProcessing}
                            aria-label="Select input type (Text or URL)"
                        >
                            <option value="Text">Text</option>
                            <option value="URL">URL</option>
                        </select>
                        <div className="absolute right-2 top-1/2 -translate-y-1/2 pointer-events-none text-gray-500">
                            <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="m6 9 6 6 6-6" /></svg>
                        </div>
                    </div>
                </div>

                <div className="flex flex-col">
                    <label
                        htmlFor="language-select"
                        className="flex items-center gap-1.5 text-[10px] uppercase tracking-widest text-gray-400 font-bold mb-1.5 ml-1"
                    >
                        <Globe size={10} className="text-accent" aria-hidden="true" />
                        <span>Language</span>
                    </label>
                    <div className="relative">
                        <select
                            id="language-select"
                            value={language}
                            onChange={e => setLanguage(e.target.value)}
                            className="appearance-none bg-black/20 border border-white/10 rounded-lg pl-3 pr-8 py-1.5 text-sm focus:outline-none focus:border-accent focus:ring-1 focus:ring-accent/50 transition-all hover:bg-white/5 cursor-pointer min-w-[120px]"
                            disabled={isProcessing}
                            aria-label="Select output language"
                        >
                            <option value="Italian">🇮🇹 Italian</option>
                            <option value="English">🇬🇧 English</option>
                        </select>
                        <div className="absolute right-2 top-1/2 -translate-y-1/2 pointer-events-none text-gray-500">
                            <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="m6 9 6 6 6-6" /></svg>
                        </div>
                    </div>
                </div>

            </div>

            {/* Group 3: Agent Personalities */}
            <div className="flex items-center gap-4">

                {/* PRO Agent Personality */}
                <div className="flex flex-col">
                    <label
                        id="pro-personality-label"
                        className="flex items-center gap-1.5 text-[10px] uppercase tracking-widest text-gray-400 font-bold mb-1.5 ml-1"
                    >
                        <Shield size={10} style={{ color: 'var(--color-pro)' }} aria-hidden="true" />
                        <span>Defender Style</span>
                    </label>
                    <div
                        className="flex gap-1.5"
                        role="radiogroup"
                        aria-labelledby="pro-personality-label"
                    >
                        <button
                            onClick={() => setProPersonality('PASSIVE')}
                            disabled={isProcessing}
                            className={`px-3 py-1.5 text-xs rounded-lg transition-all ${proPersonality === 'PASSIVE'
                                    ? 'bg-accent text-white border-2 border-accent font-extrabold shadow-lg shadow-accent/50 scale-105'
                                    : 'bg-black/20 text-gray-400 border border-white/10 hover:bg-white/5 hover:border-white/20 font-normal opacity-60'
                                } ${isProcessing ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
                            role="radio"
                            aria-checked={proPersonality === 'PASSIVE'}
                            aria-label="Oliver - Passive defender personality (cautious and tentative)"
                        >
                            <div className="flex items-center gap-1.5">
                                <Feather size={12} />
                                <span>Oliver</span>
                            </div>
                        </button>
                        <button
                            onClick={() => setProPersonality('ASSERTIVE')}
                            disabled={isProcessing}
                            className={`px-3 py-1.5 text-xs rounded-lg transition-all ${proPersonality === 'ASSERTIVE'
                                    ? 'bg-accent text-white border-2 border-accent font-extrabold shadow-lg shadow-accent/50 scale-105'
                                    : 'bg-black/20 text-gray-400 border border-white/10 hover:bg-white/5 hover:border-white/20 font-normal opacity-60'
                                } ${isProcessing ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
                            role="radio"
                            aria-checked={proPersonality === 'ASSERTIVE'}
                            aria-label="Marcus - Assertive defender personality (confident and persuasive)"
                        >
                            <div className="flex items-center gap-1.5">
                                <Zap size={12} />
                                <span>Marcus</span>
                            </div>
                        </button>
                        <button
                            onClick={() => setProPersonality('AGGRESSIVE')}
                            disabled={isProcessing}
                            className={`px-3 py-1.5 text-xs rounded-lg transition-all ${proPersonality === 'AGGRESSIVE'
                                    ? 'bg-accent text-white border-2 border-accent font-extrabold shadow-lg shadow-accent/50 scale-105'
                                    : 'bg-black/20 text-gray-400 border border-white/10 hover:bg-white/5 hover:border-white/20 font-normal opacity-60'
                                } ${isProcessing ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
                            role="radio"
                            aria-checked={proPersonality === 'AGGRESSIVE'}
                            aria-label="Victor - Aggressive defender personality (forceful and confrontational)"
                        >
                            <div className="flex items-center gap-1.5">
                                <Flame size={12} />
                                <span>Victor</span>
                            </div>
                        </button>
                    </div>
                </div>

                <div className="w-px h-16 bg-white/10 mx-2"></div>

                {/* CONTRA Agent Personality */}
                <div className="flex flex-col">
                    <label
                        id="contra-personality-label"
                        className="flex items-center gap-1.5 text-[10px] uppercase tracking-widest text-gray-400 font-bold mb-1.5 ml-1"
                    >
                        <Search size={10} style={{ color: 'var(--color-contra)' }} aria-hidden="true" />
                        <span>Skeptic Style</span>
                    </label>
                    <div
                        className="flex gap-1.5"
                        role="radiogroup"
                        aria-labelledby="contra-personality-label"
                    >
                        <button
                            onClick={() => setContraPersonality('PASSIVE')}
                            disabled={isProcessing}
                            className={`px-3 py-1.5 text-xs rounded-lg transition-all ${contraPersonality === 'PASSIVE'
                                    ? 'bg-accent text-white border-2 border-accent font-extrabold shadow-lg shadow-accent/50 scale-105'
                                    : 'bg-black/20 text-gray-400 border border-white/10 hover:bg-white/5 hover:border-white/20 font-normal opacity-60'
                                } ${isProcessing ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
                            role="radio"
                            aria-checked={contraPersonality === 'PASSIVE'}
                            aria-label="Sophie - Passive skeptic personality (polite and diplomatic)"
                        >
                            <div className="flex items-center gap-1.5">
                                <Feather size={12} />
                                <span>Sophie</span>
                            </div>
                        </button>
                        <button
                            onClick={() => setContraPersonality('ASSERTIVE')}
                            disabled={isProcessing}
                            className={`px-3 py-1.5 text-xs rounded-lg transition-all ${contraPersonality === 'ASSERTIVE'
                                    ? 'bg-accent text-white border-2 border-accent font-extrabold shadow-lg shadow-accent/50 scale-105'
                                    : 'bg-black/20 text-gray-400 border border-white/10 hover:bg-white/5 hover:border-white/20 font-normal opacity-60'
                                } ${isProcessing ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
                            role="radio"
                            aria-checked={contraPersonality === 'ASSERTIVE'}
                            aria-label="Diana - Assertive skeptic personality (professional and firm)"
                        >
                            <div className="flex items-center gap-1.5">
                                <Zap size={12} />
                                <span>Diana</span>
                            </div>
                        </button>
                        <button
                            onClick={() => setContraPersonality('AGGRESSIVE')}
                            disabled={isProcessing}
                            className={`px-3 py-1.5 text-xs rounded-lg transition-all ${contraPersonality === 'AGGRESSIVE'
                                    ? 'bg-accent text-white border-2 border-accent font-extrabold shadow-lg shadow-accent/50 scale-105'
                                    : 'bg-black/20 text-gray-400 border border-white/10 hover:bg-white/5 hover:border-white/20 font-normal opacity-60'
                                } ${isProcessing ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
                            role="radio"
                            aria-checked={contraPersonality === 'AGGRESSIVE'}
                            aria-label="Raven - Aggressive skeptic personality (harsh and relentless)"
                        >
                            <div className="flex items-center gap-1.5">
                                <Flame size={12} />
                                <span>Raven</span>
                            </div>
                        </button>
                    </div>
                </div>

            </div>

        </div>
    );
};

export default ConfigPanel;
