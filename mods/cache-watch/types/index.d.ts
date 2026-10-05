export type CacheWatchStamp = number | null

declare module 'claude-code' {
  interface PluginState {
    'cache-watch': { lastReplyAt: CacheWatchStamp; tick: number; isHidden: boolean }
  }
}
