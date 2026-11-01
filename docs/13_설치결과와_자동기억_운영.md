> 이 문서는 2026-11-01 조사·설치 기록입니다. 새 컴퓨터에서는 루트 README와 `scripts/bootstrap.py`를 우선 사용하세요. `$HOME`은 해당 컴퓨터의 홈 디렉터리이며, 당시 경로·검증 결과가 새 컴퓨터에 그대로 적용되는 것은 아닙니다.

# 설치 결과와 자동 기억 운영

설치·확인 기준: **2026-11-01**.
Claude Code의 기본 기억, 과거 대화 검색, Obsidian 선별 저장을 연결했습니다.
이 문서는 실제 설정을 설명합니다. **실제 Claude 세션의 자동 저장과 후속 검색까지 검증했습니다.**

## 1. 무엇을 설치하고 연결했는가

| 구성 | 현재 상태 | 역할 |
|---|---|---|
| Claude Code | 2.1.316 | 실행 환경 |
| 내장 Auto memory | `autoMemoryEnabled: true` | 프로젝트별 선호·피드백·지속 맥락 |
| episodic-memory | 1.6.0, user scope 설치; MCP 연결 확인 | 과거 Claude 대화 보관·검색 |
| claude-obsidian | 3.0.1, user scope 설치 | 선별한 지식을 Markdown 위키로 관리 |
| Obsidian vault | `$HOME/claude/obsidian`, 초기화 완료 | 읽고 관리할 장기 지식 |
| 사용자 자동화 훅 | 시작·입력·응답 종료·세션 종료에 추가 | 로컬 검색·대화 동기화·선별 저장 요청 |
| 기존 Orca 훅 | 보존 | 기존 운영 유지 |
| Serena | 기존 MCP 연결 확인 | 프로젝트 코드 탐색·편집 지원 |
| Context7 | 설치·활성화됨, 인증 필요 | 라이브러리 문서 검색; 로그인은 사용자 요청에 따라 나중에 |
| 공식 Dart/Flutter | `dart-flutter@dart-flutter` 1.0.7 설치, MCP 연결 확인 | 기존 Flutter SDK로 탐색·진단·개발 스킬 제공 |

Serena 연결은 각 프로젝트·언어에서의 모든 기능 검증을 뜻하지 않습니다.
주언어 응답이 없어 실제 확인한 Flutter 프로젝트를 기준으로 공식 Flutter 팀 플러그인을 설치했습니다. 이는 native LSP 플러그인이 아니라 Dart MCP의 `lsp`·진단 도구와 스킬 묶음입니다. 기존 SDK `$FLUTTER_SDK`의 `bin`을 Claude 실행 PATH에 연결했습니다. SDK를 이동·삭제하면 이 경로도 수정해야 합니다. [공식 플러그인](https://github.com/flutter/agent-plugins)

## 2. 기억은 세 곳에 나뉜다

| 기억 종류 | 저장 내용 | 위치·범위 |
|---|---|---|
| 내장 기억 | 선호·교정·지속해서 필요한 맥락 | 기본적으로 `~/.claude/projects/<project>/memory/` |
| 대화 보관·검색 | 실제 Claude 대화 기록과 검색 인덱스 | episodic-memory의 로컬 archive·인덱스 |
| Obsidian 지식 | 완료·검증된 결정, 해결책, 재사용 절차, 출처 있는 조사 | 선택한 vault의 위키 |

초기 동기화는 **Claude 대화만 대상으로 9개 기록**을 처리했습니다.
후속 검증 세션까지 자동 동기화한 최종 점검에서는 **12개 대화·436개 교환**이 색인되어 있었습니다. 숫자는 이후 대화로 늘어납니다. 다른 에이전트의 이력은 이번 수집 범위에 넣지 않았습니다.
episodic-memory의 로컬 보관 기록에는 실제 원래 Claude 대화가 포함됩니다.
반면 위키에는 대화 전문을 복사하지 않고, 오래 쓸 가치가 있는 결과만 골라 남깁니다.

내장 Auto memory는 프로젝트별 기억입니다. 모든 프로젝트·기기의 지식을 하나로 합치거나 Obsidian에 동기화하는 기능은 아닙니다.
`/memory`에서 상태와 파일을 확인할 수 있습니다. [내장 기억 공식 문서](https://code.claude.com/docs/en/memory)

## 3. 다음 Claude 세션에서 일어나는 일

| 시점 | 이번 구성의 동작 |
|---|---|
| 세션 시작 `SessionStart` | Claude 대화 증분 동기화를 요청하고, Obsidian의 최근 핵심 맥락을 제한된 분량으로 읽음 |
| 질문 입력 `UserPromptSubmit` | 입력과 관련된 과거 대화·위키를 로컬에서 검색해 필요한 일부를 맥락으로 전달 |
| 응답 종료 `Stop` | 대화 동기화를 요청하고, 저장할 새 지식이 있는지 현재 Claude에게 한 번 점검하도록 안내 |
| 세션 종료 `SessionEnd` | 대화 증분 동기화를 요청 |

저장 후보 판단은 현재 대화를 처리한 Claude가 합니다. 별도 Claude 프로세스를 반복 실행해 요약하는 방식은 쓰지 않습니다.
Stop에서는 같은 저장 점검이 반복되는 것을 막으며, 저장할 내용이 없거나 이미 저장했다면 추가 노트 없이 끝냅니다.
가치 있는 내용이 있어도 검증 실패를 무시하고 저장하지 않습니다.
훅은 운영체제의 상시 데몬이 아니며, 강제 종료·프로세스 중단 뒤 작업 완료를 보장하지 않습니다.
백그라운드 동기화가 이미 진행 중이면 다음 이벤트에서 후속 변경이 반영될 수 있습니다.

위키의 시작 맥락은 `CLAUDE_OBSIDIAN_SESSION_CONTEXT=1`로 켠 선택 기능입니다.
이 기능 자체는 지식을 쓰지 않습니다. 위키 저장은 아래의 별도 검증 절차를 거칩니다.
[Claude 훅 공식 문서](https://code.claude.com/docs/en/hooks), [claude-obsidian 훅 설명](https://github.com/AgriciDaniel/claude-obsidian/blob/main/hooks/README.md)

## 4. 무엇을 자동으로 남기는가

대상은 새롭고 지속 가치가 있는 **완료·검증된 결정, 확인된 해결책, 재사용할 절차, 출처가 있는 조사 결과**입니다.
일상적인 답변, 미완료 작업, 기존 노트와 같은 내용, 자격 증명, 관련 없는 자료, 대화 전문은 위키 저장에서 제외합니다.
현재 대화에서 저장하지 말라는 요청이 있으면 이를 우선합니다.
기존 결론을 실질적으로 바꾸거나 노트를 삭제하는 권한까지 자동 저장에 포함하지 않습니다.

저장용 어댑터의 흐름은 다음과 같습니다.

1. `snapshot`으로 현재 노트·인덱스 상태를 확인합니다.
2. `prepare`로 새 노트나 작은 추가 내용을 트랜잭션 초안으로 준비합니다.
3. `inspect`로 목적지·변경 내용·저장 형식·작업 완결성을 검사합니다.
4. 검사한 내용과 정확한 승인 해시를 사용해 `apply`합니다.
5. 저장 영수증을 확인하고 `reindex` 후 `search`로 다시 찾을 수 있는지 확인합니다.

이는 허용된 저장 작업을 좁게 연결한 도구입니다. 임의 스크립트를 실행하거나 실패한 검증을 우회하는 허가는 아닙니다.
원본 위키를 일반 파일 쓰기로 직접 덮어쓰지 않으며, 노트·인덱스·로그·핵심 맥락을 함께 다룹니다.
검사 뒤 다른 변경이 생겨 적용할 수 없으면 최신 상태를 다시 읽고 검사합니다.
저장 성공은 실제 영수증·operation ID가 나온 경우에만 보고합니다.
[claude-obsidian 프로젝트·저장 흐름](https://github.com/AgriciDaniel/claude-obsidian)

## 5. 파일과 검색 운영

자동화 파일은 `$HOME/claude/automation/`에 있습니다.

| 파일 | 역할 |
|---|---|
| `memory_hooks.py` | Claude 이벤트별 대화 동기화·검색·저장 점검 연결 |
| `memory_cli.py` | 선택한 vault와 현재 설치된 플러그인에 맞춘 저장·검색 어댑터 |
| `episodic_search.mjs` | 과거 대화의 로컬 검색 |
| `config.json` | vault·실행 환경 위치 |
| `AUTOMATION.md` | 검색·선별 저장의 운영 규칙 |

수동 조회가 필요하면 다음처럼 사용할 수 있습니다.

```sh
python3 $HOME/claude/automation/memory_cli.py paths
python3 $HOME/claude/automation/memory_cli.py search "검색할 주제"
```

환경에서 오래된 Python이 먼저 선택되는 문제가 발견되어, 기존 Python 3.11 경로가 우선되도록 Claude 설정의 PATH를 조정했습니다.
새 Python을 설치한 것은 아닙니다. 이미 열려 있는 Claude 세션은 새 세션에서 설정 적용을 확인하는 편이 확실합니다.

검색 결과가 없다고 기억 자체가 없는 것은 아닙니다.
영어 중심 임베딩을 사용하므로 한국어 질의만으로 회수가 부족하면 짧은 영어 기술 용어·정확한 파일명도 시도합니다.
한국어와 영어 검색 품질이 같다고 보장하지 않습니다.
검색·임베딩·보관은 로컬에서 처리하지만, 선택된 검색 결과는 Claude의 대화 맥락으로 전달됩니다.
[episodic-memory 검색·저장 구조](https://github.com/obra/episodic-memory)

## 6. 중복 동기화와 요약 호출을 어떻게 줄였는가

- `EPISODIC_MEMORY_DISABLE_AUTO_SYNC=1`: 플러그인 자체의 시작 동기화를 끕니다.
- 사용자 훅이 실행하는 자식 동기화 프로세스에서만 위 값을 `0`으로 바꾸고 `--only claude`로 범위를 제한합니다.
- `EPISODIC_MEMORY_SKIP_SUMMARIES=1`: 별도 모델 요약 생성을 생략합니다. 대화 보관·임베딩·검색을 끄는 설정은 아닙니다.

이 구성은 같은 시작 이벤트에 중복 동기화 작업이 생기는 것을 줄이기 위한 것입니다.
현재 Claude가 검색 결과를 읽거나 선별 지식을 작성하는 작업은 Claude 사용량에 포함될 수 있습니다.

## 7. 중지·복구·미완료 항목

이번에 추가한 사용자 훅을 임시 중지하려면 다음 환경변수로 Claude를 시작합니다.

```sh
CLAUDE_MEMORY_AUTOMATION_DISABLED=1 claude
```

이는 사용자 훅의 동기화·질문 시 검색·Stop 저장 점검을 중지하며 기존 기록을 삭제하지 않습니다.
내장 Auto memory, claude-obsidian의 시작 hot context, 수동 검색·저장은 별도입니다.
따라서 모든 기억 기능을 끄는 단일 스위치로 해석하면 안 됩니다.

설정 변경 전 백업: `$HOME/claude/setup-backups/20261101-185108`.
백업의 설정으로 되돌리면 해당 설정 변경을 복구할 수 있지만, 설치한 플러그인·생성된 기록·위키가 자동 삭제되지는 않습니다.
설치 이후 다른 설정을 추가했다면 파일 전체를 덮어쓰기보다 변경 내용을 비교해 복구합니다.

Context7 로그인은 사용자 요청에 따라 남겨두었습니다. 준비됐을 때 실행합니다.

```sh
claude mcp login plugin:context7:context7
```

또는 새 Claude 세션의 `/mcp`에서 Context7을 선택해 로그인합니다.
현재는 인증 필요 상태이며 문서 검색 성공을 확인한 상태가 아닙니다.
[Context7 공식 인증 안내](https://context7.com/docs/clients/claude-code)

| 최종 확인 항목 | 상태 |
|---|---|
| 플러그인 설치·내장 기억·vault 초기화 | 완료 |
| episodic-memory·Serena MCP 연결 | 확인 |
| 초기 Claude 대화 보관·로컬 검색 | 확인 |
| 기존 Orca 훅 보존 | 확인 |
| 실제 세션의 선별 저장 → 영수증 → 재검색 | **완료: 원칙 노트 1개와 index/log/hot를 함께 저장** |
| Context7 OAuth | 사용자 요청으로 나중에 |
| 공식 Dart/Flutter MCP | 설치·기존 SDK 연결 완료; native LSP는 별도 설치하지 않음 |


최종 질문 훅은 한국어 질의 `개발 기억 3계층 운영 원칙`으로 위키와 대화를 함께 회수했습니다. 검색 전후 노트 해시는 같았고, 보관함 lint는 **오류 0건**이었습니다. 훅의 경로·반복 방지·입력 제한 등 15개 테스트와 어댑터의 snapshot/prepare·경로 제한 검사를 통과했습니다.

macOS Finder가 `.vault-meta/transactions/.DS_Store`를 만들면 현재 플러그인이 런타임 상태 오류로 저장을 거부할 수 있습니다. 이번 점검에서 생긴 Finder 메타데이터는 백업 폴더의 `finder-metadata/`로 옮겨 해결했습니다. 같은 오류가 재발하면 오류에 명시된 Finder 메타데이터만 백업 이동하고 재시도하며, 실제 transaction 파일은 삭제하지 않습니다.
