# TMS Development MCP Server

[![English](https://img.shields.io/badge/lang-English-blue.svg)](README.md) [![한국어](https://img.shields.io/badge/언어-한국어-orange.svg)](README.ko.md)

FastMCP 기반 MCP 서버로, **Omelet Routing Engine API**와 **iNavi Maps API** 문서를 지능적으로 탐색하여 효과적인 운송관리시스템(TMS)을 구축할 수 있도록 돕습니다.

## 주요 기능

- 🚀 **멀티 프로바이더 지원**: Omelet과 iNavi API 문서를 통합된 도구로 손쉽게 열람
- 📚 **스마트 문서 탐색**: 프로바이더를 자동 인식하는 지능형 도구 제공
- 🔄 **자동 예제 생성**: LLM 기반 요청 본문 예제 생성 및 API 스키마 유효성 검사
- 🎯 **프로바이더 필터링**: 특정 프로바이더만 조회하거나 통합 조회 지원

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

3. 환경변수 설정:
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
      "tms-dev": {
         "command": "/path/to/tms-dev-mcp/.venv/bin/python",
         "args": [
            "/path/to/tms-dev-mcp/tms_mcp/main.py",
            "start-server"
         ]
      }
   }
}
```

## 프로젝트 구조

```
tms_mcp/
├── server.py              # FastMCP 서버 인스턴스
├── main.py                # CLI 엔트리 포인트
├── config.py              # 설정 관리
├── pipeline/
│   ├── pipeline.py        # 문서 인덱싱 파이프라인
│   └── graph.py           # LLM 기반 예제 생성
├── tools/
│   └── doc_tools.py       # 문서 조회 도구
└── docs/                  # 생성된 문서
    ├── basic_info.md      # 공통 API 개요
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
- `get_endpoint_overview(path, provider)`: 특정 엔드포인트의 상세 개요 조회
- `get_request_body_schema(path, provider)`: 특정 엔드포인트의 요청 본문 스키마 조회
- `get_request_body_example(path, provider)`: 특정 엔드포인트의 요청 본문 예제 조회
- `get_response_schema(path, response_code, provider)`: 특정 엔드포인트와 응답코드에 대한 응답 스키마 조회

## 문서 생성 파이프라인

파이프라인은 다음을 자동으로 수행합니다:
1. 설정된 URL에서 OpenAPI 스펙을 가져옵니다
2. 모든 `$ref` 참조를 해석합니다
3. 프로바이더별로 문서를 분리합니다
4. 프로바이더 전용 문서 구조를 생성합니다
5. LLM 기반 예제를 생성합니다 (Omelet 전용)
6. 실제 API에 대해 예제를 유효성 검사합니다

### 문서 업데이트

```bash
cd scripts
bash update_docs.sh
```
또는
```bash
python -m tms_mcp.main update-docs
```
