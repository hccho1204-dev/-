// 체험 모드: API 키 없이도 전체 흐름(토론→배정→수행→반려→보강→전략→승인→발행)을 볼 수 있게 만든 가짜 응답
const { agents, company } = require('./env');

const pick = (arr, n) => arr.slice(0, n);
const short = (s, n = 40) => (s.length > n ? s.slice(0, n) + '…' : s);
const wantsMax = (t) => /극대화|좋아요|리포스트|조회수/.test(t.instruction);

function triage(t) {
  const staff = agents().filter((a) => a.tier === 'staff');
  const scored = staff
    .map((a) => ({ id: a.id, score: a.keywords.filter((k) => t.instruction.includes(k)).length }))
    .sort((x, y) => y.score - x.score);
  let relevant = scored.filter((s) => s.score > 0).map((s) => s.id);
  if (t.publish?.enabled && !relevant.includes('jopalo')) relevant.unshift('jopalo');
  if (relevant.length < 2) relevant = [...new Set([...relevant, 'jopalo', 'moncherry', 'johoesu'])];
  const taskType = t.publish?.enabled ? 'threads_post' : /분석|성과|제안|리포트/.test(t.instruction) ? 'analysis' : 'general';
  return {
    taskType,
    title: short(t.instruction.replace(/\s+/g, ' '), 28),
    relevant: pick(relevant, 4),
    agenda: `CEO 지시 "${short(t.instruction, 50)}"를 마감(${t.deadline}) 안에 어떻게 실행할 것인가`,
    keyQuestions: ['마감 안에 가능한가', '회사 브랜드에 도움이 되는가', '무엇을 성공으로 볼 것인가'],
  };
}

const OPINIONS = {
  jopalo: (t) => `쓰레드 운영 쪽에서 먼저 말씀드립니다. 마감이 ${t.deadline}이라 오늘 안에 승인까지 받아서 내보내려면 일정이 빠듯합니다. ${wantsMax(t) ? '그리고 솔직히 걸리는 게 있습니다. 첫 게시물인데 리포스트·좋아요 극대화를 목표로 잡는 건 위험합니다. ' : ''}첫 게시물은 계정의 첫인상입니다. 첫인상이 브랜드 정체성보다 조회수 위주로 남으면 이후에 손해입니다. 제안: 반응 유도는 질문형 마무리 한 줄로 절제하고, "이 계정이 뭘 하는 곳인지"가 보이게 가죠. 게시 시간은 저녁 8~9시를 추천합니다.`,
  moncherry: () => `조팔로 님 의견에 동의합니다. 브랜드 문체 기준으로 보면 "좋아요 눌러주세요" 같은 문구는 금지 표현에 가깝습니다. 첫 문장은 솔직한 고백형으로 가겠습니다. 예: "AI 직원 10명에게 첫 게시물을 맡겨봤습니다." 문구 2안을 만들어 비교해 드리겠습니다.`,
  johoesu: () => `콘텐츠 입장에서 핵심은 첫 3초입니다. 영상이라면 가장 강한 장면을 앞으로 빼야 하고, 글에서는 "왜 이걸 봐야 하는지"를 첫 줄에 넣어야 합니다. 반응 극대화 목표 자체는 나쁘지 않다고 봅니다. 다만 방법이 자극이 아니라 '궁금증'이어야 합니다.`,
  kimgeungeo: () => `근거 담당으로서 한 가지 확인이 필요합니다. AI 뮤직비디오라면 음원과 영상 생성 도구의 상업적 이용 조건을 확인해야 합니다. 출처 확인 없이 올렸다가 신고당하면 첫 게시물부터 계정 신뢰가 깨집니다. 체크리스트로 정리하겠습니다.`,
  jeonhwanyul: (t) => `데이터 관점입니다. "극대화"는 측정할 수 없으면 목표가 아닙니다. 게시 후 24시간 기준 조회·좋아요·리포스트·답글을 측정 시점으로 정하죠. ${/분석|성과/.test(t.instruction) ? '지난 게시물 수치가 있으면 그걸 기준선으로 쓰겠습니다.' : '첫 게시물이라 기준선이 없으니 이번 수치가 기준선이 됩니다.'}`,
  anberg: () => `기술 쪽 사실부터 말씀드립니다. 쓰레드 API로 글은 바로 올라가지만, 영상은 파일을 직접 올릴 수 없고 "공개 인터넷 주소(URL)"가 있어야 합니다. 대안은 두 가지: ① 공개 주소를 만들어 API로 올리기 ② CEO께서 직접(수동) 업로드. 오늘 마감이면 ②가 안전합니다.`,
  joyoungmi: () => `디자인 쪽입니다. 영상 첫 장면이 곧 썸네일 역할을 합니다. 첫 프레임에 글자가 너무 많으면 모바일에서 안 읽힙니다. 첫 장면 가이드를 한 장으로 정리하겠습니다.`,
  majinyul: () => `커머스 입장에서는 첫 게시물에서 판매 동선은 넣지 않는 걸 추천합니다. 첫인상에서 파는 느낌이 나면 팔로우 전환이 떨어집니다. 수익화는 5번째 게시물 이후에 검토하죠.`,
};

function opinion(agentId, t) {
  return (OPINIONS[agentId] || (() => '제 담당 관점에서 특별한 반대는 없습니다. 배정해 주시면 바로 진행하겠습니다.'))(t);
}

const REACTIONS = {
  majinyul: '판매 링크는 이번엔 빼는 게 맞다고 봅니다. 첫인상 우선에 동의합니다.',
  anberg: '영상은 API 직접 업로드가 안 됩니다. 발행 방식은 제가 확인하겠습니다.',
  joyoungmi: '첫 장면에 글자를 최소화해 주세요. 모바일에서 안 읽힙니다.',
  kimgeungeo: '음원 출처 확인은 꼭 문서로 남겨주세요.',
  jeonhwanyul: '성공 기준을 숫자로 정해두지 않으면 나중에 분석을 못 합니다.',
  johoesu: '첫 줄 훅 아이디어 몇 개 보태겠습니다.',
  moncherry: '문구에 금지 표현 없는지 마지막에 제가 한 번 더 보겠습니다.',
  jopalo: '게시 시간은 저녁 8~9시가 좋겠습니다.',
};
function reactions(t, others) {
  return others.slice(0, 5).map((id, i) => ({ agent: id, text: i === 3 ? null : REACTIONS[id] || null }));
}
function rebuttal(agentId) {
  return `${agentId === 'johoesu' ? '브랜드 우선에 동의하되, 첫 줄은 궁금증을 자극하는 방향으로 가겠습니다.' : '앞선 의견들 반영해서 제 파트 조정하겠습니다.'}`;
}

const TASKS = {
  jopalo: ['게시 운영안', '게시 시간, 첫 댓글 문구, 24시간 반응 대응 계획'],
  moncherry: ['게시 문구 2안', '브랜드 톤에 맞는 게시 문구 2안과 금지 표현 점검'],
  johoesu: ['콘텐츠 포인트', '영상/글의 핵심 장면과 첫 줄 훅 3개'],
  kimgeungeo: ['저작권·정책 체크', '음원·영상 출처와 플랫폼 정책 위반 여부 체크리스트'],
  jeonhwanyul: ['성과 지표 계획', '성공 지표(KPI)와 측정 시점, 기준선'],
  joyoungmi: ['첫 장면 가이드', '영상 첫 장면/커버 가이드'],
  anberg: ['게시 기술 점검', '텍스트/영상 게시 방식과 대안'],
  majinyul: ['수익화 검토', '이번 게시물의 수익화 동선 필요 여부'],
};
function assign(t) {
  const ids = t.relevant.slice(0, 4);
  if (t.publish?.enabled && !ids.includes('moncherry')) ids.push('moncherry');
  if (t.publish?.enabled && !ids.includes('anberg') && t.publish.videoFile) ids.push('anberg');
  return {
    summary: `토론 결과, CEO 지시는 실행하되 '반응 극대화'는 자극이 아닌 궁금증·질문형 마무리로 달성하기로 했습니다. 첫인상은 브랜드 정체성 우선.`,
    direction: '브랜드 정체성을 먼저 보여주고, 반응은 자연스럽게 유도한다. 성과는 24시간 수치로 측정한다.',
    decisions: ['게시 시간 저녁 8~9시', '좋아요·리포스트 요청 문구 금지', '24시간 후 성과 측정'],
    ceoAdjustments: wantsMax(t) ? '“리포스트·좋아요 극대화” → “브랜드 첫인상을 지키면서 반응 극대화”로 조정. 이유: 첫 게시물이 조회수용 계정으로 인식되면 장기적으로 손해.' : '조정 없음',
    assignments: ids.map((id) => ({ agent: id, task: (TASKS[id] || ['담당 업무', '담당 관점에서 필요한 작업'])[1], deliverable: (TASKS[id] || ['담당 업무'])[0] })),
  };
}

function execute(a, asg, t) {
  const fix = (t.pendingFixes || []).find((f) => f.agent === a.id);
  const rein = (t.reinforcements || []).slice(-1)[0];
  return `> 한줄요약: ${a.name}의 ${asg.deliverable} — ${asg.task}를 정리한 문서다.

# ${asg.deliverable} (${a.title} ${a.name}, ${t.round}차)

## 결론
- ${asg.task}: 준비 완료. 방향은 "${t.direction || '브랜드 우선'}"에 맞췄습니다.

## 내용
1. 첫 줄 후보: "AI 직원 10명에게 첫 게시물을 맡겨봤습니다."
2. 마무리 질문: "여러분이라면 AI에게 어떤 일을 먼저 맡기시겠어요?"
3. 측정: 게시 24시간 후 조회·좋아요·리포스트·답글 기록 (추정 아님, 실측)

${fix ? `## 보강 반영 (비서실장 반려 사유)\n- 요청: ${fix.request}\n- 반영: 요청대로 수정했습니다.\n` : ''}${rein && t.round > 1 ? `## CEO 보강 지시 반영\n- 지시: ${rein.text}\n- 반영: 결론을 맨 위로 올리고, 근거와 담당·마감을 명시했습니다.\n` : ''}`;
}

function review(t, checklistItems) {
  if (t.round === 1) {
    return {
      verdict: 'reject',
      checklist: checklistItems.map((item, i) => ({ item, pass: !(i === 1 || i === checklistItems.length - 1), note: i === 1 ? '첫 문장이 약함' : i === checklistItems.length - 1 ? '담당·마감 누락' : '' })),
      reasons: ['첫 줄만 읽고 멈춰서 볼 이유가 부족합니다', '다음 행동에 담당자·마감일이 빠져 있습니다'],
      fixRequests: t.assignments.slice(0, 2).map((x) => ({ agent: x.agent, request: '첫 문장을 구체적인 장면으로 바꾸고, 다음 행동에 담당·마감을 넣을 것' })),
      lesson: '첫 문장과 "담당·마감"은 작업 전에 완료 기준을 읽었으면 막을 수 있었다',
    };
  }
  return {
    verdict: 'approve',
    checklist: checklistItems.map((item) => ({ item, pass: true, note: '' })),
    reasons: ['모든 완료 기준 통과'],
    fixRequests: [],
    lesson: '',
  };
}

function reworkAssign(t) {
  const ids = [...new Set((t.pendingFixes || []).map((f) => f.agent).concat(t.assignments.slice(0, 1).map((a) => a.agent)))];
  return {
    message: 'CEO 보강 지시와 반려 사유를 합쳐 수정 작업을 배정합니다.',
    assignments: ids.map((id) => ({ agent: id, task: '반려 사유와 CEO 보강 지시 반영', deliverable: (TASKS[id] || ['수정본'])[0] + ' 수정본' })),
  };
}

function strategy(t) {
  return {
    verdict: 'caution',
    summary: '실행은 가능하나, 단기 반응 목표가 브랜드 정체성을 흐릴 위험이 있습니다.',
    concerns: [
      { issue: '첫 게시물 반응 극대화 목표', why: '첫인상이 조회수 계정으로 굳으면 이후 전문성 콘텐츠의 신뢰가 떨어짐', severity: 'mid' },
      { issue: t.publish?.videoFile ? '영상 API 업로드 제약' : '성과 측정 기준선 부재', why: t.publish?.videoFile ? '공개 URL이 없으면 자동 게시 불가 → 마감 직전 수동 전환 위험' : '첫 게시물이라 비교 대상이 없음', severity: t.publish?.videoFile ? 'high' : 'low' },
      { issue: '마감 압박으로 검수 생략', why: '오늘 마감이라 저작권 확인이 형식적으로 끝날 수 있음', severity: 'mid' },
    ],
    recommendations: ['게시 문구에서 반응 요청 문구 완전 제거', t.publish?.videoFile ? '영상은 CEO 수동 게시를 기본안으로' : '이번 수치를 기준선으로 기록', '24시간 후 성과 분석 업무 자동 생성'],
  };
}

function final(t) {
  const c = company();
  const post = t.publish?.enabled
    ? `AI 직원 10명에게 첫 게시물을 맡겨봤습니다.\n\n토론하고, 일을 나누고, 서로 검수하고,\n반려도 한 번 당했습니다.\n\n그렇게 나온 첫 결과물이 이 ${t.publish.videoFile ? '영상' : '글'}입니다.\n\n여러분이라면 AI에게 어떤 일을 먼저 맡기시겠어요?`
    : null;
  return {
    strategyDecisions: (t.strategy?.recommendations || []).map((r, i) => ({ recommendation: r, accept: i !== 2, reason: i !== 2 ? '타당함, 즉시 반영' : '다음 업무에서 CEO 지시로 처리' })),
    report: {
      headline: t.publish?.enabled ? `첫 쓰레드 게시물 준비 완료 — 브랜드 우선, 반응은 질문형으로 유도` : `${t.title} 완료 — 결론과 다음 행동 정리`,
      decisionNeeded: t.publish?.enabled ? '아래 게시 문구로 게시를 승인하시겠습니까? (발행 큐에서 승인)' : '다음 행동 3가지를 이대로 진행할지 승인해 주세요.',
      summary: ['CEO 지시는 실행하되 "반응 극대화"는 자극이 아닌 궁금증으로 달성', '1차 검수에서 반려 → 첫 문장·담당/마감 보강 후 통과', '24시간 후 조회·좋아요·리포스트·답글을 실측해 기준선으로 기록'],
      findings: [
        { title: '첫인상은 브랜드 우선', detail: 'SNS 운영 매니저 조팔로가 제기, 전원 동의. 첫 게시물이 조회수용 계정으로 인식되는 위험 회피.', evidence: '1차 토론' },
        { title: '반려 후 개선', detail: '첫 문장을 구체적 장면으로 교체, 다음 행동에 담당·마감 명시.', evidence: `검수 ${t.reviews?.length || 1}회` },
      ],
      risks: [{ risk: '초기 반응 저조', mitigation: '24시간 후 분석해 두 번째 게시물 방향 조정' }, { risk: '음원 저작권', mitigation: '김근거 체크리스트 통과 후에만 게시' }],
      nextActions: [
        { owner: '조팔로', action: '게시 후 첫 댓글 달기, 답글 대응', due: t.deadline },
        { owner: '전환율', action: '24시간 성과 측정 및 기록', due: '게시 +1일' },
        { owner: '조회수', action: '두 번째 게시물 후보 3개 제안', due: '게시 +2일' },
      ],
    },
    post: post ? { text: post } : null,
    memoryNote: `${t.title}: 첫인상은 브랜드 우선, 반응은 질문형 유도로 결정 (${c.name})`,
  };
}

module.exports = { triage, opinion, reactions, rebuttal, assign, execute, review, reworkAssign, strategy, final };
