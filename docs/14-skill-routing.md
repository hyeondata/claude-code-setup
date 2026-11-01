> 이 문서는 2026-11-01 조사·설치 기록입니다. 새 컴퓨터에서는 루트 README와 `scripts/bootstrap.py`를 우선 사용하세요. `$HOME`은 해당 컴퓨터의 홈 디렉터리이며, 당시 경로·검증 결과가 새 컴퓨터에 그대로 적용되는 것은 아닙니다.

# Matt·pstack 설치 결과와 개발 스킬 역할 분담

확인일: 2026-11-01 · 대상: 이 Mac의 **Claude Code 사용자 범위**

설치와 전역 지침 적용을 완료했습니다. **Superpowers를 기본 개발 절차로 유지하고, Matt의 호출 가능한 전문 스킬을 필요한 단계에만 추가합니다. pstack의 심층 검증은 원본의 직접 호출 제한 때문에 명령 실행 방식으로 남겼습니다.** 모든 플러그인이 훅처럼 자동 실행되는 구성은 아닙니다.

## 설치된 구성

| 구성 | 설치 버전 | 설치 경로/출처 | 역할 |
|---|---|---|---|
| Superpowers | 7.0.0, 기존 유지 | `superpowers@claude-plugins-official` | 계획·구현·디버깅·TDD·검증·일반 리뷰 |
| Matt Pocock | 1.3.1, 새 설치 | `mattpocock-skills@claude-plugins-official` | 도메인 모델·모듈 경계·에이전트 문서 |
| pstack | 0.15.36, 새 설치 | `pstack@cursor-plugins` | 변경 영향 분석·중요 변경의 심층 리뷰 |

Matt은 공식 마켓플레이스가 지정한 커밋 `49dd158d1076134a641b33efb035946536778336`을 설치했습니다. 저장소 main의 버전과 다를 수 있습니다. pstack은 Cursor 전용 폴더가 아닌 제작자의 `harness/pstack/claude-code` 패키지를 설치했으며 커밋은 `ae5650febf4320793844c12c4adaa937f417f8da`입니다.

Matt 플러그인은 등록 스킬 27개를 묶어서 설치합니다. 추천 스킬만 별도로 복사하지 않았습니다. pstack은 스킬 58개와 에이전트 2개를 제공합니다. 두 플러그인 자체에는 훅과 MCP 서버가 없습니다. [Matt 저장소](https://github.com/mattpocock/skills), [pstack Claude Code 어댑터](https://github.com/cursor/plugins/blob/main/pstack/docs/harness/claude-code.md)

## 실제 선택 규칙

| 작업 | 기본 선택 | 실행 방식 |
|---|---|---|
| 일반 기능 구현·계획·TDD·버그 진단·일반 리뷰 | Superpowers의 관련 단계 | 요청에 맞게 자동 선택 |
| 용어 혼용, 업무 개념, 용어집, 중요한 설계 결정·ADR | `mattpocock-skills:domain-modeling` | 자동 선택 가능 |
| 모듈 인터페이스, 결합도, 테스트 경계 설계 | `mattpocock-skills:codebase-design` | 자동 선택 가능 |
| CLAUDE.md·AGENTS.md 등의 실질적인 개선 | `mattpocock-skills:writing-for-agents` | 필요할 때 자동 선택 가능 |
| API·직렬화·DB·의존성·실행 순서의 호환성 위험 | `pstack:blast-radius` | 적절한 시점에 명령 안내, 직접 호출 필요 |
| 중요한 diff의 적대적 검증·심층 리뷰 | `pstack:interrogate` | 직접 호출 필요 |
| 저장소 전체의 구조 개선 후보 분석 | `mattpocock-skills:improve-codebase-architecture` | 직접 호출 필요 |
| 심화 인터뷰와 도메인 문서화를 함께 진행 | `mattpocock-skills:grill-with-docs` | 직접 호출 필요 |

한 작업에는 주도하는 절차를 하나만 둡니다. Matt의 지원 단계가 끝나면 진행 중인 절차로 돌아갑니다. 동일한 계획·질문·테스트·리뷰를 Superpowers와 Matt에서 반복하지 않습니다. 간단한 설명·기계적 수정에는 전체 개발 절차를 시작하지 않습니다.

Matt의 `tdd`, `diagnosing-bugs`, `code-review` 등은 설치되어 있지만 기본 경로에서 제외했습니다. 사용자가 선택하면 해당 Superpowers 단계를 대체합니다. `poteto-mode`, `setup-pstack`, `automate-me`, `recall`, Matt의 프로젝트 setup도 자동 시작하지 않습니다. 외부 이슈·PR·메시지 게시, 커밋·배포는 해당 작업에 대한 별도 권한 범위를 따릅니다.

## 자동 사용의 정확한 범위

설치 실물에서 pstack의 58개 스킬 중 57개가 `disable-model-invocation: true`이며, 예외는 설정용 `setup-pstack`입니다. Matt의 등록 스킬 27개 중 11개는 모델 호출이 가능하지만, 추천한 심화 명령 두 개는 직접 호출 전용입니다.

이 제한은 `CLAUDE.md`만으로 해제되지 않으며, 현재 `skillOverrides`도 플러그인 스킬에는 적용되지 않습니다. 따라서 동작하지 않는 override 설정이나 캐시 수정은 추가하지 않았습니다. 호출이 제한된 절차를 파일 읽기로 재현하거나 자식 Claude 세션으로 우회하지 않도록 명시했습니다. [Claude Code 스킬 호출 제어](https://code.claude.com/docs/en/skills#control-who-invokes-a-skill), [skillOverrides 적용 범위](https://code.claude.com/docs/en/skills#override-skill-visibility-from-settings)

심층 도구를 실행할 때는 **현재 메시지에** 다음 중 필요한 명령과 대상을 적습니다.

```text
/pstack:blast-radius 현재 변경의 API 호환성과 DB 마이그레이션 영향을 검증해줘
/pstack:interrogate 현재 브랜치 변경을 리뷰해줘. 수정은 하지 마
/mattpocock-skills:improve-codebase-architecture 이 저장소의 구조 개선 후보를 분석해줘
/mattpocock-skills:grill-with-docs 이 기능의 도메인과 설계 결정을 정리해줘
```

`CLAUDE.md`의 자동 선택은 모델의 판단을 유도하는 지침입니다. 모든 요청에서 정확히 같은 선택을 강제하는 이벤트 훅이나 플러그인별 비활성화 설정은 아닙니다. 실제 프로젝트 지침과 사용자 요청도 선택에 영향을 줍니다.

## 적용 파일과 기존 구성

- 실제 전역 지침: `$HOME/.claude/CLAUDE.md`
- 사용자 정리 폴더의 예시: `$HOME/claude/CLAUDE.example.md`
- 지침은 영어, 응답과 개인 지식 노트는 한국어 기본값을 유지했습니다.
- 기존 기억 지침은 문자열 그대로 유지했습니다. Auto memory, episodic-memory, Obsidian 저장·검색 훅, 환경변수, 권한 설정을 변경하지 않았습니다.
- Obsidian 보관함은 `$HOME/claude/obsidian`을 유지합니다.
- Context7 로그인은 사용자 요청대로 보류했습니다.
- 실제 프로젝트에 Matt setup을 실행하거나 용어집·ADR·이슈 트래커를 일괄 생성하지 않았습니다. 작업별 기존 문서 관례를 우선합니다.

이번 설정 JSON의 변경 항목은 플러그인 활성화 목록과 `cursor-plugins` 마켓플레이스 등록뿐입니다. 개발 스킬을 실행하는 추가 훅은 만들지 않았습니다.

## 검증

| 점검 | 결과 |
|---|---|
| 새 세션에서 두 신규 플러그인 인식 | 통과 |
| 도메인 용어·ADR 가상 요청 | `mattpocock-skills:domain-modeling`만 실제 로드 |
| 월말 날짜 버그 진단 가상 요청 | `superpowers:systematic-debugging`만 실제 로드 |
| API·DB 변경 영향 가상 요청 | 자동 호출 없이 `/pstack:blast-radius` 안내 |
| 기존 기억 지침·훅·환경·권한 보존 | 모두 일치 |
| 기존 플러그인 활성화 상태 보존 | 모두 일치 |

세 라우팅 세션 모두 오류·권한 거절 없이 끝났습니다. 기계 판독 결과는 `개발스킬_설치검증.json`에 있습니다.

네이티브 `claude plugin validate`는 두 패키지 모두 통과했습니다. 배포용 아이콘 누락과 Matt 패키지 루트 CLAUDE.md가 프로젝트 지침으로 로드되지 않는다는 경고 등이 있었습니다. 이는 이번 스킬 설치 실패를 뜻하지 않으며, 역할 분담은 실제 전역 CLAUDE.md에 별도로 적용했습니다.

테스트는 새 Claude 세션에서 가상 작업의 스킬 선택·로드까지만 확인했습니다. 테스트 세션에 한해 MCP·훅·기억 저장을 끄고 읽기/스킬 도구만 허용했습니다. 실제 구현·심층 리뷰의 품질, 모든 미래 요청의 자동 선택, 기존 기억 자동화의 재실행을 새로 검증한 것은 아닙니다. 기존 기억 기능의 실행 검증은 [13번 문서](13-installed-memory.md)에 있습니다.

## 적용 확인과 되돌리기

열려 있는 Claude Code에서는 새 세션을 시작하는 것이 가장 확실합니다. 플러그인만 갱신할 때는 `/reload-plugins`를 사용할 수 있습니다. 일반 작업은 평소처럼 요청하면 됩니다.

```sh
claude plugin list
claude plugin details mattpocock-skills@claude-plugins-official
claude plugin details pstack@cursor-plugins
```

변경 전 백업: `$HOME/claude/setup-backups/20261101-190458-engineering`. 기존 지침·설정·플러그인 등록부·마켓플레이스 등록부·README·예시 파일을 보관했습니다.

지침만 되돌릴 때는 이 백업의 `CLAUDE.md`를 실제 전역 파일로 복원합니다. 두 플러그인을 잠시 중지하려면 아래 명령을 사용합니다. 이후 설정 변경을 잃지 않도록 오래된 `settings.json` 전체를 무조건 덮어쓰지는 마세요.

```sh
claude plugin disable mattpocock-skills@claude-plugins-official
claude plugin disable pstack@cursor-plugins
```
