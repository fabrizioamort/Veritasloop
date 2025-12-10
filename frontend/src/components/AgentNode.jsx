
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

const AgentNode = ({ role, status, label }) => {
    const Icon = icons[role] || Shield;
    const color = colors[role];
    const isActive = status !== 'idle';

    return (
        <div className="flex flex-col items-center gap-4 p-6">
            <div className="relative">
                {/* Pulse Effect */}
                {isActive && (
                    <motion.div
                        initial={{ scale: 1, opacity: 0.5 }}
                        animate={{ scale: 1.5, opacity: 0 }}
                        transition={{ duration: 1.5, repeat: Infinity }}
                        className="absolute inset-0 rounded-full"
                        style={{ backgroundColor: color, filter: 'blur(10px)' }}
                    />
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
                <h3 className="text-xl font-bold tracking-wider" style={{ color }}>{label}</h3>
                <p className="text-sm font-mono text-muted animate-pulse">
                    {isActive ? status.toUpperCase() : 'STANDBY'}
                </p>
            </div>
        </div>
    );
};

export default AgentNode;
