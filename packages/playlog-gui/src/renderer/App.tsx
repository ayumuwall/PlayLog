import { useEffect, useState } from 'react';

export function App(): JSX.Element {
  const [platform, setPlatform] = useState('unknown');

  useEffect(() => {
    let mounted = true;
    const fetchPlatform = async (): Promise<void> => {
      if (typeof window.playlog?.getPlatform === 'function') {
        const result = await window.playlog.getPlatform();
        if (mounted) {
          setPlatform(result);
        }
      } else if (window.playlog?.platform) {
        setPlatform(window.playlog.platform);
      }
    };
    void fetchPlatform();
    return () => {
      mounted = false;
    };
  }, []);

  return (
    <main>
      <h1>PlayLog GUI</h1>
      <p>Detected platform: {platform}</p>
      <p>Electron + React scaffoldingが正常に動作しています。</p>
    </main>
  );
}
