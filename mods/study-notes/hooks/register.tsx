import { atom, read, update } from 'claude-code'
import type { Register } from 'claude-code'

import type { StudyNote } from '../types'

const PANE = 'study-notes'
const notes = atom({ plugin: 'study-notes', key: 'notes' } as const, [])
const pending = atom({ plugin: 'study-notes', key: 'pending' } as const, [])
const isWriting = atom({ plugin: 'study-notes', key: 'isWriting' } as const, false)

const EDIT_TOOLS = new Set(['Edit', 'Write', 'MultiEdit', 'NotebookEdit'])

export function fileName(path: string): string {
  return path.split('/').pop() ?? path
}

export function notePrompt(files: string[]): string {
  return [
    `방금 이 대화에서 다음 파일을 만들거나 고쳤습니다: ${files.join(', ')}`,
    '코딩을 모르는 사람이 공부할 수 있게 한국어로 학습 노트를 써 주세요.',
    '형식(마크다운, 전체 12줄 이내):',
    '### 무엇을 바꿨나',
    '- 한두 줄',
    '### 왜 바꿨나',
    '- 한두 줄 (사용자의 요청과 연결해서)',
    '### 오늘의 개념',
    '- 이번 변경에 나온 용어 1~2개를 비유로 쉽게 설명',
    '도구는 쓰지 말고 노트만 답하세요.',
  ].join('\n')
}

export const register: Register = on => {
  on('session.start', async ($, e, next) => {
    await $.command.register({
      name: 'study-notes',
      description: '학습 노트 패널 열기 (AI가 코드를 왜 바꿨는지 쉬운 설명)',
    })

    return next(e)
  })

  on('command.run', { command: 'study-notes' }, async $ => {
    await $.ui.open({ id: PANE, title: '📒 학습 노트' })

    return { text: '학습 노트 패널을 열었습니다.' }
  })

  on('tool.call', async ($, e, next) => {
    const ran = await next(e)
    const path = (e as { file_path?: unknown; notebook_path?: unknown }).file_path
      ?? (e as { notebook_path?: unknown }).notebook_path
    const isChange = EDIT_TOOLS.has(String(e.tool)) && ran.deny === undefined && ran.isError !== true
    if (isChange && typeof path === 'string') {
      await update($, pending, list => (list.includes(path) ? list : [...list, path]))
    }

    return ran
  })

  on('turn.complete', async ($, e, next) => {
    const done = await next(e)
    const files = await read($, pending)
    if (files.length === 0) {
      return done
    }

    await update($, pending, () => [])
    await update($, isWriting, () => true)
    const reply = await $.model.fork({ prompt: notePrompt(files.map(fileName)) })
    await update($, isWriting, () => false)
    if (!reply.isAnswered) {
      $.ui.log(`study-notes: 노트를 쓰지 못했습니다 (${reply.reason})`, { to: 'debug' })
      return done
    }

    const note: StudyNote = { at: await $.clock.now(), files: files.map(fileName), text: reply.text }
    await update($, notes, list => [...list, note].slice(-30))
    $.ui.toast('📒 학습 노트가 추가됐어요 (/study-notes)')

    return done
  })

  on('ui.render', { component: 'Pane', requestId: PANE }, async ($, e) => {
    const { Box, Markdown, Text } = $.ui.resolve(e)
    const list = await read($, notes)
    const writing = await read($, isWriting)

    return (
      <Box flexDirection="column">
        {writing && <Text color="yellow">✏️ 노트 작성 중…</Text>}
        {list.length === 0 && !writing && (
          <Text dimColor>아직 노트가 없어요. AI가 파일을 고치면 여기에 설명이 쌓입니다.</Text>
        )}
        {[...list].reverse().map(note => (
          <Box flexDirection="column" marginBottom={1}>
            <Text bold>📄 {note.files.join(', ')}</Text>
            <Markdown text={note.text} />
          </Box>
        ))}
      </Box>
    )
  })
}
