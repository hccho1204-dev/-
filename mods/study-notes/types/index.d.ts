export type StudyNote = { at: number; files: string[]; text: string }

declare module 'claude-code' {
  interface PluginState {
    'study-notes': { notes: StudyNote[]; pending: string[]; isWriting: boolean }
  }
}
