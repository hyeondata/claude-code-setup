> 이 문서는 2026-11-01 조사·설치 기록입니다. 새 컴퓨터에서는 루트 README와 `scripts/bootstrap.py`를 우선 사용하세요. `$HOME`은 해당 컴퓨터의 홈 디렉터리이며, 당시 경로·검증 결과가 새 컴퓨터에 그대로 적용되는 것은 아닙니다.

# Claude Code 기억과 지식관리 도구

기준일: **2026-11-01**. 공식 문서·공개 저장소와 일부 hook/skill 소스를 확인한 비교 문서다.
실제 설치, 설정 변경, 기능 실행 검증은 하지 않았다. 설치 명령은 별도 설치 안내에서 다룬다.
추천 우선순위는 개인 개발과 Obsidian 지식관리를 기준으로 한 판단이며, 기능의 절대적인 우열을 뜻하지 않는다.

## 1. 먼저 나눠야 할 세 가지 기억

추가 조사: [09 기억과 검색 추가 조사](09-memory-research.md)에 QMD·MCPVault·Local REST API와 클라우드 기억 대체안 등 8종을 추가했습니다. 현재 조합을 유지하면서 무엇을 더할지와 무엇을 대체할지를 구분합니다.

| 필요한 기억 | 우선 검토 | 담는 내용 |
|---|---|---|
| 다음 작업에도 지킬 규칙·선호 | `CLAUDE.md` + 내장 Auto memory | 개발 규칙, 사용자의 교정, 지속되는 프로젝트 맥락 |
| 지난 대화에서 무엇을 결정했는지 | `episodic-memory` 또는 `claude-mem` | 대화 원문 검색 또는 도구 관찰·작업 요약 |
| 사람이 읽고 관리하는 장기 지식 | `claude-obsidian` 또는 Basic Memory | 출처 있는 노트, 설계 결정, 학습·연구 자료 |

기본 제안은 **내장 기억을 먼저 사용하고, 과거 대화 검색과 지식 위키를 필요에 따라 추가**하는 것이다.
세 층은 역할을 나눈 운영 방식이다. 제품 사이의 자동 동기화·자동 위키 통합을 의미하지 않는다.

## 2. 자동 저장·자동 검색의 실제 차이

| 도구 | 자동으로 하는 부분 | 사람이 요청하거나 모델이 판단하는 부분 |
|---|---|---|
| `CLAUDE.md` | 해당 범위의 지침을 세션에 로드 | 규칙 작성·수정 |
| 내장 Auto memory | 기본 활성화된 로컬 세션에서 기억 기능 제공 | Claude가 저장 가치와 상세 기억 읽기를 판단 |
| `episodic-memory` | **SessionStart**에서 대화 동기화·색인 | 검색 스킬·agent가 필요에 따라 MCP 검색·읽기 |
| `claude-obsidian` | 시작·Stop hook으로 운영 안내·상태 점검 | 원문 ingest, 지식 저장, vault 질의 |
| Basic Memory | 추가 플러그인의 브리핑·체크포인트 | 지식 쓰기·검색; MCP만으로 전체 대화 캡처가 되지는 않음 |
| `claude-mem` | hook 기반 관찰 수집·AI 요약·세션 context 제공 | 검색과 상세 회수 |

hook은 정해진 시점에 실행되는 코드다. 스킬은 모델이 언제 어떤 도구를 쓸지 안내하는 지침이다.
따라서 “검색 스킬이 있다”는 사실은 “모든 질문 전에 검색 hook이 강제로 실행된다”는 뜻이 아니다.
로컬 보관과 모델 전송도 구분해야 한다. Claude가 읽은 기억은 사용하는 모델의 context에 포함될 수 있다.

## 3. 기본 구성: CLAUDE.md와 내장 Auto memory

**우선순위: 모든 사용자에게 먼저 권장. 별도 플러그인이나 MCP가 아니다.**

- `CLAUDE.md`: 사람이 정한 지침. 프로젝트 구조, 개발 규칙, 검증 명령처럼 반복해서 적용할 내용을 적는다.
- Auto memory: Claude가 사용자 선호·교정·프로젝트 맥락·참조 위치 등을 선별해 적는다.
- 로컬 세션에서는 기본 활성화지만 일부 백그라운드·중첩·호스팅 실행에는 예외가 있다.
- 기본 보관 위치는 `~/.claude/projects/<project>/memory/`이며, 같은 저장소의 worktree가 공유한다.
- `MEMORY.md`는 처음 200줄 또는 25KB까지 로드하고, 별도 주제 파일은 필요에 따라 읽는다.
- `/memory`로 확인·편집·활성 상태를 관리할 수 있다.
- 별도 기억 서버 요금은 없지만, 기억을 읽고 쓰는 작업은 Claude 사용의 일부다.
- 모든 대화·도구 실행을 보관하는 기록 장치로 기대하면 안 된다.
- 코드나 Git 이력에서 다시 알 수 있는 내용보다 반복되는 사용자 교정과 외부 맥락에 적합하다.

출처: [Claude Code 공식 기억 문서](https://code.claude.com/docs/en/memory).

## 4. 과거 대화 검색: episodic-memory

**우선순위: 대화의 결정 이유·예전 해결책을 자주 찾을 때 권장. 플러그인 + MCP + 스킬이다.**

- 대화 파일을 archive에 복사하고 사용자·agent 대화를 색인한다.
- 로컬 Transformers.js 임베딩과 SQLite/sqlite-vec를 사용한다.
- 의미 검색과 정확한 문자열 검색을 지원하고, 결과에서 원래 대화를 열 수 있다.
- 저장은 전용 로컬 archive·인덱스로 관리한다. `EPISODIC_MEMORY_CONFIG_DIR`로 기준 디렉터리를 바꿀 수 있다.
- 검색 결과에 붙이는 요약은 기본적으로 Claude 인증을 이용한 모델 호출이며 사용량이 발생할 수 있다.
- `EPISODIC_MEMORY_SKIP_SUMMARIES=1`이면 요약 호출을 생략하고 검색은 유지한다.
- 내장 Auto memory와 달리 원래 대화에서 논의한 대안·제약·이유를 찾는 데 목적이 있다.
- `claude-mem`과 겹치므로 초기에는 둘 중 하나를 선택하는 편이 관리하기 쉽다.

### Hook 동작 정정: SessionEnd가 아니라 SessionStart

확인 당시 README는 세션 종료 색인을 설명하지만 실제 `hooks/hooks.json`은 다음 동작이다.

| 항목 | 실제 hook 정의 |
|---|---|
| 이벤트 | `SessionStart` |
| matcher | `startup|resume|clear` |
| 동작 | CLI의 `sync --background` 실행 |
| SessionEnd | 해당 hook 파일에는 등록 없음 |

이 문서는 실제 hook 정의를 기준으로 한다. 시작·재개·`/clear` 때 기존 대화를 백그라운드로 동기화한다.
검색은 hook이 수행하지 않는다. `remembering-conversations` 스킬이 필요할 때 검색 agent를 호출하도록 안내한다.
실제 검색 실행은 모델의 스킬 선택과 준수에 의존한다.

출처: [README](https://github.com/obra/episodic-memory), [실제 hook](https://github.com/obra/episodic-memory/blob/main/hooks/hooks.json), [검색 스킬](https://github.com/obra/episodic-memory/blob/main/skills/remembering-conversations/SKILL.md).

## 5. 출처 있는 Obsidian 위키: claude-obsidian

**우선순위: Obsidian에 연구·학습·프로젝트 지식을 쌓는다면 주요 추천. Claude Code 플러그인·스킬 묶음이다.**

- 원문을 보존하고 출처가 연결된 Markdown 노트·링크·인덱스를 만든다.
- 선택한 vault가 보관 장소이며, Obsidian 커뮤니티 플러그인으로 설치하는 제품은 아니다.
- `wiki-ingest`는 자료를 지식으로 정리하는 작업이고, `wiki-query`는 읽기 전용 질의다.
- `save`는 사용자가 요청한 답변·통찰을 저장한다. 전 대화 자동 기록기가 아니다.
- `wiki-retrieve`는 로컬 BM25 검색을 제공한다. 선택형 reranking·원격 모델과 구분해야 한다.
- 시작·Stop hook은 운영 안내와 점검을 위한 것이며, 대화를 자동 지식 노트로 저장하는 기능으로 해석하면 안 된다.
- PDF/EPUB는 메타데이터·파일 보존을 지원하지만 본문 추출은 별도 도구가 필요하다.
- 로컬 파일을 기본으로 쓰되 Claude가 읽은 노트는 Claude에 전달된다. 추가 원격 작업은 별도다.
- 플러그인 자체 구독료는 없으며, 정리·질의에 사용하는 AI 사용량은 발생한다.
- episodic-memory 검색 결과를 자동으로 위키에 통합하는 기본 연동은 확인하지 않았다.

출처: [공식 README](https://github.com/AgriciDaniel/claude-obsidian), [hook 정의](https://github.com/AgriciDaniel/claude-obsidian/blob/main/hooks/hooks.json).

## 6. Obsidian 작성 능력: kepano/obsidian-skills

**우선순위: 위키 운영 전체보다 노트·Canvas·Bases 작성이 목적일 때 선택. 스킬 묶음이다.**

- Obsidian Markdown, Bases, JSON Canvas, CLI, Defuddle, Knap 사용법을 제공한다.
- 자체 기억 DB·대화 자동 캡처·지식 수명주기 관리 도구는 아니다.
- 보관은 작업하는 vault 파일이며, 별도 동기화 서비스를 제공하는 것으로 보지 않는다.
- CLI·웹 추출 등은 해당 실행 도구가 필요하다. 스킬 설치가 모든 실행 의존성을 해결하지는 않는다.
- `claude-obsidian`의 Markdown/Bases/Canvas/CLI/웹 추출 안내와 상당히 겹친다.
- 이미 claude-obsidian을 쓴다면 필요한 기능의 차이를 확인한 뒤 추가한다.
- AI가 파일을 작성·읽을 때는 사용하는 AI의 사용량과 데이터 처리 경로를 따른다.

출처: [공식 README와 스킬 목록](https://github.com/kepano/obsidian-skills).

## 7. 여러 AI가 공유하는 Markdown 지식: Basic Memory

**우선순위: Claude 외의 MCP 클라이언트와도 같은 지식을 쓰고 싶을 때 추천. MCP + 선택형 플러그인이다.**

- Markdown 원본과 로컬 SQLite 인덱스를 사용하며, 기본 노트 위치는 `~/basic-memory`다.
- 사람과 AI가 같은 파일을 읽고 쓰므로 Obsidian·텍스트 편집기와 함께 쓰기 좋다.
- 의미 검색과 지식 관계 탐색을 제공한다.
- Claude Code 플러그인은 세션 브리핑·압축 전 체크포인트·기억 명령을 추가한다.
- MCP만 연결했다고 모든 대화를 자동으로 기록하는 것은 아니다.
- 로컬판은 무료이며 AGPL-3.0, Cloud는 선택형 유료 서비스다. 최신 요금은 구매 시 확인한다.
- 로컬 보관과 Cloud 보관·동기화를 선택할 수 있고, 모델에 전달되는 검색 결과는 별개다.
- CLI의 익명 프로모션·전환 통계가 문서화되어 있으며 opt-out 설정이 있다.
- claude-obsidian과 장기 노트 역할이 겹친다. 출처 보존 위키와 범용 MCP 지식 저장소 중 우선 목적을 고른다.

출처: [공식 README: 저장·플러그인·Telemetry](https://github.com/basicmachines-co/basic-memory).

## 8. 개발 작업 관찰의 자동 기억: claude-mem

**우선순위: 도구 실행·디버깅 이력을 자동 요약해 이어가고 싶을 때 선택. hook 중심 플러그인이다.**

- 세션·도구 실행 관찰을 수집하고 AI로 요약해 이후 세션에 필요한 context를 제공한다.
- 로컬 worker, SQLite와 검색 도구를 사용하며 Chroma 의미 검색은 선택 구성이다.
- 기본 DB 경로는 `~/.claude-mem/claude-mem.db`다.
- 검색은 인덱스 → 타임라인 → 필요한 관찰 상세 조회의 흐름을 제공한다.
- 자동 수집은 편하지만 무엇을 저장·주입할지 설정과 유지 관리가 필요하다.
- Node/Bun worker 등 운영 요소가 있으며, 단순 Markdown 파일만 관리하는 구성보다 복잡하다.
- 요약은 Claude 플랜/API 또는 선택한 provider의 사용량을 소비한다.
- 선택형 hosted observer·Cloud Sync가 있으므로 “완전 로컬·완전 무료”라고 단정하면 안 된다.
- episodic-memory와 함께 시작하기보다, 원문 대화 검색과 관찰 요약 중 필요한 쪽을 고른다.

출처: [README](https://github.com/thedotmack/claude-mem), [아키텍처](https://docs.claude-mem.ai/architecture/overview), [provider 설정](https://docs.claude-mem.ai/configuration).

## 9. Serena를 사용 중이라면: Serena memories

**우선순위: Serena 코드 탐색·편집을 이미 사용하는 경우 우선 활용. 별도 기억 전용 제품은 아니다.**

- 프로젝트 기억은 `.serena/memories/`, 공통 기억은 기본 `~/.serena/memories/global/`에 둔다.
- 사람이 읽고 고칠 수 있는 Markdown이며 프로젝트 기억을 Git으로 관리할 수 있다.
- 초기 onboarding에서 프로젝트 정보를 조사해 기록한다.
- 이후 agent는 기억 이름 목록과 내부 참조를 바탕으로 필요한 파일을 읽는다.
- 기본 철학은 벡터 검색이나 hook 자동 주입보다 이름·참조를 통한 선택적 읽기다.
- 새로운 사실과 결정의 갱신을 명시적으로 요청하면 운영 기준을 유지하기 쉽다.
- 내용 저장과 읽기는 agent 사용량의 일부다. Serena 자체의 코드 분석 기능과 함께 도입 부담을 판단한다.
- Serena 자체는 프로젝트 데이터 외부 전송 없이 익명 사용 통계를 수집한다고 밝히며 opt-out을 제공한다.
- MCP가 반환한 기억이 사용하는 AI에게 전달되는 것은 별개다.

출처: [기억·onboarding](https://oraios.github.io/serena/02-usage/045_memories.html), [개인정보 정책](https://oraios.github.io/serena/01-about/070_privacy.html).

## 10. 공유 기억 서버: mcp-memory-service

**우선순위: 여러 agent·클라이언트가 공통 기억 서버를 쓰는 경우 조건부 추천. 백엔드 + MCP/REST다.**

- 로컬 ONNX 임베딩·SQLite 기반 기억 저장, 의미/BM25 검색, 지식그래프·문서 ingest를 제공한다.
- 보관 위치·데이터 경로는 선택한 백엔드 설정에 따른다. Cloudflare·Hybrid·Milvus 선택지도 있다.
- 선택형 Claude 플러그인의 세션 종료 hook은 키워드 요약을 자동 저장한다.
- 중요한 결정·원인·교훈은 `remember-session`으로 모델이 선별하고 중복 확인 후 저장한다.
- 핵심 로컬 연산과 선택형 LLM 요약·평가, Cloud 동기화를 구분해야 한다.
- LLM 기능은 설정한 provider로 데이터를 보내며, 동기화는 선택한 원격 저장소를 사용한다.
- Python 서비스, endpoint·API key, 선택적 Node hook 등을 운영해야 한다.
- Claude 플러그인은 문서상 실험 단계다. 기존 hook 설치기와 플러그인을 동시에 켜면 중복 실행될 수 있다.
- 개인의 단일 Claude Code+Obsidian 구성에는 Basic Memory나 claude-obsidian보다 운영 부담이 클 수 있다.

출처: [공식 README](https://github.com/doobidoo/mcp-memory-service), [플러그인 실제 저장 방식·실험 상태](https://github.com/doobidoo/mcp-memory-service/blob/main/claude-hooks/PLUGIN.md).

## 11. 기본 추천에서 제외하거나 실험용으로 두는 후보

### MCP Memory reference server

- **유형:** MCP 참조 구현. 엔터티·관계·관찰을 로컬 JSONL에 저장한다.
- 모델이 저장·검색 도구를 호출해야 하며 대화 자동 기록·의미 검색 시스템과 다르다.
- `MEMORY_FILE_PATH`로 파일을 지정한다. 기본은 서버 디렉터리의 `memory.jsonl`이다.
- 별도 LLM 추출 백엔드는 기본 요구가 아니지만, 이를 사용하는 Claude의 사용량은 발생한다.
- 간단한 실험·자체 MCP 개발에는 유용하나 공식 저장소가 production-ready가 아닌 참조 구현이라고 명시한다.
- 개인의 주 기억 시스템으로는 앞선 후보보다 우선순위를 낮춘다.

출처: [Memory README](https://github.com/modelcontextprotocol/servers/blob/main/src/memory/README.md), [참조 구현의 범위](https://github.com/modelcontextprotocol/servers).

### Graphiti

- **유형:** 시간 정보를 가진 지식그래프 프레임워크 + 참조 MCP 서버.
- episode에서 엔터티·관계를 추출하고 시간 조건·의미·혼합 검색으로 사실을 찾는다.
- 저장은 FalkorDB/Neo4j이며, 추출 LLM·임베딩 provider를 구성해야 한다.
- 외부 API를 쓰면 추론 데이터와 사용량이 해당 provider로 간다. 로컬 모델 구성도 가능하다.
- MCP 연결만으로 전체 대화를 자동 기록하는 Claude 플러그인은 아니다.
- 참조 서버는 인증·권한관리 없는 실험 구현으로 명시되어 있다.
- 일반 개인용 추천에서 제외하고, 시간적 관계를 가진 기억 시스템을 직접 개발할 때 검토한다.

출처: [Graphiti MCP README](https://github.com/getzep/graphiti/blob/main/mcp_server/README.md).

### remember / claude-remember

- **유형:** 자동 작업 일지·인계 플러그인. 대화를 일별·최근·장기 Markdown 요약으로 압축한다.
- 기본 저장소는 프로젝트 `.remember/`, 외부 저장 모드는 `~/.remember/<slug>/`다.
- 세션 시작에 여러 기억 파일을 주입하고 명시적 인계 메모 기능을 제공한다.
- 요약은 별도 Claude CLI 호출 등으로 처리하므로 인증된 provider의 사용량이 발생한다.
- 확인 당시 라이선스는 source-available이며 수정·재배포·재판매를 허용하지 않는다고 명시한다.
- 외부 저장 모드에서 상위 폴더가 upstream 있는 Git 저장소이면 자동 백업 push 조건이 생긴다.
- 자동 일지를 선호하면 검토할 수 있으나, 데이터 흐름·라이선스·중복을 고려해 기본 조합에서는 제외한다.

출처: [공식 README: 동작·저장·Git 백업·라이선스](https://github.com/Digital-Process-Tools/claude-remember).

## 12. 용도별 최종 선택

| 사용자 목적 | 시작 조합 | 추가 시점 |
|---|---|---|
| 일반 개발, 최소 관리 | 내장 Auto memory + `CLAUDE.md` | 과거 대화 회수 실패가 반복될 때 확장 |
| 예전 결정·대화 검색 | 기본 구성 + episodic-memory | 원문 검색 외에 작업 관찰 요약이 필요하면 claude-mem과 비교 |
| Obsidian 연구·학습 위키 | 기본 구성 + claude-obsidian | 과거 대화도 필요할 때 episodic-memory 추가 |
| Obsidian 문법·Canvas·Bases 작성 | 기본 구성 + obsidian-skills | 출처 보존·ingest·위키 점검이 필요하면 claude-obsidian 검토 |
| 여러 AI의 Markdown 지식 공유 | 기본 구성 + Basic Memory | 개인 파일 관리보다 공유 서버가 필요하면 mcp-memory-service 비교 |
| Serena 중심 코드 작업 | 기본 구성 + Serena memories | 대화 이력·연구 위키는 별도 목적이 있을 때만 추가 |
| 여러 agent의 기억 백엔드 | mcp-memory-service | 그래프의 시간적 사실 추적을 직접 개발한다면 Graphiti 검토 |

내장 기억 + episodic-memory + claude-obsidian 조합은 **규칙·선호 / 대화 원문 / 선별 지식**을 나누는 제안이다.
예를 들어 과거 대화를 검색한 뒤 “이 결정과 근거를 vault에 저장해 줘”라고 요청하는 수동 연결이 가능하다.
항상 자동으로 기록을 위키에 옮기거나 검색 결과를 지식으로 승격하는 연동이 제공된다고 가정하지 않는다.
처음에는 목적에 맞는 한 가지를 추가하고, 중복 저장·중복 주입·실제 회수 품질을 확인한 뒤 확장한다.

---

[목차로 돌아가기](00-index.md)
