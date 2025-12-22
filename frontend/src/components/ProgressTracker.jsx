import React from 'react';
import { Target, Search, MessageSquare, Scale } from 'lucide-react';

const steps = [
    { id: 'analysis', label: 'Analysis', icon: Target },
    { id: 'research', label: 'Research', icon: Search },
    { id: 'debate', label: 'Debate', icon: MessageSquare },
    { id: 'verdict', label: 'Verdict', icon: Scale },
];

const ProgressTracker = ({ currentStep }) => {
    // Helper to determine step status: 'complete', 'current', 'pending'
    const getStepStatus = (stepId, index) => {
        const stepOrder = ['analysis', 'research', 'debate', 'verdict'];
        const currentIndex = stepOrder.indexOf(currentStep);

        if (index < currentIndex) return 'complete';
        if (index === currentIndex) return 'current';
        return 'pending';
    };

    return (
        <div className="w-full max-w-2xl mx-auto mb-4 px-4">
            <div className="relative flex justify-between items-center">
                {/* Connecting Line */}
                <div className="absolute top-1/2 left-0 w-full h-0.5 bg-white/10 -z-10 transform -translate-y-1/2 rounded-full"></div>
                <div
                    className="absolute top-1/2 left-0 h-0.5 bg-accent -z-10 transform -translate-y-1/2 rounded-full transition-all duration-500"
                    style={{
                        width: `${(Math.max(0, ['analysis', 'research', 'debate', 'verdict'].indexOf(currentStep)) / 3) * 100}%`
                    }}
                ></div>

                {steps.map((step, index) => {
                    const status = getStepStatus(step.id, index);
                    const Icon = step.icon;

                    return (
                        <div key={step.id} className="flex flex-col items-center gap-2 relative group">
                            <div
                                className={`w-8 h-8 rounded-full flex items-center justify-center border-2 transition-all duration-300 z-10 
                                    ${status === 'complete' ? 'bg-accent border-accent text-white scale-110' :
                                        status === 'current' ? 'bg-black border-accent text-accent shadow-[0_0_15px_rgba(var(--accent-rgb),0.5)] scale-125' :
                                            'bg-black/40 border-white/10 text-gray-500'}`}
                            >
                                <Icon size={14} strokeWidth={status === 'current' ? 2.5 : 2} />
                            </div>
                            <span
                                className={`absolute -bottom-6 text-[10px] uppercase tracking-wider font-bold whitespace-nowrap transition-colors duration-300
                                    ${status === 'current' ? 'text-accent' :
                                        status === 'complete' ? 'text-gray-300' :
                                            'text-gray-600'}`}
                            >
                                {step.label}
                            </span>
                        </div>
                    );
                })}
            </div>
        </div>
    );
};

export default ProgressTracker;
