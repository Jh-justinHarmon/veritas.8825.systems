interface BackgroundLayerProps {
  site: 'claude' | 'langchain' | 'stripe';
}

const SITE_CONFIG = {
  claude: {
    image: '/screenshots/claude-screenshot.png',
    overlay: 'rgba(255, 255, 255, 0.21)',
  },
  langchain: {
    image: '/screenshots/langchain-screenshot.png',
    overlay: 'rgba(255, 255, 255, 0.34)',
  },
  stripe: {
    image: '/screenshots/stripe-screenshot.png',
    overlay: 'rgba(0, 0, 0, 0.55)',
  },
};

export default function BackgroundLayer({ site }: BackgroundLayerProps) {
  const config = SITE_CONFIG[site];

  return (
    <div
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        width: '100%',
        height: '100%',
        zIndex: -1,
        pointerEvents: 'none',
        overflow: 'hidden',
      }}
    >
      {/* Background image with blur */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          width: '100%',
          height: '100%',
          backgroundImage: `url(${config.image})`,
          backgroundSize: 'cover',
          backgroundPosition: 'center',
          filter: 'blur(8px)',
          transform: 'scale(1.05)',
        }}
      />
      
      {/* Overlay tint */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          width: '100%',
          height: '100%',
          backgroundColor: config.overlay,
        }}
      />
    </div>
  );
}
