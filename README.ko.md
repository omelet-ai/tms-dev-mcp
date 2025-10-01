# TMS Development MCP Server

[![English](https://img.shields.io/badge/lang-English-blue.svg)](README.md) [![한국어](https://img.shields.io/badge/언어-한국어-orange.svg)](README.ko.md)

FastMCP 기반 MCP 서버로, **Omelet Routing Engine API**와 **iNavi Maps API** 문서를 지능적으로 탐색하여 효과적인 운송관리시스템(TMS)을 구축할 수 있도록 돕습니다.

## 주요 기능

- 🚀 **멀티 프로바이더 지원**: Omelet과 iNavi API 문서를 통합된 도구로 손쉽게 열람
- 📚 **스마트 문서 관리**: 프로바이더를 자동 인식하는 지능형 문서 조회 도구 제공
- 🎯 **프로바이더 필터링**: 특정 프로바이더만 조회하거나 통합 조회 지원
- 🧩 **통합 플레이북**: 대표적인 TMS 워크플로우를 빠르게 시작할 수 있는 통합 패턴과 가이드 제공

API 키는 [Omelet Routing Engine 홈페이지](https://routing.oaasis.cc/)와 [iNavi iMPS 홈페이지](https://mapsapi.inavisys.com/)에서 발급받을 수 있습니다.
(이 MCP 서버를 실행하는 데에는 API 키가 필수는 아닙니다.)

## 빠른 시작

### 사전 준비

시작하기 전에 시스템에 [uv](https://docs.astral.sh/uv/getting-started/installation/)가 설치되어 있어야 합니다.

### 설치

1. 저장소 클론:
```bash
git clone https://github.com/omelet-ai/tms-dev-mcp.git
cd tms-dev-mcp
```

2. 가상환경 생성 및 활성화:
```bash
uv sync --all-groups
source .venv/bin/activate  # Windows: .venv\Scripts\activate
```

3. (선택) 환경 변수 설정:
```bash
cp env.example .env
# .env 파일을 열어 환경설정을 수정하세요
```

4. (선택) 서버 개발용 pre-commit 설치:
```bash
pre-commit install
```

### 서버 실행 (로컬)

#### Cursor / Claude Desktop 설정 예시
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

#### Claude Code
프로젝트 루트 디렉터리에서 터미널을 열고 다음 명령을 실행하세요:
```bash
claude mcp add TMS-Development-Wizard /path/to/tms-dev-mcp/.venv/bin/python /path/to/tms-dev-mcp/tms_mcp/main.py start-server
```

#### Codex CLI
프로젝트 루트 디렉터리에서 터미널을 열고 다음 명령을 실행하세요:
```bash
codex mcp add TMS-Development-Wizard /path/to/tms-dev-mcp/.venv/bin/python /path/to/tms-dev-mcp/tms_mcp/main.py start-server
```

#### Gemini CLI
프로젝트 루트 디렉터리에서 터미널을 열고 다음 명령을 실행하세요:
```bash
gemini mcp add TMS-Development-Wizard /path/to/tms-dev-mcp/.venv/bin/python /path/to/tms-dev-mcp/tms_mcp/main.py start-server
```

## 프로젝트 구조

```
tms_mcp/
├── server.py              # FastMCP 서버 인스턴스
├── main.py                # CLI 엔트리 포인트
├── config.py              # 설정 관리
├── pipeline/
│   └── pipeline.py        # 문서 인덱싱 파이프라인
├── tools/
│   └── doc_tools.py       # 문서 조회 도구
└── docs/                  # 생성된 문서
    ├── basic_info.md      # 공통 API 개요
    ├── integration_patterns/ # 통합 패턴 및 에이전틱 가이드라인
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

(일부 폴더/파일은 간략화를 위해 생략되었습니다)

## 제공 도구

- `get_basic_info()`: Omelet Routing Engine 및 iNavi Maps API의 기본 정보를 조회
- `list_endpoints(provider)`: 프로바이더(omelet/inavi)로 엔드포인트 목록 필터링 조회
- `list_integration_patterns()`: 통합 패턴 카탈로그와 간단한 설명을 조회
- `get_integration_pattern(pattern_id, simple=False)`: 특정 통합 플레이북을 가져오며, `simple=True`가 아니면 에이전틱 가이드를 함께 제공
- `get_endpoint_overview(path, provider)`: 특정 엔드포인트의 상세 개요 조회
- `get_request_body_schema(path, provider)`: 특정 엔드포인트의 요청 본문 스키마 조회
- `get_response_schema(path, response_code, provider)`: 특정 엔드포인트와 응답코드에 대한 응답 스키마 조회
- `list_examples(path, example_type, provider)`: 특정 엔드포인트의 사용 가능한 요청 및 응답 예제 목록 조회
- `get_example(path, example_name, example_type, response_code, provider)`: 특정 엔드포인트의 예제 조회

## 문서 생성 파이프라인

파이프라인은 다음을 자동으로 수행합니다:
1. 설정된 URL에서 OpenAPI 스펙을 가져옵니다
2. jsonref를 사용하여 모든 `$ref` 참조를 해석합니다
3. 프로바이더별로 문서를 분리합니다 (Omelet/iNavi)
4. 템플릿 기반으로 통합 패턴 플레이북과 공통 에이전틱 가이드를 생성합니다
5. 프로바이더 전용 문서 구조를 생성합니다:
   - 요청/응답 스키마
   - OpenAPI 스펙에서 추출한 요청/응답 예제
   - 엔드포인트 요약 및 개요
6. 일관성을 보장하기 위해 이전 문서를 원자적으로 교체합니다

### 문서 업데이트

`update_docs.sh` 스크립트를 사용하여 OpenAPI 문서를 업데이트합니다:

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
