import { expect, test } from 'claude-code/testing'

import { fileName, notePrompt } from './register'

test('노트 요청문에 고친 파일 이름이 들어간다', async () => {
  expect(fileName('/home/me/app/src/main.py')).toBe('main.py')
  expect(notePrompt(['main.py', 'app.tsx'])).toContain('main.py, app.tsx')
})
