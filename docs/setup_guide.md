# StockSage AI 설치 및 설정 가이드

이 가이드는 StockSage AI를 설치하고 설정하는 방법을 단계별로 안내합니다.

## 1. 사전 요구사항

- Python 3.10 이상
- [uv](https://github.com/astral-sh/uv) 패키지 관리자
- Anthropic API 키
- Windows, macOS 또는 Linux 운영 체제

## 2. 설치 절차

### 2.1 저장소 클론

```bash
git clone https://github.com/yourusername/stocksage-ai.git
cd stocksage-ai
```

### 2.2 가상 환경 생성 및 활성화

**macOS/Linux:**

```bash
uv venv
source .venv/bin/activate
```

**Windows:**

```cmd
uv venv
.venv\Scripts\activate
```

### 2.3 의존성 설치

```bash
uv pip install -r requirements.txt
```

### 2.4 환경 변수 설정

1. 템플릿 파일 복사:

```bash
cp .env.template .env
```

2. `.env` 파일을 텍스트 편집기로 열고 필요한 API 키 등을 설정:

```
ANTHROPIC_API_KEY=your_api_key_here
```

### 2.5 MCP 서버 도구 설치

다음 명령을 통해 필요한 MCP 서버 도구를 설치합니다:

```bash
uvx install mcp-server-sequential-thinking
uvx install mcp-server-think
uvx install mcp-server-fetch
```

## 3. 설정 디렉토리 생성

설정 파일을 저장할 디렉토리를 생성합니다:

```bash
mkdir -p config
```

## 4. 애플리케이션 실행

```bash
streamlit run app.py
```

이 명령은 로컬 서버를 시작하며, 자동으로 브라우저가 열리면서 http://localhost:8501 주소로 접속됩니다.

## 5. 문제 해결

### 5.1 의존성 충돌

만약 패키지 의존성 충돌이 발생하면 다음 명령으로 가상 환경을 재생성해보세요:

```bash
deactivate  # 기존 가상 환경 비활성화
rm -rf .venv  # 가상 환경 삭제
uv venv  # 새 가상 환경 생성
source .venv/bin/activate  # 가상 환경 활성화
uv pip install -r requirements.txt  # 의존성 재설치
```

### 5.2 MCP 서버 문제

MCP 서버 관련 오류가 발생하면 다음 사항을 확인하세요:

1. `mcp_servers` 디렉토리가 존재하고, 해당 디렉토리 내에 `mcp_server_config.json` 파일이 있는지 확인
2. MCP 도구가 올바르게 설치되었는지 확인:
   ```bash
   uvx list | grep mcp-server
   ```
3. 설정 파일의 경로가 올바른지 확인

### 5.3 API 키 문제

API 키 관련 오류가 발생하면 다음을 확인하세요:

1. `.env` 파일이 프로젝트 루트 디렉토리에 존재하는지 확인
2. API 키 형식이 올바른지 확인
3. 환경 변수가 로드되는지 확인:
   ```python
   import os
   print(os.environ.get("ANTHROPIC_API_KEY"))
   ```

## 6. 고급 설정

### 6.1 커스텀 MCP 서버 추가

추가 MCP 서버를 사용하려면 `mcp_servers/mcp_server_config.json` 파일을 편집하세요:

```json
{
  "custom_server": {
    "command": "python",
    "args": ["path/to/your/server.py"],
    "transport": "stdio"
  }
}
```

### 6.2 앱 설정 사용자 정의

`config/app_config.json` 파일을 만들어 앱 동작을 사용자 정의할 수 있습니다:

```json
{
  "theme": "light",
  "default_market": "US",
  "mcp_timeout": 60,
  "max_history_size": 100,
  "default_model": "claude-3-7-sonnet-latest"
}
```

## 7. 업데이트 방법

저장소의 최신 변경 사항을 가져오려면:

```bash
git pull origin main
uv pip install -r requirements.txt  # 새로운 의존성 설치
```

## 8. 백업 및 복원

### 8.1 설정 백업

사용자 설정을 백업하려면:

```bash
cp config/user_config.json config/user_config_backup.json
```

### 8.2 설정 복원

백업에서 설정을 복원하려면:

```bash
cp config/user_config_backup.json config/user_config.json
```

## 9. 추가 도움말

더 자세한 정보는 [공식 문서](https://github.com/yourusername/stocksage-ai)를 참조하거나, 이슈 트래커를 통해 질문하세요.
