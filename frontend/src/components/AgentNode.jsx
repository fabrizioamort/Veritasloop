
import React from 'react';
import { motion } from 'framer-motion';
import { Shield, Search, Gavel } from 'lucide-react';

const icons = {
    PRO: Shield,
    CONTRA: Search,
    JUDGE: Gavel
};

const colors = {
    PRO: 'var(--color-pro)',
    CONTRA: 'var(--color-contra)',
    JUDGE: 'var(--color-judge)'
};

// Agent names based on personality
const AGENT_NAMES = {
    PRO: {
        PASSIVE: "Oliver",
        ASSERTIVE: "Marcus",
        AGGRESSIVE: "Victor"
    },
    CONTRA: {
        PASSIVE: "Sophie",
        ASSERTIVE: "Diana",
        AGGRESSIVE: "Raven"
    }
};

const AgentNode = ({ role, status, label, personality }) => {
    const Icon = icons[role] || Shield;
    const color = colors[role];
    const isActive = status !== 'idle';

    // Get personality-based name if available
    const agentName = personality && AGENT_NAMES[role]
        ? AGENT_NAMES[role][personality]
        : null;

    // Construct display label
    const displayLabel = agentName ? `${agentName}` : label;

    return (
        <div className="flex flex-col items-center gap-4 p-6">
            <div className="relative">
                {/* Pulse Effect */}
                {/* Pulse Effect (Speaking/Active) */}
                {isActive && status !== 'searching' && (
                    <motion.div
                        initial={{ scale: 1, opacity: 0.5 }}
                        animate={{ scale: 1.5, opacity: 0 }}
                        transition={{ duration: 1.5, repeat: Infinity }}
                        className="absolute inset-0 rounded-full"
                        style={{ backgroundColor: color, filter: 'blur(10px)' }}
                    />
                )}

                {/* Searching Effect */}
                {status === 'searching' && (
                    <>
                        <motion.div
                            animate={{ rotate: 360 }}
                            transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
                            className="absolute inset-[-8px] rounded-full border border-dashed"
                            style={{ borderColor: color, opacity: 0.6 }}
                        />
                        <motion.div
                            animate={{ rotate: -360 }}
                            transition={{ duration: 3, repeat: Infinity, ease: "linear" }}
                            className="absolute inset-[-15px] rounded-full border border-dotted"
                            style={{ borderColor: color, opacity: 0.3 }}
                        />
                    </>
                )}

                {/* Core Icon */}
                <motion.div
                    animate={{ scale: isActive ? 1.1 : 1 }}
                    className="relative z-10 p-6 rounded-full glass-panel border-2"
                    style={{ borderColor: color, boxShadow: `0 0 20px ${color}40` }}
                >
                    <Icon size={48} color={color} />
                </motion.div>
            </div>

            <div className="text-center">
                <h3 className="text-xl font-bold tracking-wider" style={{ color }}>{displayLabel}</h3>
                <p className="text-xs text-gray-500 uppercase tracking-widest mb-1">
                    {role} AGENT
                </p>
                <p className="text-sm font-mono text-muted animate-pulse">
                    {isActive ? status.toUpperCase() : 'STANDBY'}
                </p>
            </div>
        </div>
    );
};

export default AgentNode;
