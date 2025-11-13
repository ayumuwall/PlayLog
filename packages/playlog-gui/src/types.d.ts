export interface PlaylogBridge {
  readonly platform: string;
  getPlatform?: () => Promise<string>;
}

declare global {
  interface Window {
    playlog: PlaylogBridge;
  }
}
