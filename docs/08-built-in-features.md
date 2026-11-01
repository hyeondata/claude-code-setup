> 이 문서는 2026-11-01 조사·설치 기록입니다. 새 컴퓨터에서는 루트 README와 `scripts/bootstrap.py`를 우선 사용하세요. `$HOME`은 해당 컴퓨터의 홈 디렉터리이며, 당시 경로·검증 결과가 새 컴퓨터에 그대로 적용되는 것은 아닙니다.

# 추가 설치 전에 활용할 Claude Code 내장 기능

조사일: **2026-11-01**. 공식 문서에서 확인한 기능과 이 사용자 구성에 대한 추천을 구분했습니다. 명령·설정 예시는 참고용이며 실행하지 않았습니다. 기능 제공 여부는 설치 버전, 연결 공급자, 계정·조직 설정에 따라 달라질 수 있습니다.

## 먼저 볼 기능

| 우선순위 | 기능 | 지금 구성에 주는 이점 |
|---|---|---|
| 우선 | `/context`, `/memory`, `/mcp`, `/hooks` | 작성한 규칙과 기억 도구가 실제로 로드됐는지 확인 |
| 우선 | 경로별 `.claude/rules/` | 전역 지침에 프로젝트별 세부 규칙이 쌓이는 문제를 줄임 |
| 우선 | `/resume`와 세션 이름 | 이전 작업을 이어가는 일은 내장 기능으로 처리 |
| 선택 | 서브에이전트 persistent memory | 리뷰·디버깅 담당별로 반복해서 얻는 지식을 축적 |
| 선택 | 내장 `/goal` | 완료 조건이 명확한 반복 작업을 계속 진행 |
| 선택 | Worktree | 여러 작업의 파일 변경을 분리 |
| 필요해질 때 | Skills, 예약 실행, headless | 반복 절차를 실제 실행 흐름으로 묶음 |
| 고급 | Agent teams, Channels | 여러 세션 협업 또는 외부 이벤트 반응 |

위 순서는 추천 판단입니다. 플러그인을 더 설치하기 전에 현재 구성의 로드·검색·저장을 먼저 확인하는 편이 원인 파악과 운영이 쉽습니다.

## 1. 경로별 규칙과 공통 지침 분리

**유형:** 내장 지침 로딩. **추천:** 프로젝트별 규칙이 늘어날 때 우선.

- 공통 선호는 사용자 전역 `CLAUDE.md`, 코드 영역별 규칙은 프로젝트 `.claude/rules/`에 둡니다.
- `paths`가 있는 규칙은 해당 패턴의 파일을 다룰 때 로드됩니다. 없는 규칙은 시작할 때 항상 로드됩니다.
- `@` import는 문서 분리를 돕지만, 가져온 내용도 함께 로드되므로 그 자체가 컨텍스트 절감 기능은 아닙니다.

아래는 `.claude/rules/api.md`에 둘 수 있는 **설계 예시**입니다.

```markdown
---
paths:
  - "src/api/**/*.ts"
---

Keep API changes compatible with the documented request and response schema.
Run the existing API contract checks for endpoints changed in this task.
```

이 규칙도 모델이 따르는 지침입니다. 반드시 실행돼야 하는 검사는 테스트·CI·훅으로 별도 구현합니다.

출처: [경로별 규칙](https://code.claude.com/docs/en/memory#path-specific-rules), [파일 import](https://code.claude.com/docs/en/memory#import-additional-files).

## 2. Auto memory의 저장 범위 설정

**유형:** 내장 기억. **추천:** 현재 기본 구성을 유지하되 범위를 이해.

기본 Auto memory는 같은 저장소의 worktree끼리 공유하는 로컬 기억입니다. 사용자 전역 `CLAUDE.md`와 달리 모든 프로젝트에 자동으로 동일한 기억을 제공하는 것은 아닙니다. `autoMemoryDirectory`로 저장 위치를 바꿀 수도 있습니다.

현재 구성에서는 Auto memory 디렉터리와 `$HOME/claude/obsidian`을 분리하는 것을 권합니다. 같은 폴더로 바꾼다고 Auto memory와 claude-obsidian의 색인·트랜잭션 형식이 통합되는 것은 아닙니다. 이 분리 권고는 두 저장 방식을 함께 운영하기 위한 설계 판단입니다.

출처: [Auto memory 저장 위치](https://code.claude.com/docs/en/memory#storage-location).

## 3. 서브에이전트별 persistent memory

**유형:** 내장 에이전트 설정. **추천:** 같은 역할을 반복 호출할 때 선택.

예를 들어 리뷰 담당이 프로젝트의 반복 실수를 기억하게 할 수 있습니다. 에이전트 정의에 `memory`를 지정하고, 무엇을 기록·참고할지 본문에 명시합니다.

| 범위 | 저장 위치 | 적합한 경우 |
|---|---|---|
| `user` | `~/.claude/agent-memory/<name>/` | 프로젝트를 넘어 같은 역할에 적용할 지식 |
| `project` | `.claude/agent-memory/<name>/` | 저장소에서 공유할 역할별 지식 |
| `local` | `.claude/agent-memory-local/<name>/` | 해당 프로젝트에서 본인만 사용할 지식 |

일반 서브에이전트는 메인 대화의 Auto memory를 그대로 받지 않습니다. 자신의 `memory` 설정이 필요하며, Auto memory를 비활성화한 경우 이 설정도 효력이 없습니다. 에이전트를 여러 개 쓰면 모델 사용량도 추가됩니다.

현재 사용자의 개인 개발 환경에는 `local`부터 검토하고, 팀 공유가 필요하면 `project`를 선택하는 것을 권합니다. 사람도 읽을 공통 지식은 계속 Obsidian에 정리합니다.

출처: [서브에이전트 기억](https://code.claude.com/docs/en/sub-agents#enable-persistent-memory), [시작 시 받는 컨텍스트](https://code.claude.com/docs/en/sub-agents#what-loads-at-startup).

## 4. `/resume`와 세션 이름

**유형:** 내장 대화 관리. **추천:** 기본 사용법으로 익히기.

```text
/resume
```

터미널에서는 `claude --continue`로 최근 세션을, `claude --resume`으로 세션 선택기를 엽니다. 선택기에서 이름 검색·미리보기·프로젝트 범위 확장을 할 수 있습니다. 작업에 이름을 붙이면 나중에 이어가기 편합니다.

“어제 하던 작업을 그대로 계속”에는 이 기능이 먼저입니다. “여러 대화에서 비슷한 문제와 결정을 찾아 현재 작업에 참고”에는 episodic-memory가 추가 가치를 줍니다. 세션 재개가 장기 보관·의미 검색·위키 작성을 모두 대신한다고 보지는 않습니다.

출처: [세션 관리](https://code.claude.com/docs/en/sessions).

## 5. 긴 작업 절차는 Skill로 분리

**유형:** 내장 확장 방식. **추천:** 반복 절차가 길어질 때 선택.

전역 `CLAUDE.md`에는 실행 조건을 짧게 남기고, 여러 단계의 절차는 스킬로 분리할 수 있습니다. 스킬 본문은 호출할 때 로드됩니다.

자동 호출이 목적이라면 스킬의 설명뿐 아니라 호출 설정도 확인해야 합니다. `disable-model-invocation: true`는 모델의 자율 호출을 제한하므로 `CLAUDE.md`의 한 줄 지시와 같은 종류의 설정이 아닙니다. 반대로 `user-invocable: false`는 사용자 메뉴에서 숨기는 설정이며 모델 호출 차단용이 아닙니다.

내장 `/run`, `/verify`, `/run-skill-generator`도 확인할 가치가 있습니다. 앱 실행·실제 동작 검증과 프로젝트별 실행 절차 기록에 쓰입니다. 현재 내장 `/verify`는 사용자가 직접 호출하는 기능이므로 “완료 시 자동으로 실행” 지침만으로 자동 호출된다고 가정하지 않습니다.

현재 51줄의 전역 기억 지침은 바로 더 쪼갤 필요가 크지 않습니다. 위키 저장 절차가 길어지거나 별도 검증을 반복할 때 스킬 분리를 검토하면 됩니다.

출처: [Skills와 내장 검증 기능](https://code.claude.com/docs/en/skills), [호출 주체 제어](https://code.claude.com/docs/en/skills#control-who-invokes-a-skill).

## 6. 설정 진단 명령

**유형:** 내장 진단. **추천:** 현재 구성에서 가장 먼저.

| 명령 | 확인할 내용 |
|---|---|
| `/context` | 전역·프로젝트 지침, 기억 파일, 도구가 현재 컨텍스트에 로드됐는가 |
| `/memory` | Auto memory 상태와 기억 파일 위치 |
| `/mcp` | 서버 연결과 노출된 도구 |
| `/hooks` | 등록된 훅과 이벤트 |
| `/skills` | 사용 가능한 스킬 |
| `/status` | 활성 설정의 출처 |
| `claude doctor` | 터미널에서 실행하는 읽기 전용 설치·설정 진단 |

Claude Code 안의 `/doctor`는 진단 후 수정안을 제시할 수 있는 점검 흐름입니다. 터미널의 `claude doctor`와 같은 실행 형태로 취급하지 않습니다.

현재 사용자는 전역 지침 파일이 있는지만 확인한 상태이므로, 새 실제 세션에서 `/context` → `/memory` → `/mcp` 순서로 확인하는 것이 좋습니다. 파일 검증과 모델 세션에서의 기능 검증은 별개입니다.

출처: [설정 진단](https://code.claude.com/docs/en/debug-your-config).

## 7. MCP Tool search

**유형:** 내장 도구 정의 지연 로딩. **추천:** 기본 동작을 먼저 활용.

현행 문서에서 Tool search는 지원 환경에서 기본 활성화입니다. MCP 도구 정의를 필요할 때 불러오므로 “MCP를 추가하면 모든 도구 설명이 항상 시작부터 로드된다”는 설명은 현재 기본 동작과 맞지 않습니다.

`ENABLE_TOOL_SEARCH=auto`를 명시한 경우에는 10% 임계값 방식입니다. 이를 현재 미설정 상태의 기본값과 혼동하지 않습니다. 모델·공급자·조직 설정에 따라 지연 로딩이 지원되지 않는 예외도 있습니다.

이 기능은 도구 **정의**의 컨텍스트 비용을 줄입니다. 거대한 검색 결과·테스트 로그·소스 코드 출력까지 자동으로 필요한 부분만 골라주는 것은 아닙니다. RTK나 코드 색인을 비교할 때 두 비용을 구분해야 합니다.

출처: [MCP Tool search](https://code.claude.com/docs/en/mcp#scale-with-mcp-tool-search), [설정과 기본값](https://code.claude.com/docs/en/mcp#configure-tool-search).

## 8. Worktree로 병렬 수정 분리

**유형:** 내장 Git 작업 공간 관리. **추천:** 동시에 둘 이상의 작업을 할 때.

터미널 사용 예시:

```bash
claude --worktree login-fix
```

각 세션이 독립된 파일 사본과 브랜치에서 작업합니다. 같은 파일을 두 세션이 동시에 바꾸는 충돌을 줄이는 데 유용합니다. 새 checkout이므로 의존성·실행 환경 준비는 따로 필요할 수 있습니다.

Worktree는 코드 파일을 나누는 기능입니다. 공통 원격 서비스나 사용자가 지정한 하나의 Obsidian 보관함까지 각각 독립시키지는 않습니다. 위키를 동시에 저장할 때에는 저장 도구의 충돌 감지·트랜잭션 절차를 유지해야 합니다.

출처: [Worktree](https://code.claude.com/docs/en/worktrees).

## 9. Checkpoint와 `/rewind`

**유형:** 내장 대화·파일 복원. **추천:** 실험적 변경과 긴 디버깅에서 선택.

`/rewind`로 코드, 대화, 또는 둘 모두를 이전 지점으로 되돌릴 수 있습니다. 대화 일부만 요약하는 선택지도 제공합니다.

모든 외부 작업을 되돌리는 백업 기능은 아닙니다. Bash만으로 변경한 파일, 일부 서브에이전트 변경 등에는 추적·복원 한계가 있습니다. MCP를 통해 다른 서비스에 쓴 데이터나 위키 트랜잭션까지 일괄 취소된다고 가정하지 않습니다. Git과 저장 도구의 복구 절차가 계속 필요합니다.

출처: [Checkpointing과 복원 한계](https://code.claude.com/docs/en/checkpointing).

## 10. 내장 `/goal`: 완료 조건까지 계속 작업

**유형:** 내장 세션 자동 진행. **추천:** 반복 플러그인보다 먼저 검토.

예시:

```text
/goal Finish the scoped API migration and show the relevant tests passing; leave unrelated modules unchanged.
```

매 턴 이후 별도 모델이 대화에 드러난 결과로 완료 여부를 판단하고, 미완료면 다음 턴을 진행합니다. 평가자가 독립적으로 테스트를 실행하는 것은 아닙니다. 모델 판단이므로 완료 판정의 정확성은 검증 결과와 조건의 명확성에 달려 있습니다.

Ralph 계열의 반복 흐름이 필요하다고 느낄 때 먼저 내장 `/goal`을 확인할 가치가 있습니다. 정해진 시간마다 확인하는 `/loop`, 이벤트에 반응하는 훅과도 목적이 다릅니다. 중지에는 `/goal clear`를 사용합니다. 지속 실행은 사용량을 늘릴 수 있습니다.

출처: [Goal](https://code.claude.com/docs/en/goal).

## 11. 예약 실행: `/loop`, Desktop, Cloud

**유형:** 내장 스케줄링. **추천:** 정기 작업이 실제로 있을 때.

| 방식 | 적합한 일 | 로컬 파일 | 실행 조건 |
|---|---|---|---|
| `/loop` | 현재 작업의 CI·빌드 상태 확인 | 현재 세션에서 접근 | 세션이 실행 중이어야 함 |
| Desktop local task | 매일 로컬 보관함 점검·프로젝트 확인 | 접근 가능 | 앱이 열려 있고 컴퓨터가 깨어 있어야 함 |
| Cloud scheduled task | 저장소 이벤트·정기 클라우드 작업 | 개인 Mac의 파일에 직접 접근하지 않음 | 클라우드 설정·연결 필요, 로컬 PC가 꺼져도 실행 |

현재 로컬 Obsidian 보관함을 대상으로 한 정기 점검은 Desktop 방식이 더 직접적입니다. 이것은 추천 설계이며, 예약 작업을 만들지 않았습니다. 매 작업 완료 후 저장하는 `CLAUDE.md` 규칙과 정기 점검은 서로 다른 실행 계기입니다.

현재 `/loop` 예약은 재개 시 복원되는 경우도 있으므로 “프로세스를 닫으면 무조건 영구 삭제”라고 단정하지 않습니다. 그래도 종료된 세션이 백그라운드 서비스처럼 계속 작업하는 것은 아닙니다. Cloud scheduled tasks는 조사 시점 research preview입니다.

출처: [세션 스케줄링](https://code.claude.com/docs/en/scheduled-tasks), [Desktop 예약](https://code.claude.com/docs/en/desktop-scheduled-tasks), [Cloud 예약](https://code.claude.com/docs/en/routines).

## 12. Headless CLI와 Agent SDK

**유형:** CLI·SDK 자동화. **추천:** 별도 수집기·검증 파이프라인이 필요해질 때.

`claude -p`는 비대화형 실행의 출발점입니다. 스크립트에서 결과·종료 상태를 받고 후속 처리를 할 수 있습니다. SDK는 프로그램에서 에이전트 실행을 더 세밀하게 제어하는 데 쓰입니다.

특히 `--bare`는 지침·훅·플러그인·MCP·기억의 자동 발견을 생략합니다. 지금 작성한 전역 `CLAUDE.md`가 모든 자동 실행에서 항상 적용된다고 가정하면 안 됩니다. 명시적으로 필요한 설정과 맥락을 전달해야 합니다. 현재 bare 모드에서는 구독 로그인 대신 API·공급자 인증을 고려해야 하는 점도 있습니다.

현재 목적에는 별도 SDK 프로그램을 먼저 만들 필요가 없습니다. 기존 스킬의 정상 저장 흐름으로 요구를 충족하지 못할 때 검토합니다.

출처: [비대화형 실행과 bare mode](https://code.claude.com/docs/en/headless).

## 13. Agent teams와 Channels: 고급 확장

| 기능 | 쓰는 상황 | 추가 조건 | 현재 추천 |
|---|---|---|---|
| Agent teams | 서로 다른 역할이 의견을 주고받는 큰 조사·구현 | 실험 기능 활성화, 세션·사용량 관리 | 단일 세션·서브에이전트로 부족할 때 |
| Channels | CI·외부 서비스 이벤트를 열린 세션으로 전달 | 지원 인증 방식, 채널 플러그인·자격증명, 실행 중인 세션 | 이벤트 기반 운영이 필요할 때 |

Agent teams는 조사 시점 기본 비활성화인 실험 기능이며, 세션 복원·조율 관련 한계가 있습니다. 팀별 모델 요청과 조정 비용도 고려해야 합니다.

Channels는 일반적인 요청형 MCP와 달리 이벤트를 세션으로 밀어 넣는 통로입니다. 자동 기억을 위한 필수 구성은 아니며, 열린 세션에서 반응한다는 실행 조건이 있습니다. 이 문서 작성 중 외부 채널을 연결하거나 메시지를 보내지 않았습니다.

출처: [Agent teams](https://code.claude.com/docs/en/agent-teams), [Channels](https://code.claude.com/docs/en/channels).

## 현재 구성에 대한 도입 순서

1. 전역 지침 로드, Auto memory 활성화, 두 기억 플러그인 도구 노출을 실제 세션에서 확인합니다.
2. 작은 작업 하나를 저장하고 다음 작업에서 다시 검색해 기본 흐름을 검증합니다.
3. 프로젝트별 규칙이 늘어나면 `.claude/rules/`, 반복 전문 역할이 생기면 subagent memory를 추가합니다.
4. 완료 조건 기반 반복 작업에는 `/goal`, 시간 기반 점검에는 알맞은 스케줄링을 선택합니다.
5. 팀·SDK·Channels는 구체적인 운영 필요가 생겼을 때 도입합니다.

이 순서는 현재 사용자의 목적을 기준으로 한 추천이며 모든 기능을 활성화하라는 의미가 아닙니다.

---

[전체 목차](00-index.md)
