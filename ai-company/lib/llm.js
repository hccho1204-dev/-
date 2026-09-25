// AI 호출: 클로드(비서실장·직원), GPT(전략실장). 키가 없으면 체험 모드(가짜 응답).
const { company, agent, secrets } = require('./env');

function mode() {
  const s = secrets();
  return {
    claude: !!s.ANTHROPIC_API_KEY,
    gpt: !!s.OPENAI_API_KEY,
    demo: !s.ANTHROPIC_API_KEY,
  };
}

async function callClaude(model, system, prompt, maxTokens) {
  const key = secrets().ANTHROPIC_API_KEY;
  const r = await fetch('https://api.anthropic.com/v1/messages', {
    method: 'POST',
    headers: { 'content-type': 'application/json', 'x-api-key': key, 'anthropic-version': '2023-06-01' },
    body: JSON.stringify({ model, max_tokens: maxTokens, system, messages: [{ role: 'user', content: prompt }] }),
  });
  const j = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(`클로드 호출 실패(${r.status}): ${j.error?.message || '알 수 없는 오류'}`);
  const text = (j.content || []).filter((b) => b.type === 'text').map((b) => b.text).join('');
  return { text, usage: { in: j.usage?.input_tokens || 0, out: j.usage?.output_tokens || 0 }, model };
}

async function callGPT(model, system, prompt, maxTokens) {
  const key = secrets().OPENAI_API_KEY;
  const r = await fetch('https://api.openai.com/v1/chat/completions', {
    method: 'POST',
    headers: { 'content-type': 'application/json', authorization: `Bearer ${key}` },
    body: JSON.stringify({
      model,
      max_completion_tokens: maxTokens * 4, // GPT 추론 모델은 생각 토큰도 여기서 소모하므로 넉넉히
      messages: [{ role: 'system', content: system }, { role: 'user', content: prompt }],
    }),
  });
  const j = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(`GPT 호출 실패(${r.status}): ${j.error?.message || '알 수 없는 오류'}`);
  return { text: j.choices?.[0]?.message?.content || '', usage: { in: j.usage?.prompt_tokens || 0, out: j.usage?.completion_tokens || 0 }, model };
}

// 응답에서 JSON만 뽑아낸다
function parseJSON(text) {
  const s = String(text || '').replace(/```(?:json)?/g, '');
  const start = s.search(/[[{]/);
  if (start < 0) throw new Error('AI 응답에 JSON이 없습니다');
  const open = s[start], close = open === '{' ? '}' : ']';
  const end = s.lastIndexOf(close);
  return JSON.parse(s.slice(start, end + 1));
}

/**
 * ask({ task, agentId, system, prompt, json, maxTokens, mock })
 * - agentId 의 tier 에 맞는 모델로 호출
 * - 키가 없으면 mock() 결과를 돌려준다 (체험 모드)
 */
async function ask({ task, agentId, system, prompt, json = false, maxTokens = 1200, mock }) {
  const a = agent(agentId) || { tier: 'staff' };
  const models = company().models || {};
  const m = mode();
  let res;

  if (a.tier === 'strategist' && m.gpt) {
    res = await callGPT(models.strategist || 'gpt-5', system, prompt, maxTokens);
  } else if (m.claude) {
    const model = a.tier === 'chief' ? models.chief : models.staff;
    res = await callClaude(model || 'claude-sonnet-5', system, prompt, maxTokens);
  } else {
    await new Promise((r) => setTimeout(r, 350 + Math.random() * 500)); // 실제처럼 보이게 약간 대기
    const v = mock ? mock() : '';
    res = { text: typeof v === 'string' ? v : JSON.stringify(v), usage: { in: 0, out: 0 }, model: 'demo' };
  }

  if (task) {
    task.usage = task.usage || { calls: 0, in: 0, out: 0 };
    task.usage.calls += 1;
    task.usage.in += res.usage.in;
    task.usage.out += res.usage.out;
  }
  if (!json) return res.text.trim();
  try {
    return parseJSON(res.text);
  } catch (e) {
    if (!m.claude && !m.gpt) throw e;
    // 한 번만 다시 요청
    const retry = a.tier === 'strategist' && m.gpt
      ? await callGPT(models.strategist || 'gpt-5', system, prompt + '\n\n반드시 JSON만 출력하세요. 다른 말은 쓰지 마세요.', maxTokens)
      : await callClaude((a.tier === 'chief' ? models.chief : models.staff) || 'claude-sonnet-5', system, prompt + '\n\n반드시 JSON만 출력하세요. 다른 말은 쓰지 마세요.', maxTokens);
    return parseJSON(retry.text);
  }
}

module.exports = { ask, mode, parseJSON };
