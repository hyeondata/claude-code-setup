# 나의 Claude Code 설정

여러 컴퓨터에서 같은 개발 절차와 기억 자동화 **설정**을 복원하기 위한 개인 저장소입니다. Obsidian 보관함, 대화 기록, Auto memory 데이터, 저장 초안, 인증정보는 포함하지 않습니다.

## 새 컴퓨터에서 시작

macOS 또는 Linux에서 Git, 인증된 Claude Code CLI, **Python 3.10 이상**, **Node.js 20 이상**을 먼저 준비합니다. 아래 예시는 `python3.11`을 사용합니다. 다른 실행 파일을 쓴다면 먼저 `--version`으로 버전을 확인하고 바꾸세요. macOS의 기본 `python3`은 더 오래된 버전일 수 있습니다.

비공개 GitHub 저장소이므로 GitHub 인증이 필요합니다. `~/claude`가 이미 존재하면 비어 있는 다른 폴더에 clone하세요.

```sh
git clone https://github.com/hyeondata/claude-code-setup.git "$HOME/claude"
cd "$HOME/claude"
python3.11 scripts/bootstrap.py --install-plugins
python3.11 scripts/bootstrap.py --apply --install-plugins --vault "$HOME/claude/obsidian"
```

첫 실행은 **미리보기만** 합니다. `--apply`를 붙인 실행만 설정을 기록하고, `--install-plugins`가 함께 있으면 누락된 플러그인을 설치합니다. 적용 후 Claude Code의 **새 세션**을 시작하세요. 이미 설치된 사용자 플러그인의 버전이나 비활성화 상태는 강제로 바꾸지 않습니다.

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

개발 스킬의 주도 절차는 하나만 선택합니다. 기본 구현·디버깅·TDD는 Superpowers, 필요한 도메인·설계 단계는 Matt으로 연결합니다. `pstack:blast-radius`, `pstack:interrogate`와 Matt의 일부 심화 명령은 제작자가 직접 호출 전용으로 지정했으므로 자동 실행을 약속하지 않습니다. [역할 분담 상세](docs/14_개발스킬_설치와_역할분담.md)

`config/plugins.json`은 설치 소스와 **검증 당시 버전**을 기록합니다. 버전 고정 lockfile은 아닙니다. 새 설치는 각 마켓플레이스의 현재 배포 항목을 따르므로 이후 버전은 달라질 수 있습니다. 플러그인 소스·캐시를 이 저장소에 복사하지 않습니다.

## 컴퓨터마다 따로 필요한 것

- Claude와 GitHub 로그인, Context7 등 서비스 연결 승인은 각 컴퓨터에서 수행합니다. Context7 로그인은 이 구성에서 자동 진행하지 않습니다.
- **보관함과 과거 대화는 Git으로 동기화되지 않습니다.** 이 저장소는 동작 규칙과 자동화 코드를 옮깁니다. 기존 기억 데이터까지 다른 컴퓨터에 생기는 것은 아닙니다.
- 기존 환경의 `serena`(`uvx`)와 `headroom` MCP는 컴퓨터별 별도 설치·등록 대상입니다. 원래 MCP 등록부나 실행 환경 전체를 덮어쓰지 않습니다. 필요한 등록은 각 도구의 공식 안내와 프로젝트 환경을 따르세요.
- Dart/Flutter가 필요하면 SDK를 설치하고 `dart`를 실행할 수 있는 PATH를 준비한 뒤 아래 선택 설치를 사용합니다. SDK 자체를 다운로드하거나 프로젝트별 SDK 경로를 복제하지 않습니다.

```sh
python3.11 scripts/bootstrap.py --apply --install-plugins --with-optional --vault "$HOME/claude/obsidian"
```

## 관리되는 파일과 보존 범위

- `config/CLAUDE.md.tmpl`: 영어 운영 지침의 원본. 응답과 개인 노트는 한국어 기본값입니다.
- `config/plugins.json`: 복원할 플러그인·마켓플레이스 목록.
- `automation/`: 보관함 쓰기의 검증·공식 트랜잭션을 유지하는 실행 코드와 문서 템플릿.
- `scripts/bootstrap.py`: 현재 컴퓨터의 Python·Node·설정·보관함 경로를 감지하고 병합합니다.
- `docs/`: 이전 추천 조사 및 설치 기록 14개. 기록 속 당시 설치 경로와 상태를 새 컴퓨터의 사실로 해석하지 마세요.

스크립트는 `~/.claude/settings.json`의 관련 항목을 병합하고, `~/.claude/CLAUDE.md`에는 관리 표식이 있는 블록을 추가·갱신합니다. 기존의 다른 훅·권한·설정·지침을 보존합니다. 반복 실행해도 관리 블록과 훅이 중복되지 않습니다. 기존 지침에 상충하는 수동 규칙이 있다면 내용을 확인해 조정하세요.

`automation/config.json`, `automation/AUTOMATION.md`, `automation/drafts/`는 컴퓨터에서 생성하는 **Git 제외 대상**입니다. 적용 후 운영 방법은 생성된 `automation/AUTOMATION.md`를 읽으세요. 기본 경로가 아닌 Claude 설정 디렉터리를 사용하면 `--claude-home`을 지정하고 Claude도 같은 `CLAUDE_CONFIG_DIR`로 실행해야 합니다.

## 업데이트

```sh
git pull --ff-only
python3.11 scripts/bootstrap.py --vault "/현재/보관함/경로"
python3.11 scripts/bootstrap.py --apply --vault "/현재/보관함/경로"
```

다른 보관함을 사용한다면 재적용할 때도 같은 `--vault`를 지정하세요. 지침 변경은 설치된 전역 파일 대신 `config/CLAUDE.md.tmpl`에 반영하여 커밋하고 각 컴퓨터에서 다시 적용합니다. 새 플러그인이 추가된 경우에만 `--install-plugins`를 함께 사용하면 됩니다.

## 제외와 복구

`.gitignore`는 허용 목록 방식입니다. `obsidian/`뿐 아니라 실제 설정 JSON, 저장 초안, 백업, 로그, 데이터베이스, 캐시, 인증 파일은 기본적으로 추적하지 않습니다. 새 소스 파일을 추가하려면 필요한 경로만 허용 목록에 추가하세요. 개인 파일을 `git add -f`로 강제 등록하지 마세요.

적용 전에는 백업 경로와 복구 지침을 출력합니다. 해당 백업의 `manifest.json`에 따라 원래 있던 파일을 복원하고, 처음 생성된 파일만 삭제하면 됩니다. 플러그인 설치는 외부 CLI 작업이므로 별도 제거가 필요할 수 있습니다. 설치 중 실패했다면 원인을 해결하고 같은 명령으로 재실행하세요. 전체 사용자 설정을 과거 사본으로 무조건 덮어쓰면 이후의 다른 변경을 잃을 수 있습니다.

## 검증 범위

```sh
python3.11 -B -m unittest discover -s tests -v
claude plugin list
```

임시 환경에서 미리보기의 무변경, 설정 보존, 재실행, 경로 공백 처리, 플러그인 설치 후 병합 등을 검증합니다. 실제 새 컴퓨터에서 로그인과 보관함 초기화까지 대신 수행하는 테스트는 아닙니다. 기존 Mac의 플러그인 선택·기억 자동화 검증은 `docs/13_설치결과와_자동기억_운영.md`, `docs/14_개발스킬_설치와_역할분담.md`를 참고하세요.
