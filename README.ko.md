# TMS Development Wizard MCP Server

[![English](https://img.shields.io/badge/🇬🇧-English-blue.svg)](README.md)
[![한국어](https://img.shields.io/badge/🇰🇷-한국어-orange.svg)](README.ko.md)

---

## 🎯 개요

**🚚TMS Development Wizard🧙‍♂️**는 [Omelet의 Routing Engine](https://www.oaasis.cc/routing)과 [iNavi의 Maps API](https://mapsapi.inavisys.com/)를 탐색할 수 있는 도구를 제공하여 TMS(Transport Management System) 구축을 돕습니다. 더 이상 여러 API 문서를 오가며 씨름할 필요 없이, 나만의 맞춤형 TMS를 손쉽게 구축해보세요.

**이런 분들께 적합합니다:**
- 🚀 **빠른 API 탐색** - 긴 문서를 읽지 않고도 가능한 기능을 빠르게 파악
- 🧪 **프로토타이핑 & 테스트** - 수 분 안에 테스트 구현 완성
- 🏗️ **프로덕션 시스템** - API 통합 패턴 가이드로 복잡한 TMS 워크플로우 구축

---

## ✨ 기능

- 🚀 **멀티 프로바이더 지원** - Omelet Routing Engine과 iNavi Maps API 문서에 대한 통합 액세스
- 📚 **엔드포인트 탐색** - 상세한 개요와 함께 프로바이더별 API 엔드포인트 검색 및 필터링 (`list_endpoints`, `get_endpoint_overview`)
- 🧩 **통합 패턴** - 일반적인 TMS 사용 사례를 위한 에이전틱 코딩 가이드라인이 포함된 사전 구축된 워크플로우 패턴 (`list_integration_patterns`, `get_integration_pattern`)
- 🔍 **스키마 탐색기** - 모든 엔드포인트와 HTTP 상태 코드에 대한 요청/응답 스키마 검사 (`get_request_body_schema`, `get_response_schema`)
- 💡 **예제 라이브러리** - OpenAPI 스펙에서 추출한 실제 API 요청/응답 예제 액세스 (`list_examples`, `get_example`)

> **참고:** [Omelet](https://routing.oaasis.cc/)과 [iNavi](https://mapsapi.inavisys.com/)의 API 키는 이 MCP 서버 설치에 필수는 아닙니다. 하지만 실시간 테스트가 가능한 원활한 코딩 경험과 적절한 디버깅을 위해 미리 준비하시는 것을 권장합니다.

---

## 🚀 빠른 시작

### MCP 서버 설치

**사전 요구사항:** [uv](https://docs.astral.sh/uv/getting-started/installation/)가 설치되어 있어야 합니다.

<details>
<summary><b>Cursor</b></summary>

Cursor > Settings > Cursor Settings > Tools & MCP로 이동한 뒤 아래 내용을 추가하세요:

```json
{
   "mcpServers": {
      "TMS Development Wizard": {
         "command": "uvx",
         "args": ["tms-mcp"]
      }
   }
}
```
</details>
<details>
<summary><b>Claude Desktop</b></summary>

⚠️ Claude Desktop은 API 서버에 직접 요청을 전송할 수 없습니다. 엔드포인트와 응답 탐색용으로만 활용하세요.

1. 터미널에서 `uvx` 설치 경로를 확인합니다.
   - macOS/Linux: `which uvx`
   - Windows: `where uvx`

2. MCP 설정 JSON 파일을 열고(Claude > Settings > Developer > Edit Config) 아래 내용을 추가합니다:

```json
{
   "mcpServers": {
      "TMS Development Wizard": {
         "command": "[1단계에서 확인한 uvx 경로]",
         "args": ["tms-mcp"]
      }
   }
}
```

3. JSON 파일을 저장하고 Claude Desktop을 재시작합니다.
</details>
<details>
<summary><b>Claude Code</b></summary>

프로젝트 루트에서 터미널을 열고 실행:

```bash
claude mcp add TMS-Development-Wizard uvx tms-mcp
```
</details>
<details>
<summary><b>Codex CLI</b></summary>

프로젝트 루트에서 터미널을 열고 실행:

```bash
codex mcp add TMS-Development-Wizard uvx tms-mcp
```
</details>
<details>
<summary><b>Gemini CLI</b></summary>

프로젝트 루트에서 터미널을 열고 실행:

```bash
gemini mcp add TMS-Development-Wizard uvx tms-mcp
```
</details>

### 사용 예제

<details>
<summary><b>🔍 사용 가능한 API 탐색</b></summary>

```
Omelet에서 사용 가능한 라우팅 API는 무엇인가요?
```

```
지오코딩을 위한 모든 iNavi 엔드포인트를 보여주세요
```

```
VRP와 Advanced VRP 엔드포인트의 차이점은 무엇인가요?
```

```
사용 가능한 모든 통합 패턴을 나열해주세요
```

</details>

<details>
<summary><b>🏗️ 기능 구축</b></summary>

```
Omelet의 VRP API를 사용하여 50개 배송 주소에 대한 경로 최적화를 구현하는 데 도움을 주세요
```

```
100개 위치에 대한 거리 매트릭스를 계산해야 합니다. 어떤 엔드포인트를 사용해야 하고 어떻게 해야 하나요?
```

```
iNavi의 지오코딩 API를 사용하여 주소를 좌표로 변환하는 함수를 만들어주세요
```

```
시간 창이 있는 픽업-배송 문제를 구현하는 방법을 보여주세요
```

</details>

<details>
<summary><b>🧩 통합 패턴 따르기</b></summary>

```
라스트마일 배송 시스템을 구축하고 싶습니다. 어떤 통합 패턴을 따라야 하나요?
```

```
내비게이션 앱을 위한 고정밀 라우팅 패턴을 보여주세요
```

```
완전한 TMS를 위해 Omelet의 라우팅과 iNavi의 지도를 어떻게 결합하나요?
```

</details>

<details>
<summary><b>🐛 디버깅 & 스키마 검증</b></summary>

```
VRP 엔드포인트에서 400 오류가 발생합니다. 요청 스키마를 보여주세요
```

```
cost-matrix API의 예상 응답 형식은 무엇인가요?
```

```
Advanced VRP 엔드포인트에 대한 유효한 요청 본문 예제를 보여주세요
```

```
route-time 엔드포인트가 반환할 수 있는 응답 코드는 무엇인가요?
```

</details>

---

## 🛠️ 개발

### 설정

서버에 기여하거나 커스터마이징하려면:

1. **[uv](https://docs.astral.sh/uv/getting-started/installation/) 설치**

2. **리포지토리 클론 및 개발 환경 설정:**
   ```bash
   git clone https://github.com/omelet-ai/tms-dev-mcp.git
   cd tms-dev-mcp
   uv sync --all-groups
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   ```

3. **pre-commit 훅 설치:**
   ```bash
   pre-commit install
   ```

4. **(선택사항) 환경 변수 설정:**
   ```bash
   cp env.example .env
   # .env 파일을 설정에 맞게 편집
   ```

---

### 로컬 설치

MCP 클라이언트가 로컬 MCP 서버에 연결하도록 구성합니다. `/path/to/tms-dev-mcp`를 실제 설치 경로로 바꾸세요.

<details>
<summary><b>Cursor / Claude Desktop</b></summary>

MCP 설정으로 이동하여 다음을 추가하세요:

```json
{
   "mcpServers": {
      "TMS Development Wizard": {
         "command": "/path/to/tms-dev-mcp/.venv/bin/python",
         "args": [
            "/path/to/tms-dev-mcp/tms_mcp/main.py",
            "start-server"
         ]
      }
   }
}
```

</details>

<details>
<summary><b>Claude Code</b></summary>

프로젝트 루트에서 터미널을 열고 실행:

```bash
claude mcp add TMS-Development-Wizard /path/to/tms-dev-mcp/.venv/bin/python /path/to/tms-dev-mcp/tms_mcp/main.py start-server
```

</details>

<details>
<summary><b>Codex CLI</b></summary>

프로젝트 루트에서 터미널을 열고 실행:

```bash
codex mcp add TMS-Development-Wizard /path/to/tms-dev-mcp/.venv/bin/python /path/to/tms-dev-mcp/tms_mcp/main.py start-server
```

</details>

<details>
<summary><b>Gemini CLI</b></summary>

프로젝트 루트에서 터미널을 열고 실행:

```bash
gemini mcp add TMS-Development-Wizard /path/to/tms-dev-mcp/.venv/bin/python /path/to/tms-dev-mcp/tms_mcp/main.py start-server
```

</details>

---

### 현재 구현된 도구

현재 구현된 도구들의 개요입니다:

| 도구 | 설명 |
|------|------|
| `get_basic_info()` | Omelet Routing Engine과 iNavi Maps API 모두에 대한 개요 정보 가져오기 |
| `list_endpoints(provider)` | 사용 가능한 모든 API 엔드포인트 나열, 선택적으로 프로바이더(`omelet`/`inavi`)로 필터링 |
| `list_integration_patterns()` | 설명이 포함된 통합 패턴 카탈로그 탐색 |
| `get_integration_pattern(pattern_id, simple)` | 에이전틱 코딩 가이드라인이 포함된 특정 통합 플레이북 검색 |
| `get_endpoint_overview(path, provider)` | 특정 API 엔드포인트에 대한 상세 개요 가져오기 |
| `get_request_body_schema(path, provider)` | 엔드포인트의 요청 본문 스키마 가져오기 |
| `get_response_schema(path, response_code, provider)` | 엔드포인트와 상태 코드에 대한 응답 스키마 가져오기 |
| `list_examples(path, example_type, provider)` | 엔드포인트의 사용 가능한 요청/응답 예제 나열 |
| `get_example(path, example_name, example_type, response_code, provider)` | 엔드포인트의 특정 예제 가져오기 |


---

### 프로젝트 구조

```
tms_mcp/
├── server.py              # FastMCP 서버 인스턴스
├── main.py                # CLI를 포함한 진입점
├── config.py              # 구성 관리
├── pipeline/
│   ├── pipeline.py        # 문서 인덱싱 파이프라인
│   ├── models.py          # 데이터 모델
│   ├── utils.py           # 유틸리티 함수
│   ├── generators/        # 문서 생성기
│   └── templates/         # 문서 템플릿
├── tools/
│   └── doc_tools.py       # 문서 쿼리를 위한 MCP 도구
└── docs/                  # 생성된 문서
    ├── basic_info.md      # 공유 API 개요
    ├── integration_patterns/  # 통합 패턴 및 가이드라인
    ├── omelet/            # Omelet 전용 문서
    │   ├── openapi.json
    │   ├── endpoints_summary.md
    │   ├── overviews/
    │   ├── schemas/
    │   └── examples/
    └── inavi/             # iNavi 전용 문서
        ├── openapi.json
        ├── endpoints_summary.md
        ├── overviews/
        └── schemas/
```

(간결성을 위해 일부 폴더/파일은 생략됨)
---

### 문서 생성 파이프라인

파이프라인은 OpenAPI 사양을 자동으로 처리하고 구조화된 문서를 생성합니다:

1. **가져오기(Fetch)** - 구성된 URL에서 OpenAPI 스펙 다운로드
2. **해결(Resolve)** - jsonref를 사용하여 완전한 스키마를 위해 모든 `$ref` 참조 해결
3. **분할(Split)** - 프로바이더별(Omelet/iNavi)로 문서 분리
4. **생성(Generate)** - 템플릿에서 통합 패턴과 가이드라인 생성
5. **구조화(Structure)** - 프로바이더별 문서 생성:
   - 요청/응답 스키마
   - 엔드포인트 요약 및 상세 개요
   - OpenAPI 스펙에서 추출한 요청/응답 예제
6. **배포(Deploy)** - 일관성을 보장하기 위해 이전 문서를 원자적으로 교체

---

### 문서 업데이트

`update_docs.sh`로 최신 OpenAPI 스펙을 반영하세요:

```bash
cd scripts

# 모든 프로바이더 업데이트
./update_docs.sh

# Omelet 프로바이더만 업데이트
./update_docs.sh omelet

# iNavi 프로바이더만 업데이트
./update_docs.sh inavi

# 여러 프로바이더 업데이트
./update_docs.sh omelet inavi

# 사용법 정보 표시
./update_docs.sh --help
```

---

### 기여하기

1. **리포지토리 포크**
2. **브랜치 생성** (`git checkout -b feature/amazing-feature`)
3. **변경사항 작성** (`pre-commit` 훅 실행을 잊지 마세요)
4. **변경사항 커밋** (`git commit -m 'Add amazing feature'`)
5. **브랜치로 푸시** (`git push origin feature/amazing-feature`)
6. **Pull Request 오픈**

코드가 다음을 충족하는지 확인하세요:
- 모든 pre-commit 훅 통과 (ruff, mypy 등)
- 적절한 테스트 포함
- 기존 코드 스타일 준수
- 명확한 커밋 메시지 포함

---

## 📄 라이선스

이 프로젝트는 MIT 라이선스에 따라 라이선스가 부여됩니다.

---

<div align="center">

**[⬆ 맨 위로](#tms-development-wizard-mcp-server)**

</div>
