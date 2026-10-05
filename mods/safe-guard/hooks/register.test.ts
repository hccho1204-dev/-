import { expect, test } from 'claude-code/testing'

import { findRisk } from './register'

test('위험 명령은 잡고 평범한 명령은 통과시킨다', async () => {
  expect(findRisk('rm -rf build')).toBeDefined()
  expect(findRisk('git push --force origin main')).toBeDefined()
  expect(findRisk('git reset --hard HEAD~1')).toBeDefined()
  expect(findRisk('ls -la')).toBeUndefined()
  expect(findRisk('git push -u origin feature')).toBeUndefined()
  expect(findRisk('npm run build')).toBeUndefined()
})
