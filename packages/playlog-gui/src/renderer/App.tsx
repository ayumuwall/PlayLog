import { ChangeEvent, useEffect, useState } from 'react';

export function App(): JSX.Element {
  const [platform, setPlatform] = useState('unknown');
  const [seratoMode, setSeratoMode] = useState<'auto' | 'crate' | 'logs'>('auto');
  const [seratoRoot, setSeratoRoot] = useState('');
  const [timelineEstimate, setTimelineEstimate] = useState(false);

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
      <section>
        <h2>Serato 設定（ベータ）</h2>
        <label>
          モード
          <select
            value={seratoMode}
            onChange={(event: ChangeEvent<HTMLSelectElement>) =>
              setSeratoMode(event.target.value as 'auto' | 'crate' | 'logs')
            }
          >
            <option value="auto">auto（crate→logs フォールバック）</option>
            <option value="crate">crate</option>
            <option value="logs">logs</option>
          </select>
        </label>
        <label>
          _Serato_ ルート
          <input
            type="text"
            placeholder="~/Music/_Serato_"
            value={seratoRoot}
            onChange={(event: ChangeEvent<HTMLInputElement>) => setSeratoRoot(event.target.value)}
          />
        </label>
        <label>
          <input
            type="checkbox"
            checked={timelineEstimate}
            onChange={(event: ChangeEvent<HTMLInputElement>) => setTimelineEstimate(event.target.checked)}
          />
          タイムライン推定（crateに時刻が無い場合）
        </label>
        <p>
          現在の設定: mode={seratoMode}, timeline-estimate={timelineEstimate ? 'on' : 'off'}, root=
          {seratoRoot || '(未設定)'}
        </p>
      </section>
    </main>
  );
}
