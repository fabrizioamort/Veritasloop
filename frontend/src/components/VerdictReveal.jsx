
import React from 'react';
// eslint-disable-next-line no-unused-vars -- motion is used in JSX
import { motion } from 'framer-motion';
import { CheckCircle, XCircle, AlertTriangle, HelpCircle } from 'lucide-react';

const VerdictReveal = ({ data, onReset, onReviewDebate }) => {
    if (!data) return null;

    const { verdict, confidence_score, summary, analysis } = data;

    const config = {
        VERO: { color: '#4caf50', Icon: CheckCircle, label: 'VERIFIED TRUE' },
        FALSO: { color: '#f44336', Icon: XCircle, label: 'VERIFIED FALSE' },
        PARZIALMENTE_VERO: { color: '#ffb74d', Icon: AlertTriangle, label: 'PARTIALLY TRUE' },
        CONTESTO_MANCANTE: { color: '#ab47bc', Icon: HelpCircle, label: 'MISSING CONTEXT' },
        NON_VERIFICABILE: { color: '#9e9e9e', Icon: HelpCircle, label: 'UNVERIFIABLE' }
    };

    const { color, Icon, label } = config[verdict] || config.NON_VERIFICABILE;

    return (
        <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className="absolute inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-md p-8"
            role="dialog"
            aria-modal="true"
            aria-labelledby="verdict-title"
            aria-describedby="verdict-summary"
        >
            <div className="max-w-4xl w-full glass-panel p-8 md:p-12 border-2" style={{ borderColor: color, boxShadow: `0 0 50px ${color}20` }}>
                <div className="flex flex-col items-center text-center">
                    <Icon size={80} color={color} className="mb-6" aria-hidden="true" />

                    <h1 id="verdict-title" className="text-4xl md:text-6xl font-black tracking-widest mb-2" style={{ color }}>
                        {label}
                    </h1>

                    <div className="text-2xl font-mono text-white/80 mb-8" aria-label={`Confidence score: ${confidence_score} percent`}>
                        CONFIDENCE: {confidence_score}%
                    </div>

                    <p id="verdict-summary" className="text-lg text-secondary leading-relaxed max-w-2xl mb-8">
                        {summary}
                    </p>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6 w-full mb-8" role="region" aria-label="Debate analysis">
                        <div className="p-4 bg-white/5 rounded-lg border border-white/5">
                            <h3 className="text-sm font-mono text-muted mb-2">PRO STRENGTH</h3>
                            <p className="text-white">{analysis?.pro_strength || "N/A"}</p>
                        </div>
                        <div className="p-4 bg-white/5 rounded-lg border border-white/5">
                            <h3 className="text-sm font-mono text-muted mb-2">CONTRA STRENGTH</h3>
                            <p className="text-white">{analysis?.contra_strength || "N/A"}</p>
                        </div>
                    </div>

                    <div className="flex gap-4" role="group" aria-label="Verdict actions">
                        <button
                            onClick={onReset}
                            className="px-8 py-3 bg-white text-black font-bold rounded hover:scale-105 transition-transform"
                            aria-label="Start a new verification"
                        >
                            VERIFY ANOTHER CLAIM
                        </button>
                        <button
                            onClick={onReviewDebate}
                            className="px-8 py-3 border border-white text-white font-bold rounded hover:bg-white/10 transition-colors"
                            aria-label="Review the full debate transcript"
                        >
                            REVIEW DEBATE
                        </button>
                    </div>
                </div>
            </div>
        </motion.div>
    );
};

export default VerdictReveal;
