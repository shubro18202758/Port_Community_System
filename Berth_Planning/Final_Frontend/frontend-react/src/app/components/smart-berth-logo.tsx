export function SmartBerthLogo({ className = "", size = 40 }: { className?: string; size?: number }) {
  return (
    <div className={`flex items-center gap-3 ${className}`}>
      <svg width={size} height={size} viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
        <defs>
          {/* Gradient for the main icon */}
          <linearGradient id="berthGradient" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#00D4AA" />
            <stop offset="50%" stopColor="#0C7BBD" />
            <stop offset="100%" stopColor="#0A4D8C" />
          </linearGradient>
          <linearGradient id="aiGradient" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#00E5BE" />
            <stop offset="100%" stopColor="#00A896" />
          </linearGradient>
          <linearGradient id="waveGradient" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stopColor="#0C7BBD" stopOpacity="0.4" />
            <stop offset="100%" stopColor="#0A4D8C" stopOpacity="0.1" />
          </linearGradient>
          {/* Glow filter */}
          <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
            <feGaussianBlur stdDeviation="2" result="coloredBlur"/>
            <feMerge>
              <feMergeNode in="coloredBlur"/>
              <feMergeNode in="SourceGraphic"/>
            </feMerge>
          </filter>
        </defs>

        {/* Background circle - port representation */}
        <circle cx="50" cy="50" r="46" fill="#0A1628" stroke="url(#berthGradient)" strokeWidth="2"/>

        {/* Inner ring - AI processing indicator */}
        <circle cx="50" cy="50" r="38" fill="none" stroke="#0C7BBD" strokeWidth="1" strokeDasharray="4 4" opacity="0.5"/>

        {/* Stylized S-shaped vessel path */}
        <path
          d="M 25 65 Q 35 65, 40 55 Q 45 45, 50 45 Q 55 45, 60 55 Q 65 65, 75 65"
          fill="none"
          stroke="url(#aiGradient)"
          strokeWidth="3"
          strokeLinecap="round"
          filter="url(#glow)"
        />

        {/* Modern vessel silhouette */}
        <g transform="translate(50, 32)">
          {/* Ship hull */}
          <path
            d="M -18 0 L 18 0 L 14 10 L -14 10 Z"
            fill="url(#berthGradient)"
          />
          {/* Ship bridge */}
          <rect x="-6" y="-8" width="12" height="8" rx="1" fill="#00D4AA"/>
          {/* AI antenna/sensor */}
          <circle cx="0" cy="-12" r="3" fill="#00E5BE" filter="url(#glow)"/>
          <line x1="0" y1="-8" x2="0" y2="-9" stroke="#00E5BE" strokeWidth="2"/>
        </g>

        {/* AI Neural nodes - representing smart technology */}
        <g filter="url(#glow)">
          {/* Left node cluster */}
          <circle cx="22" cy="40" r="4" fill="#00D4AA"/>
          <circle cx="18" cy="52" r="2.5" fill="#00A896"/>
          <line x1="22" y1="40" x2="18" y2="52" stroke="#00D4AA" strokeWidth="1"/>
          <line x1="22" y1="40" x2="32" y2="32" stroke="#00D4AA" strokeWidth="1" opacity="0.7"/>

          {/* Right node cluster */}
          <circle cx="78" cy="40" r="4" fill="#00D4AA"/>
          <circle cx="82" cy="52" r="2.5" fill="#00A896"/>
          <line x1="78" y1="40" x2="82" y2="52" stroke="#00D4AA" strokeWidth="1"/>
          <line x1="78" y1="40" x2="68" y2="32" stroke="#00D4AA" strokeWidth="1" opacity="0.7"/>
        </g>

        {/* Berth indicators at bottom */}
        <g transform="translate(50, 75)">
          <rect x="-25" y="0" width="50" height="4" rx="2" fill="#0C7BBD" opacity="0.8"/>
          <rect x="-20" y="4" width="3" height="6" rx="1" fill="#0A4D8C"/>
          <rect x="-8" y="4" width="3" height="6" rx="1" fill="#0A4D8C"/>
          <rect x="5" y="4" width="3" height="6" rx="1" fill="#0A4D8C"/>
          <rect x="17" y="4" width="3" height="6" rx="1" fill="#0A4D8C"/>
        </g>

        {/* Pulse rings - activity indicator */}
        <circle cx="50" cy="50" r="42" fill="none" stroke="#00D4AA" strokeWidth="0.5" opacity="0.3"/>
      </svg>
      <div className="flex flex-col">
        <div className="flex items-baseline gap-1.5">
          <span className="text-lg font-bold tracking-tight" style={{
            background: 'linear-gradient(135deg, #0C7BBD 0%, #00A896 100%)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            backgroundClip: 'text',
          }}>SmartBerth</span>
          <span className="text-[10px] px-1.5 py-0.5 rounded-md font-semibold" style={{
            background: 'linear-gradient(135deg, #00D4AA 0%, #00A896 100%)',
            color: 'white',
            letterSpacing: '0.5px'
          }}>AI</span>
        </div>
        <span className="text-[10px] tracking-wide" style={{ color: '#64748b' }}>Intelligent Port Operations</span>
      </div>
    </div>
  );
}
