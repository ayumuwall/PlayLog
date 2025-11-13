import { contextBridge, ipcRenderer } from 'electron';

contextBridge.exposeInMainWorld('playlog', {
  platform: process.platform,
  getPlatform: async (): Promise<string> => ipcRenderer.invoke('playlog:get-platform'),
});
