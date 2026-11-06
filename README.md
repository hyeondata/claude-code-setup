# 나의 Claude Code 설정

여러 컴퓨터에서 같은 개발 절차와 기억 자동화 **설정**을 복원하기 위한 개인 저장소입니다. Obsidian 보관함, 대화 기록, Auto memory 데이터, 저장 초안, 인증정보는 포함하지 않습니다.

## 새 컴퓨터에서 시작

macOS 또는 Linux에서 Git, 인증된 Claude Code CLI, **Python 3.10 이상**, **Node.js 20 이상**을 먼저 준비합니다. macOS의 기본 `python3`이 오래된 경우에도 `claude-sync`가 `python3.11` 등 설치된 지원 버전을 찾아 사용합니다.

비공개 GitHub 저장소이므로 GitHub 인증이 필요합니다. `~/claude`가 이미 존재하면 비어 있는 다른 폴더에 clone하세요.

```sh
git clone https://github.com/hyeondata/claude-code-setup.git "$HOME/claude"
cd "$HOME/claude"
./claude-sync pull --dry-run
./claude-sync pull
```

`--dry-run`은 현재 내려받은 파일로 **적용 미리보기만** 하며 Git fetch/pull이나 파일 변경을 하지 않습니다. `./claude-sync pull`은 최신 설정을 받아 적용하고 누락된 기본 플러그인을 설치합니다. 적용 후 Claude Code의 **새 세션**을 시작하세요. 이미 설치된 사용자 플러그인의 버전이나 비활성화 상태는 강제로 바꾸지 않습니다. 실행기는 Python 3.10 이상을 자동으로 찾습니다.

보관함이 다른 곳에 있다면 `--vault "/실제/보관함/경로"`를 지정합니다. 설치 스크립트는 보관함을 생성·초기화·복사하지 않습니다. 기존 보관함은 Obsidian Sync 등 별도 방법으로 복원하고, 새 보관함을 원하면 Claude Code에서 `/claude-obsidian:wiki`에 사용할 경로와 초기화 요청을 전달하세요. 초기화 전에는 지식 검색·저장이 작동하지 않을 수 있지만 설정 설치는 가능합니다.

## 복원되는 것

| 기능 | 구성 |
|---|---|
| 기본 개발 절차 | Superpowers |
| 도메인·모듈 설계와 지침 문서 | Matt Pocock 스킬 |
| 변경 영향 분석·심층 리뷰 | pstack, 직접 호출 제한 유지 |
| 기억 | Auto memory 활성화, episodic-memory, claude-obsidian 연결 지침 |
| 자동화 | 세션 동기화, 질문별 제한된 검색, 완료 시 선택적 저장 알림 |
| 문서·설정 보조 | Context7, claude-md-management, claude-code-setup |

개발 스킬의 주도 절차는 하나만 선택합니다. 기본 구현·디버깅·TDD는 Superpowers, 필요한 도메인·설계 단계는 Matt으로 연결합니다. `pstack:blast-radius`, `pstack:interrogate`와 Matt의 일부 심화 명령은 제작자가 직접 호출 전용으로 지정했으므로 자동 실행을 약속하지 않습니다. [역할 분담 상세](docs/14-skill-routing.md)

`config/plugins.json`은 설치 소스와 **검증 당시 버전**을 기록합니다. 버전 고정 lockfile은 아닙니다. 새 설치는 각 마켓플레이스의 현재 배포 항목을 따르므로 이후 버전은 달라질 수 있습니다. 플러그인 소스·캐시를 이 저장소에 복사하지 않습니다.

## 컴퓨터마다 따로 필요한 것

- Claude와 GitHub 로그인, Context7 등 서비스 연결 승인은 각 컴퓨터에서 수행합니다. Context7 로그인은 이 구성에서 자동 진행하지 않습니다.
- **보관함과 과거 대화는 Git으로 동기화되지 않습니다.** 이 저장소는 동작 규칙과 자동화 코드를 옮깁니다. 기존 기억 데이터까지 다른 컴퓨터에 생기는 것은 아닙니다.
- 기존 환경의 `serena`(`uvx`)와 `headroom` MCP는 컴퓨터별 별도 설치·등록 대상입니다. 원래 MCP 등록부나 실행 환경 전체를 덮어쓰지 않습니다. 필요한 등록은 각 도구의 공식 안내와 프로젝트 환경을 따르세요.
- Dart/Flutter가 필요하면 SDK를 설치하고 `dart`를 실행할 수 있는 PATH를 준비한 뒤 아래 선택 설치를 사용합니다. SDK 자체를 다운로드하거나 프로젝트별 SDK 경로를 복제하지 않습니다.

```sh
~/claude/claude-sync pull --with-optional
```

### 기억 구성 선택(`--memory`)

| 값 | 설치·연결되는 것 | 쓰는 경우 |
|---|---|---|
| `full`(기본) | 내장 Auto memory + episodic-memory + claude-obsidian + 이 저장소의 생애주기 훅(시작·입력·종료 시 검색·동기화) | 새 컴퓨터에 기억 체계가 없을 때 |
| `none` | 내장 Auto memory만 켬. 기억 플러그인 2개, 훅, 관련 env·권한 규칙, `automation/config.json`을 만들지 않음 | 그 컴퓨터에 이미 다른 기억 체계(예: 대화 수집 훅·인계 노트·노트 검색)가 있어 대화를 이중으로 저장하지 않으려 할 때 |

```sh
~/claude/claude-sync pull --memory none
```

- 고른 값은 `~/.claude/claude-code-setup-state.json`에 남아 다음 `claude-sync pull`에서 그대로 쓰입니다. 바꿀 때만 `--memory`를 다시 지정합니다.
- `full`에서 `none`으로 바꾸면 이 저장소가 넣었던 훅·env·권한 규칙만 지웁니다. 다른 훅과 사용자 설정, 이미 설치된 플러그인은 그대로 둡니다(플러그인은 필요하면 `claude plugin uninstall`로 직접 지웁니다).
- `none`에서도 개발 절차 플러그인(Superpowers, Matt, pstack, Context7 등)은 똑같이 설치됩니다.

### graphify(코드 지식 그래프, 컴퓨터별 설치)

[graphify](https://github.com/Graphify-Labs/graphify)는 Claude 플러그인이 아니라 Python CLI라서 이 저장소가 설치하지 않습니다. 설치 스크립트는 없으면 안내만 출력합니다.

```sh
uv tool install graphifyy                 # CLI: graphify, graphify-mcp
graphify install --platform claude        # 전역 스킬(~/.claude/skills/graphify)과 CLAUDE.md 안내
```

프로젝트마다(그래프를 쓸 저장소 안에서):

```sh
/graphify .                               # Claude Code 안에서 첫 그래프 생성(graphify-out/)
graphify claude install                   # 프로젝트 CLAUDE.md 규칙 + PreToolUse 안내 훅
graphify hook install                     # 커밋 시 그래프 자동 갱신(git 훅)
claude mcp add --scope local graphify -- "$(command -v graphify-mcp)" "$PWD/graphify-out/graph.json"
```

- MCP는 그래프 파일 경로가 프로젝트마다 달라 `local` 범위로 프로젝트별 등록합니다.
- `graphify-out/`을 git에 넣지 않으려면 `.git/info/exclude`에 추가합니다.

## 관리되는 파일과 보존 범위

- `config/CLAUDE.md.tmpl`: 영어 운영 지침의 원본. 응답과 개인 노트는 한국어 기본값입니다.
- `config/plugins.json`: 복원할 플러그인·마켓플레이스 목록.
- `automation/`: 보관함 쓰기의 검증·공식 트랜잭션을 유지하는 실행 코드와 문서 템플릿.
- `claude-sync` / `scripts/sync.py`: 공유 파일 커밋·푸시 및 pull 후 적용을 수행합니다.
- `scripts/bootstrap.py`: 현재 컴퓨터의 Python·Node·설정·보관함 경로를 감지하고 병합합니다.
- `docs/`: 이전 추천 조사 및 설치 기록 14개. 기록 속 당시 설치 경로와 상태를 새 컴퓨터의 사실로 해석하지 마세요. [문서 목차](docs/00-index.md)
- 문서 본문은 한국어로 유지하고 파일명은 ASCII로 통일했습니다. macOS 업로드 시 한글 파일명의 NFC/NFD 정규화 차이로 링크가 끊어지는 문제를 방지합니다.

스크립트는 `~/.claude/settings.json`의 관련 항목을 병합하고, `~/.claude/CLAUDE.md`에는 관리 표식이 있는 블록을 추가·갱신합니다. 기존의 다른 훅·권한·설정·지침을 보존합니다. 반복 실행해도 관리 블록과 훅이 중복되지 않습니다. 기존 지침에 상충하는 수동 규칙이 있다면 내용을 확인해 조정하세요.

`automation/config.json`, `automation/AUTOMATION.md`, `automation/drafts/`는 컴퓨터에서 생성하는 **Git 제외 대상**입니다. 적용 후 운영 방법은 생성된 `automation/AUTOMATION.md`를 읽으세요. 기본 경로가 아닌 Claude 설정 디렉터리를 사용하면 `--claude-home`을 지정하고 Claude도 같은 `CLAUDE_CONFIG_DIR`로 실행해야 합니다.

## 변경한 설정을 다른 컴퓨터와 공유

공유할 지침은 `config/CLAUDE.md.tmpl`, 플러그인 목록은 `config/plugins.json`에서 수정합니다. `~/.claude/CLAUDE.md`와 `~/.claude/settings.json`은 설치 후 생성·병합되는 기기별 파일이므로 그 파일만 수정하면 Git으로 공유되지 않습니다.

변경한 컴퓨터에서는 어느 폴더에서든 다음 한 명령으로 공유 파일의 변경을 커밋·푸시합니다. 커밋 메시지는 생략할 수 있습니다.

```sh
~/claude/claude-sync push -m "Update shared Claude settings"
```

다른 컴퓨터에서는 다음 한 명령으로 최신 설정을 내려받아 적용하고, 새로 추가된 기본 플러그인을 설치합니다.

```sh
~/claude/claude-sync pull
```

이 명령이 추가되기 전에 복제한 다른 컴퓨터에서는 최초 한 번 `git -C ~/claude pull --ff-only`로 실행기를 받아야 합니다. 그 뒤부터는 위 명령만 사용하면 됩니다.

백그라운드 자동 실행은 하지 않습니다. 명령을 실행할 때만 동기화합니다. `push`는 이 저장소의 공유 원본을 올리는 명령이며, 그 컴퓨터에도 변경 내용을 적용하려면 `pull`을 실행합니다. 적용 후 Claude Code의 새 세션을 시작하세요.

## 업데이트와 컴퓨터별 경로

`pull`은 `git pull --ff-only` 성공 후 기존 설치 스크립트를 실행합니다. 이전 적용 때 생성한 `automation/config.json`의 보관함·Claude 설정·Node 경로를 재사용합니다. 처음 실행할 때 기본 보관함은 **복제한 저장소 안의 `obsidian/`**입니다. Claude 설정은 `CLAUDE_CONFIG_DIR` 또는 `~/.claude`를 사용합니다.

다른 경로나 선택 플러그인이 필요할 때만 지정하세요. 보관함·Claude 설정·Node 경로는 성공적으로 적용된 뒤 다음 실행에서 재사용됩니다. 선택 플러그인의 신규 설치는 필요한 컴퓨터에서 `--with-optional`을 사용합니다.

```sh
~/claude/claude-sync pull --vault "/다른/Obsidian/경로"
~/claude/claude-sync pull --claude-home "/다른/Claude/설정"
~/claude/claude-sync pull --with-optional
~/claude/claude-sync pull --dry-run
```

- 공유 파일에 커밋하지 않은 Git 변경이 있으면 `pull`이 중단됩니다. 변경을 먼저 커밋·푸시하거나 별도로 정리하세요. 보관함처럼 Git에서 제외된 파일의 변경은 방해하지 않습니다.
- 다른 컴퓨터가 먼저 push한 상태에서는 `push`가 중단될 수 있습니다. 원격과 로컬에 서로 다른 커밋이 생겼다면 일반 Git 명령으로 내용을 검토·병합한 뒤 다시 실행하세요. 자동 강제 push, reset, stash는 하지 않습니다.
- 푸시가 실패해도 생성한 로컬 커밋은 남습니다. 네트워크·인증 문제를 해결한 뒤 같은 `push` 명령으로 재시도할 수 있습니다. 변경이 없으면 빈 커밋을 만들지 않습니다.
- pull은 성공했지만 적용이 실패한 경우 원인을 해결하고 같은 `pull` 명령을 다시 실행하면 됩니다. 기존 설치 스크립트는 재실행과 백업을 지원합니다.
- Python 실행 파일을 직접 정하려면 `CLAUDE_SYNC_PYTHON="/Python/실행파일" ~/claude/claude-sync pull`을 사용합니다. 일반 사용에는 필요하지 않습니다.

## 제외와 복구

`.gitignore`는 허용 목록 방식입니다. `obsidian/`뿐 아니라 실제 설정 JSON, 저장 초안, 백업, 로그, 데이터베이스, 캐시, 인증 파일은 기본적으로 추적하지 않습니다. `claude-sync push`도 명시된 공유 파일만 추가하고, 이미 강제로 추가된 허용 외 파일과 아직 보내지 않은 커밋의 파일 목록을 검사합니다. 새 공유 소스를 추가할 때는 `.gitignore`와 `scripts/sync.py`의 허용 목록을 함께 갱신하세요. 개인 파일을 `git add -f`로 강제 등록하지 마세요. 허용된 설정·문서 안에 직접 적은 비밀값까지 자동 판별하지는 않으므로 공유 원본에는 인증정보나 개인 노트 본문을 넣지 않습니다.

적용 전에는 백업 경로와 복구 지침을 출력합니다. 해당 백업의 `manifest.json`에 따라 원래 있던 파일을 복원하고, 처음 생성된 파일만 삭제하면 됩니다. 플러그인 설치는 외부 CLI 작업이므로 별도 제거가 필요할 수 있습니다. 설치 중 실패했다면 원인을 해결하고 같은 명령으로 재실행하세요. 전체 사용자 설정을 과거 사본으로 무조건 덮어쓰면 이후의 다른 변경을 잃을 수 있습니다.

## 검증 범위

```sh
python3.11 -B -m unittest discover -s tests -v
claude plugin list
```

임시 환경에서 미리보기의 무변경, 설정 보존, 재실행, 경로 공백 처리, 플러그인 설치 후 병합을 검증합니다. 별도의 임시 Git 원격 저장소와 두 복제본으로 커밋·푸시, pull 후 적용, 보관함 제외 및 충돌 시 중단도 확인합니다. 실제 새 컴퓨터에서 로그인과 보관함 초기화까지 대신 수행하는 테스트는 아닙니다. 기존 Mac의 플러그인 선택·기억 자동화 검증은 `docs/13-installed-memory.md`, `docs/14-skill-routing.md`를 참고하세요.
