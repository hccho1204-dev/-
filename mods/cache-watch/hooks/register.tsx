import { atom, read, update } from 'claude-code'
import type { Register } from 'claude-code'

// 프롬프트 캐시는 마지막 요청 뒤 1시간 동안 유지됩니다.
const CACHE_MS = 60 * 60 * 1000

const lastReplyAt = atom({ plugin: 'cache-watch', key: 'lastReplyAt' } as const, null)
const tick = atom({ plugin: 'cache-watch', key: 'tick' } as const, 0)
const isHidden = atom({ plugin: 'cache-watch', key: 'isHidden' } as const, false)

/** 컨텍스트 사용률을 날씨로 바꿉니다 (토큰 웨더). */
export function weather(percent: number): string {
  if (percent < 40) return '☀️ 맑음'
  if (percent < 60) return '⛅ 구름'
  if (percent < 80) return '🌧️ 소나기'
  return '⛈️ 폭풍'
}

export function cacheLeft(now: number, last: number | null): string {
  if (last === null) return '⏱ 캐시 대기'
  const left = Math.ceil((last + CACHE_MS - now) / 60000)
  return left > 0 ? `⏱ 캐시 ${left}분` : '⏱ 캐시 만료'
}

export const register: Register = on => {
  on('session.start', async ($, e, next) => {
    $.clock.every(60 * 1000, () => {
      void update($, tick, n => n + 1)
    })

    return next(e)
  })

  on('turn.complete', async ($, e, next) => {
    const now = await $.clock.now()
    await update($, lastReplyAt, () => now)

    return next(e)
  })

  on('ui.render', { component: 'AbovePrompt' }, async ($, e, next) => {
    await read($, tick)
    const last = await read($, lastReplyAt)
    if (e.props.hasSurvey || (await read($, isHidden))) {
      return next(e)
    }

    const usage = await $.session.usage()
    const percent = usage.context.percent ?? 0
    const now = await $.clock.now()
    const cost = usage.cost === undefined ? '' : ` · 💰 $${usage.cost.usd.toFixed(2)}`
    const isExpired = last !== null && now - last >= CACHE_MS
    const { Box, Button, Text } = $.ui.resolve(e)

    return (
      <Box>
        <Text color={isExpired ? 'red' : undefined} dimColor={!isExpired}>
          {cacheLeft(now, last)} · 🧠 컨텍스트 {percent}% {weather(percent)}
          {cost}{' '}
        </Text>
        <Button key="hide" label="숨기기" onPress={() => update($, isHidden, () => true)} />
      </Box>
    )
  })
}
