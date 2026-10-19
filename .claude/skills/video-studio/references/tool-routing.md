# 도구 고르는 기준

## 한 장 요약

| 질문 | 예 → | 아니오 → |
|---|---|---|
| 1. 주제만 있고 대본·음성·음악·스톡까지 통째로 필요? | **OpenMontage** | 2번 |
| 2. 내가 찍은 촬영본이 있나? | 3번 | 4번 |
| 3. 촬영본을 컷 편집(무음·재촬영 제거)해야 하나? | `shortform-auto-edit` → 그 위 그래픽은 **HyperFrames** | **HyperFrames** (촬영본 위에 얹기) |
| 4. 처음부터 그리는 모션그래픽 (인트로·아웃트로·설명 애니메이션·키네틱 자막) | **Remotion** | — |

## 도구별 성격

| | Remotion | HyperFrames | OpenMontage |
|---|---|---|---|
| 한 줄 | 영상을 **React 코드**로 | 웹페이지(**HTML/CSS**)를 영상으로 | 주제 → 완성 영상 **공장** |
| 강점 | 프레임 단위 정밀 타이밍, 단어 하나하나 움직임, 데이터로 대량 생산(이름만 바꿔 100개) | 촬영본 위 자막·숫자 강조·도식·칩, 10초 안팎 도식, 효과음 라이브러리 | 조사·대본·나레이션·배경음악·자막·스톡·품질검사 자동 |
| 약점 | 처음 프로젝트 세팅이 필요 | 긴 영상 전체 구성엔 덜 맞음 | 내 스타일을 세밀하게 맞추려면 VIDEO_SPEC를 꼭 줘야 함 |
| 결과 | `npx remotion render` → mp4 | HyperFrames CLI 렌더 → mp4 | 파이프라인이 렌더까지 |
| 쓰는 곳 | 작업 폴더 안 리모션 프로젝트 | 작업 폴더 | OpenMontage 폴더 |

## 자주 하는 조합

| 만들 것 | 조합 |
|---|---|
| 유튜브 중간 챕터 인트로 / 구독·좋아요 아웃트로 | Remotion 단독 (3~6초, 시안 4개) |
| 말하는 숏폼 (촬영본 있음) | shortform-auto-edit → HyperFrames 그래픽 |
| 설명 영상 (촬영본 없음) | OpenMontage `Animated Explainer` 파이프라인 + VIDEO_SPEC 스타일 지시 |
| 다큐·감성 몽타주 | OpenMontage `Documentary Montage` |
| 긴 팟캐스트 → 숏폼 여러 개 | OpenMontage `Podcast Repurpose` 또는 `Clip Factory` |
| 같은 틀에 내용만 바꿔 대량 | Remotion (데이터 JSON만 갈아끼우기) |

## OpenMontage 파이프라인 (공식 README 기준)
Animated Explainer · Animation · Avatar Spokesperson · Cinematic · Clip Factory · Documentary Montage · Hybrid · Localization & Dub · Podcast Repurpose · Screen Demo · Talking Head (+ 캐릭터 애니메이션)

## 기대치
- 잘함: 글자·숫자·그래프·도형 움직임, 자막, 컷, 레이아웃, 효과음 타이밍
- 어려움: 사람·캐릭터의 자연스러운 동작(걷기·계단 오르기), 연기
- → **"편집" 관점**으로 쓴다. 사람이 움직이는 장면은 실사·영상 생성 AI 결과를 재료로 가져와 편집한다.
