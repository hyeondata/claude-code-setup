> 이 문서는 2026-11-01 조사·설치 기록입니다. 새 컴퓨터에서는 루트 README와 `scripts/bootstrap.py`를 우선 사용하세요. `$HOME`은 해당 컴퓨터의 홈 디렉터리이며, 당시 경로·검증 결과가 새 컴퓨터에 그대로 적용되는 것은 아닙니다.

# CLAUDE.md 적용 안내

작성일: 2026-11-01

## 적용 위치와 언어

- 실제 사용자 전역 지침: `$HOME/.claude/CLAUDE.md`
- 추천 문서 폴더의 참고 사본: `$HOME/claude/CLAUDE.example.md`
- 사용자가 선택한 Obsidian 보관함: `$HOME/claude/obsidian`
- 지침 본문은 영어, 사용자에게 하는 답변과 개인 지식 노트의 기본 언어는 한국어입니다.
- 참고 사본은 자동으로 불러오는 설정 파일이 아닙니다. 규칙을 바꾸려면 실제 전역 지침 파일을 수정합니다.

영어가 한국어보다 항상 더 좋은 성능을 낸다고 단정할 수는 없습니다. 이번에는 사용자의 선호에 따라 영어로 작성했고, 도구 이름·저장 조건·검색 시점을 구체적으로 명시했습니다. 공식 문서가 권장하는 핵심은 짧고 명확하며 서로 충돌하지 않는 지침입니다. [공식 작성 지침](https://code.claude.com/docs/en/memory#write-effective-instructions)

## 지정한 동작

| 구성 | 지침 |
|---|---|
| Auto memory | 지속적인 선호·피드백·코드에서 알 수 없는 프로젝트 맥락을 발견하면 선별 기록 |
| episodic-memory | 과거 결정·실패한 시도·이전 대화가 관련 있을 때 검색. 기본 동기화 훅은 중복하지 않음 |
| claude-obsidian | 검증한 작업을 완료하면 재사용할 결과만 선별해 지정 보관함에 저장 |
| 기록 검증 | 실제 저장 성공을 확인한 뒤 노트 경로 보고. 없는 도구를 사용했다고 주장하지 않음 |

이 지침에는 새 노트와 의미를 훼손하지 않는 작은 추가에 대한 지속적인 저장 요청이 포함되어 있습니다. 플러그인의 기본 수동 호출 지침만을 이유로 매번 다시 묻지 않게 했으며, 플러그인의 검증·트랜잭션 절차는 유지하게 했습니다. 실제 도구나 권한 경계가 저장을 막는 경우에는 그 정확한 요구 사항을 알리도록 했습니다.

## 현재 적용 상태

- Claude Code 2.1.316, Auto memory 명시적 활성화.
- episodic-memory 1.6.0, claude-obsidian 3.0.1 설치 및 위키 초기화 완료.
- 자동 검색·대화 동기화·선별 저장 점검 훅을 추가하고 기존 Orca 훅을 보존했습니다.
- 실제 Claude 세션에서 운영 원칙 노트를 저장하고 다시 검색했습니다.
- 공식 Dart/Flutter MCP도 기존 SDK로 연결했습니다. Context7 OAuth는 나중에 진행합니다.
- 전역 정책에 `$HOME/claude/automation/AUTOMATION.md`와 제한된 저장 어댑터 사용법을 연결했습니다.

구체적인 버전·경로·검증·중지 방법은 [13 설치 결과와 자동 기억 운영](13-installed-memory.md)을 참고하세요.

`CLAUDE.md`는 실행 정책을 모델에 전달합니다. 파일 생성만으로 Auto memory 설정을 켜거나 플러그인을 설치하거나 이벤트 훅을 만드는 것은 아닙니다. [기억과 설정의 차이](https://code.claude.com/docs/en/memory#claudemd-vs-auto-memory)

## Claude Code에서 확인하기

1. 터미널에서 새 Claude Code 세션을 시작합니다.
2. `/context`의 Memory files에서 전역 `CLAUDE.md`가 로드됐는지 확인합니다.
3. `/memory`에서 Auto memory 상태를 확인합니다.
4. `/mcp`에서 기억·Dart MCP 연결을 확인하고, 완료한 작업 뒤 저장된 노트 경로를 확인합니다.

[전역 지침 위치와 로딩 방식](https://code.claude.com/docs/en/memory#choose-where-to-put-claudemd-files)

---

[목차로 돌아가기](00-index.md)
