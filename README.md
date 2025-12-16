# FARA-7B Agent Project

> Microsoft FARA-7B 모델을 사용한 로컬 브라우저 자동화 에이전트
> **핵심 가치**: vLLM만 지원하던 Magentic-UI를 **LM Studio에서도 작동**하도록 구현
> 두 가지 구현 방식 제공: **Playwright Agent** (독립 실행형) + **Magentic-UI Agent** (통합 프레임워크)

## 목차

- [프로젝트 개요](#프로젝트-개요)
- [주요 특징](#주요-특징)
- [시작하기](#시작하기)
  - [필수 조건](#필수-조건)
  - [LM Studio 설정](#lm-studio-설정)
- [사용 방법](#사용-방법)
  - [Playwright Agent](#playwright-agent)
  - [Magentic-UI Agent](#magentic-ui-agent)
- [프로젝트 구조](#프로젝트-구조)
- [문서](#문서)
- [문제 해결 과정 (참고)](#문제-해결-과정-참고)
- [제약사항](#제약사항)
- [트러블슈팅](#트러블슈팅)
- [라이선스](#라이선스)

## 프로젝트 개요

이 프로젝트는 **Microsoft FARA-7B** (7B parameter agentic model)를 사용하여 웹 브라우저를 자동화하는 두 가지 구현을 제공합니다:

1. **Playwright Agent**: CLI 기반의 빠르고 간단한 독립 실행형 에이전트
2. **Magentic-UI Agent**: 웹 UI를 통한 사용자 승인 기반 통합 프레임워크

### 핵심 특징

- 100% 로컬 실행 (LM Studio 사용)
- Vision-centric 접근 (스크린샷 기반 제어)
- OpenAI API 호환
- DOM/Accessibility tree 불필요
- GPU 최적화 (quantized 모델 지원)

## 주요 특징

| 항목 | Playwright Agent | Magentic-UI Agent |
|------|------------------|-------------------|
| **실행 방식** | CLI (터미널) | 웹 UI (localhost:8081) |
| **속도** | 빠름 | 보통 (오케스트레이션 오버헤드) |
| **사용자 승인** | 없음 (자동 실행) | Co-planning (실행 전 승인) |
| **안전성** | 낮음 | 높음 (Action guards) |
| **적합 사용** | 반복 자동화, 스크립트 | 복잡한 작업, 대화형 계획 |
| **Live View** | 없음 | Docker 브라우저 (VNC) |

## 시작하기

### 필수 조건

- **Python 3.11+**
- **LM Studio** ([다운로드](https://lmstudio.ai/))
- **FARA-7B 모델** (LM Studio에서 다운로드)
- **Playwright** (브라우저 자동화)
- **(Magentic-UI 사용 시) Docker** (Live View용)

### LM Studio 설정

1. LM Studio 실행
2. FARA-7B 모델 다운로드 및 로드
   - 모델 이름: `microsoft/Fara-7B` 또는 `microsoft_fara-7b`
3. Local Server 시작
   - 포트: `1234` (기본값)
   - **중요**: max_token을 **15000**으로 설정 (Vision 요청용)
4. 서버 확인:
   ```bash
   curl http://127.0.0.1:1234/v1/models
   ```

## 사용 방법

### Playwright Agent

빠른 CLI 기반 실행형 에이전트. 자동화 스크립트에 적합.

#### 설치

```bash
cd playwright-agent
pip install -r requirements.txt
python -m playwright install chromium
```

#### 실행

```bash
# 기본 실행 (헤드리스 모드)
python run_agent.py --task "Go to GitHub and search for 'playwright'"

# 브라우저 GUI 표시 (디버깅용)
python run_agent.py --task "Go to GitHub and search for 'playwright'" --headful

# 작업 완료 후 브라우저 유지
python run_agent.py --task "작업 내용" --headful --keep-open
```

#### 설정

`playwright-agent/config.json`:
```json
{
  "model": "microsoft_fara-7b",
  "base_url": "http://127.0.0.1:1234/v1",
  "api_key": "lm-studio",
  "max_rounds": 20,
  "max_n_images": 1,
  "temperature": 0.0
}
```

#### 사용 예제

1. **GitHub 검색**
   ```bash
   python run_agent.py --task "Go to GitHub and search for 'fastapi'" --headful
   ```

2. **Wikipedia 탐색**
   ```bash
   python run_agent.py --task "Go to Wikipedia and search for 'Python programming', click the article" --headful --keep-open
   ```

3. **Google 검색 후 결과 클릭**
   ```bash
   python run_agent.py --task "Go to Google and search for 'machine learning tutorial', click the first result"
   ```

자세한 예제는 [사용 가이드](./docs/USAGE_GUIDE.md) 참조.

### Magentic-UI Agent

웹 UI 기반 에이전트. 사용자 승인 및 계획 기능 제공.

#### 설치

```bash
cd magentic-ui-agent
pip install -r requirements.txt
```

#### 실행

```bash
magentic-ui --fara --port 8081 --config fara_config.yaml
```

브라우저에서 **http://localhost:8081** 접속

#### 설정

`magentic-ui-agent/fara_config.yaml`:
```yaml
model_config_local_surfer: &client_surfer
  provider: OpenAIChatCompletionClient
  config:
    model: "microsoft_fara-7b"
    base_url: http://127.0.0.1:1234/v1
    api_key: lm-studio
    model_info:
      vision: true
      function_calling: true
```

**주요 변경 사항**:
- `/opt/homebrew/lib/python3.11/site-packages/magentic_ui/agents/web_surfer/fara/_fara_web_surfer.py`:
  - Line 64: `model_call_timeout: int = 60` (기존 20초 → 60초)
  - Vision 처리 시간 확보용

## 프로젝트 구조

```
fara-agent-main/
├── README.md                      # 이 파일
├── LICENSE                        # MIT 라이선스
├── .gitignore                     # Git 설정
│
├── playwright-agent/              # Playwright 기반 독립 에이전트
│   ├── agent.py                   # FaraAgent 클래스 (메인 로직)
│   ├── browser.py                 # SimpleBrowser 클래스 (Playwright 래퍼)
│   ├── run_agent.py               # CLI 엔트리 포인트
│   ├── message_types.py           # LLM 메시지 데이터 구조
│   ├── prompts.py                 # 시스템 프롬프트 생성
│   ├── utils.py                   # URL 유틸리티
│   ├── config.json                # 에이전트 설정
│   ├── requirements.txt           # Python 의존성
│   ├── README.md                  # Playwright Agent 문서
│   └── downloads/                 # 다운로드 파일 저장
│
├── magentic-ui-agent/             # Magentic-UI 통합
│   ├── fara_config.yaml           # Magentic-UI 설정 (최종 작동 버전)
│   ├── requirements.txt           # Python 의존성
│   └── README.md                  # Magentic-UI Agent 문서
│
└── docs/                                      # 상세 문서
    ├── USAGE_GUIDE_MAGENTIC_UI.md            # Magentic-UI 사용 가이드 (LM Studio 연동)
    ├── USAGE_GUIDE.md                        # Playwright CLI 사용 가이드
    ├── FARA_Capability_분석_보고서.md         # Capability 분석 (Playwright 기준)
    └── FARA_설정_분석_보고서.md               # 설정 분석 (참고 문서)
```

## 문서

### 사용 가이드

- **[Magentic-UI 사용 가이드 (LM Studio 연동)](./docs/USAGE_GUIDE_MAGENTIC_UI.md)** ⭐ 권장
  - **프로젝트 핵심**: vLLM만 지원하던 Magentic-UI를 LM Studio에서 작동시키는 방법
  - LM Studio vs vLLM 비교
  - 문제 해결 과정 상세 (blank screenshot, timeout, proxy)
  - 웹 UI 기반 사용법

- **[Playwright CLI 사용 가이드](./docs/USAGE_GUIDE.md)**
  - CLI 기반 빠른 실행
  - 10가지 실전 예제
  - 트러블슈팅

### 참고 문서

- **[FARA Capability 분석 보고서](./docs/FARA_Capability_분석_보고서.md)** (Playwright CLI 기준)
  - FARA-7B 모델 capability 분석
  - 지원되는 11개 액션 목록
  - Vision-only 제약사항 상세

- **[FARA 설정 분석 보고서](./docs/FARA_설정_분석_보고서.md)** (참고 문서, Playwright CLI 기준)
  - LM Studio vs vLLM 설정 비교
  - Magentic-UI 상세 설정 분석
  - 성능 튜닝 가이드

### 참고 자료

- [FARA-7B 논문 (ArXiv)](https://arxiv.org/abs/2511.19663)
- [FARA-7B HuggingFace](https://huggingface.co/microsoft/Fara-7B)
- [Magentic-UI GitHub](https://github.com/microsoft/magentic-ui)
- [LM Studio 문서](https://lmstudio.ai/docs)

## 문제 해결 과정 (참고)

> **참고**: 이 섹션은 프로젝트 개발 중 겪었던 시행착오를 기록한 것입니다.
> 현재는 모두 해결되었으며, 자세한 내용은 [Magentic-UI 사용 가이드](./docs/USAGE_GUIDE_MAGENTIC_UI.md)를 참조하세요.

이 프로젝트 개발 중 해결한 주요 문제들:

### 1. Blank Screenshot 이슈
**증상**: 모델이 스크린샷을 보지 못하고 "blank image"라고 응답
**원인**: LM Studio의 max_token이 4000으로 제한되어 이미지 데이터 truncate
**해결**: LM Studio max_token을 **15000**으로 증가

### 2. Client Disconnected 메시지
**증상**: Vision 요청 중 "Client disconnected" 메시지 반복
**원인**: `model_call_timeout: int = 20` (20초)이 Vision 처리 시간(15-20초)보다 짧음
**해결**: `_fara_web_surfer.py`의 `model_call_timeout`을 **60초**로 증가

### 3. Proxy 불필요
**시도**: Tool calling을 위한 middleware proxy 구현
**결론**: Magentic-UI FARA 에이전트가 `<tool_call>` XML 형식을 직접 파싱
**해결**: LM Studio에 직접 연결 (proxy 제거)

## 제약사항 및 활용 범위

FARA-7B는 Vision 기반 접근 방식을 사용합니다. **실행 환경에 따라 활용 범위가 다릅니다**:

### Magentic-UI 환경 (권장)

**가능한 작업**:
- **웹 네비게이션**: 웹사이트 방문, 클릭, 스크롤, 다중 페이지 작업
- **정보 수집/요약**: 웹 페이지 내용 읽기 및 요약 (Vision 기반)
- **폼 작성**: 텍스트 입력, 버튼 클릭, 드롭다운 선택
- **복잡한 작업**: Multi-agent 협업, 사용자 승인 기반 실행 (Co-planning)
- **세션 관리**: 작업 이력 유지, Live View (Docker VNC)

### Playwright CLI 환경

**가능한 작업**:
- **웹 네비게이션**: 웹사이트 방문, 클릭, 스크롤
- **폼 작성**: 텍스트 입력, 버튼 클릭
- **검색**: 검색어 입력 및 결과 클릭
- **시각적 확인**: 페이지 도달 여부, 레이아웃 확인
- **반복 자동화**: 정형화된 웹 작업 반복 실행

**제한 사항** (Playwright CLI 구현 한계):
- 간소화된 데모 버전으로 multi-turn/세션 관리 미지원
- 구조화된 데이터 추출 기능 미구현

자세한 내용은 [FARA Capability 분석 보고서](./docs/FARA_Capability_분석_보고서.md) (Playwright CLI 기준) 참조.

## 트러블슈팅

### LM Studio 연결 실패

```bash
# 서버 상태 확인
curl http://127.0.0.1:1234/v1/models

# 응답이 없으면:
# 1. LM Studio 실행 확인
# 2. Local Server 시작 (포트 1234)
# 3. FARA-7B 모델 로드 확인
```

### Playwright 브라우저 오류

```bash
# Playwright Chromium 재설치
python -m playwright install chromium

# 권한 문제 시
sudo python -m playwright install chromium
```

### Magentic-UI Docker 이미지 문제

```bash
# Docker 상태 확인
docker ps

# Magentic-UI 재시작
# Ctrl+C로 종료 후 다시 실행
magentic-ui --fara --port 8081 --config fara_config.yaml
```

더 많은 문제 해결 방법은 [사용 가이드](./docs/USAGE_GUIDE.md) 및 [Magentic-UI 사용 가이드](./docs/USAGE_GUIDE_MAGENTIC_UI.md) 참조.

## 라이선스

이 프로젝트는 다음 오픈소스 프로젝트들의 라이선스를 준용합니다:

- **FARA-7B Model**: [MIT License](https://huggingface.co/microsoft/Fara-7B) (Microsoft)
- **Magentic-UI**: [MIT License](https://github.com/microsoft/magentic-ui) (Microsoft)
- **Playwright**: [Apache License 2.0](https://github.com/microsoft/playwright) (Microsoft)

### 이 프로젝트의 코드

MIT License

Copyright (c) 2025

본 소프트웨어 및 관련 문서 파일(이하 "소프트웨어")의 복사본을 취득하는 모든 사람에게 무료로 사용, 복사, 수정, 병합, 게시, 배포, 재라이선스 및 판매할 수 있는 권한을 제한 없이 부여합니다.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

---

**프로젝트 생성**: 2025-12-15
**최종 수정**: 2025-12-15

### 참고

공식 Microsoft FARA 프로젝트: [github.com/microsoft/fara](https://github.com/microsoft/fara)
