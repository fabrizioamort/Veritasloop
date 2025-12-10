
import React, { useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

const DebateStream = ({ messages }) => {
    const bottomRef = useRef(null);

    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    return (
        <div className="flex-1 overflow-y-auto p-4 space-y-4 pr-2">
            <AnimatePresence>
                {messages.map((msg, index) => {
                    const isPro = msg.agent === 'PRO';
                    const color = isPro ? 'var(--color-pro)' : 'var(--color-contra)';

                    return (
                        <motion.div
                            key={index}
                            initial={{ opacity: 0, x: isPro ? -20 : 20 }}
                            animate={{ opacity: 1, x: 0 }}
                            className={`p-4 rounded-lg border-l-4 glass-panel max-w-[90%] ${isPro ? 'mr-auto' : 'ml-auto'}`}
                            style={{ borderLeftColor: color }}
                        >
                            <div className="flex justify-between items-baseline mb-2">
                                <span className="font-bold text-sm tracking-wide" style={{ color }}>
                                    {msg.agent}
                                </span>
                                <span className="text-xs text-muted font-mono">ROUND {msg.round}</span>
                            </div>

                            <p className="text-sm leading-relaxed text-secondary border-l border-white/10 pl-3">
                                {msg.content}
                            </p>

                            {msg.sources && msg.sources.length > 0 && (
                                <div className="mt-3 pt-3 border-t border-white/5">
                                    <p className="text-xs font-mono text-muted mb-2">SOURCES:</p>
                                    <div className="flex flex-wrap gap-2">
                                        {msg.sources.map((src, i) => (
                                            <a
                                                key={i}
                                                href={src.url}
                                                target="_blank"
                                                rel="noopener noreferrer"
                                                className="text-xs px-2 py-1 bg-white/5 rounded hover:bg-white/10 transition-colors truncate max-w-[200px]"
                                                style={{ color: color }}
                                            >
                                                {src.title || src.url}
                                            </a>
                                        ))}
                                    </div>
                                </div>
                            )}
                        </motion.div>
                    );
                })}
            </AnimatePresence>
            <div ref={bottomRef} />
        </div>
    );
};

export default DebateStream;
