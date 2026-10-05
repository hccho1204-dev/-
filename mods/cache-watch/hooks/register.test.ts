import { expect, test } from 'claude-code/testing'

import { cacheLeft, weather } from './register'

test('컨텍스트 사용률이 날씨로 바뀐다', async () => {
  expect(weather(10)).toBe('☀️ 맑음')
  expect(weather(55)).toBe('⛅ 구름')
  expect(weather(70)).toBe('🌧️ 소나기')
  expect(weather(90)).toBe('⛈️ 폭풍')
})

test('캐시 남은 시간을 분 단위로 보여준다', async () => {
  expect(cacheLeft(0, null)).toBe('⏱ 캐시 대기')
  expect(cacheLeft(2 * 60000, 0)).toBe('⏱ 캐시 58분')
  expect(cacheLeft(61 * 60000, 0)).toBe('⏱ 캐시 만료')
})
