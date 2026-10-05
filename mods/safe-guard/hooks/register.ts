import type { Register } from 'claude-code'

/** 되돌리기 어려운 명령과, 비개발자용 쉬운 설명 */
const RISKY: ReadonlyArray<{ pattern: RegExp; why: string }> = [
  { pattern: /\brm\s+(-[a-zA-Z]*[rf][a-zA-Z]*\s+)+/, why: '파일·폴더를 휴지통 없이 바로 지웁니다' },
  { pattern: /\bgit\s+push\b.*(--force\b|-f\b|--force-with-lease)/, why: '온라인 저장소의 기록을 덮어씁니다' },
  { pattern: /\bgit\s+reset\s+--hard\b/, why: '저장 안 한 작업 내용을 모두 버립니다' },
  { pattern: /\bgit\s+clean\s+-[a-zA-Z]*f/, why: '추적하지 않는 파일을 모두 지웁니다' },
  { pattern: /\bgit\s+(checkout|restore)\s+(--\s+)?\.(\s|$)/, why: '수정 중인 내용을 모두 되돌립니다' },
  { pattern: /\bgit\s+branch\s+-D\b/, why: '브랜치를 강제로 삭제합니다' },
  { pattern: /\b(drop|truncate)\s+(table|database)\b/i, why: '데이터베이스 내용을 지웁니다' },
  { pattern: /\bdelete\s+from\s+\w+\s*(;|$)/i, why: '조건 없이 표 전체 데이터를 지웁니다' },
  { pattern: /\b(mkfs|dd\s+if=)/, why: '디스크를 덮어씁니다' },
  { pattern: /\bchmod\s+-R\s+777\b/, why: '모든 파일 권한을 활짝 엽니다' },
]

export function findRisk(command: string): string | undefined {
  return RISKY.find(one => one.pattern.test(command))?.why
}

const RUN = '실행'
const CANCEL = '취소'

export const register: Register = on => {
  on('tool.call', { tool: 'Bash' }, async ($, e, next) => {
    const why = findRisk(e.command)
    if (why === undefined) {
      return next(e)
    }

    $.ui.toast(`⚠️ 위험 명령 감지: ${why}`)
    const short = e.command.length > 120 ? `${e.command.slice(0, 120)}…` : e.command
    let answer = CANCEL
    try {
      answer = await $.ui.ask(`⚠️ ${why}. 정말 실행할까요?  ${short}`, {
        header: '위험 명령',
        options: [RUN, CANCEL],
      })
    } catch {
      answer = CANCEL
    }

    if (answer !== RUN) {
      return { deny: `${$.plugin.name}: 사용자가 위험 명령을 취소했습니다 (${why}). 다른 방법을 찾거나 사용자에게 물어보세요.` }
    }

    $.ui.log(`safe-guard: 사용자 확인 후 실행 — ${short}`)

    return next(e)
  })
}
