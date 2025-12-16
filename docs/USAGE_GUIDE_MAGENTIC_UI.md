# FARA-7B with Magentic-UI 사용 가이드 (LM Studio 연동)

> **프로젝트 핵심 가치**: Microsoft FARA-7B 모델의 최적 환경인 Magentic-UI가 공식적으로는 **vLLM만 지원**하지만,
> 이 프로젝트는 **LM Studio 환경에서도 동작하도록 구현**하여 로컬 GPU 환경에서 손쉽게 사용할 수 있게 합니다.

## 📋 목차

- [개요](#개요)
- [왜 LM Studio인가?](#왜-lm-studio인가)
- [시스템 요구사항](#시스템-요구사항)
- [설치 가이드](#설치-가이드)
- [LM Studio 설정](#lm-studio-설정)
- [Magentic-UI 실행](#magentic-ui-실행)
- [사용 방법](#사용-방법)
- [문제 해결 과정 (핵심)](#문제-해결-과정-핵심)
- [vLLM vs LM Studio 비교](#vllm-vs-lm-studio-비교)
- [트러블슈팅](#트러블슈팅)

---

## 개요

### 프로젝트 배경

Microsoft에서 FARA-7B 모델 발표 시, 최적의 실행 환경으로 **Magentic-UI 프레임워크**를 제시했습니다.
그러나 공식 문서는 **vLLM 환경만 가이드**를 제공하며, 다음과 같은 제약이 있었습니다:

#### 공식 가이드의 제약사항
- ❌ vLLM은 **Linux/WSL2 환경 필수** (macOS/Windows 네이티브 미지원)
- ❌ GPU 메모리 요구량이 높음 (최소 24GB VRAM)
- ❌ 설정이 복잡하고 초기 진입 장벽이 높음
- ❌ 개발/테스트 환경으로 부담스러움

#### 이 프로젝트의 솔루션
- ✅ **LM Studio**를 사용하여 Windows/macOS에서 바로 실행
- ✅ GUI 기반으로 모델 관리가 간편
- ✅ Quantized 모델 지원 (4-bit, 8-bit)으로 메모리 절약
- ✅ Magentic-UI와 완벽 호환되도록 구현

### Magentic-UI의 장점

| 기능 | Playwright CLI | Magentic-UI |
|------|---------------|-------------|
| **웹 UI** | ❌ | ✅ localhost:8081 |
| **사용자 승인** | ❌ | ✅ Co-planning |
| **Live View** | ❌ | ✅ Docker VNC |
| **작업 이력** | ❌ | ✅ 세션 관리 |
| **안전성** | 낮음 | ✅ Action guards |
| **복잡한 작업** | 제한적 | ✅ 오케스트레이션 |

---

## 왜 LM Studio인가?

### LM Studio의 장점

1. **크로스 플랫폼**
   - Windows, macOS, Linux 모두 지원
   - 별도의 가상화 환경 불필요

2. **사용 편의성**
   - GUI 기반 모델 다운로드 및 관리
   - 원클릭으로 서버 시작/중지
   - 실시간 로그 확인

3. **모델 최적화**
   - Quantized 모델 자동 지원 (GGUF)
   - 메모리 사용량 절감 (4-bit: ~4GB, 8-bit: ~8GB)
   - Apple Silicon Metal / NVIDIA CUDA GPU 가속 지원

4. **OpenAI API 호환**
   - `/v1/chat/completions` 엔드포인트 제공
   - Magentic-UI의 `OpenAIChatCompletionClient`와 바로 연동

5. **개발 친화적**
   - 빠른 재시작 및 모델 교체
   - 로컬 환경에서 안전한 테스트
   - 비용 없음 (완전 무료)

### vLLM vs LM Studio 선택 기준

| 상황 | 권장 환경 |
|------|----------|
| 프로덕션 배포 (고성능 필요) | vLLM |
| 개발/테스트/데모 | **LM Studio** ⭐ |
| macOS (Apple Silicon) 사용자 | **LM Studio** ⭐ |
| Windows 네이티브 | **LM Studio** ⭐ |
| Linux + 대용량 NVIDIA GPU (48GB+) | vLLM |
| NVIDIA GPU 없는 환경 | **LM Studio** ⭐ |

---

## 시스템 요구사항

### 최소 사양
- **OS**: Windows 10+, macOS 12+, Linux
- **RAM**: 16GB
- **디스크**: 10GB 여유 공간
- **GPU**: NVIDIA GPU (권장, CPU도 가능)

### 권장 사양
- **RAM**: 32GB
- **GPU**: NVIDIA GPU 8GB+ VRAM
- **디스크**: SSD 20GB

### 소프트웨어
- Python 3.11+
- Docker Desktop (Live View 사용 시)
- LM Studio (최신 버전)

---

## 설치 가이드

### 1. LM Studio 설치

1. https://lmstudio.ai/ 에서 다운로드
2. 설치 및 실행

### 2. FARA-7B 모델 다운로드

LM Studio에서:
1. Search 탭에서 "Fara" 검색
2. `microsoft/Fara-7B` 선택
3. Quantization 선택:
   - **Q4_K_M** (권장, 4-bit, ~4GB)
   - **Q8_0** (고품질, 8-bit, ~8GB)
   - **F16** (최고품질, 16-bit, ~14GB)
4. Download

### 3. Magentic-UI 설치

```bash
cd /Users/gregyh/Coding/fara-agent-main/magentic-ui-agent

# 의존성 설치
pip install -r requirements.txt

# Magentic-UI 설치 (FARA 지원)
pip install magentic-ui[fara]
```

### 4. Docker 설치 (Live View용)

Live View 기능을 사용하려면 Docker Desktop 필요:
- https://www.docker.com/products/docker-desktop/

---

## LM Studio 설정

### 1. 모델 로드

1. LM Studio → **Local Server** 탭
2. **Select a model to load** → `microsoft/Fara-7B` 선택
3. **Load Model** 클릭

### 2. 서버 설정 ⭐ 중요

**Max Tokens 설정 (필수)**:
- **Default**: 4000
- **Vision 요청용**: **15000** ⭐
- **이유**: 1440x900 스크린샷 처리에 10,000+ 토큰 필요

**설정 방법**:
1. Server Options 확장
2. "Context Length" 또는 "Max Tokens" → **15000** 입력
3. Apply

**기타 권장 설정**:
- Temperature: `0.0` (일관된 결과)
- Port: `1234` (기본값)
- GPU Layers: Auto (또는 최대값)

### 3. 서버 시작

1. **Start Server** 클릭
2. 로그에서 확인:
   ```
   [LM STUDIO SERVER] Server started on port 1234
   ```

3. 테스트:
   ```bash
   curl http://127.0.0.1:1234/v1/models
   ```

---

## Magentic-UI 실행

### 설정 파일

`magentic-ui-agent/fara_config.yaml` (이미 설정됨):

```yaml
model_config_local_surfer: &client_surfer
  provider: OpenAIChatCompletionClient
  config:
    # LM Studio 직접 연결 (Proxy 불필요)
    model: "microsoft_fara-7b"
    base_url: http://127.0.0.1:1234/v1
    api_key: lm-studio

    # Vision 지원 설정
    model_info:
      vision: true
      function_calling: true
      json_output: false

# 모든 에이전트가 동일 설정 사용
orchestrator_client: *client_surfer
web_surfer_client: *client_surfer
action_guard_client: *client_surfer
```

**핵심 포인트**:
- `base_url`: LM Studio에 **직접 연결** (Proxy 미사용)
- `model`: LM Studio 형식 (`microsoft_fara-7b`)
- `vision: true`: Vision 기능 활성화

### 실행 명령어

```bash
cd /Users/gregyh/Coding/fara-agent-main/magentic-ui-agent

magentic-ui --fara --port 8081 --config fara_config.yaml
```

### 브라우저 접속

```
http://localhost:8081
```

---

## 사용 방법

### 1. 새 세션 생성

1. Magentic-UI 웹 UI 접속
2. **New Session** 클릭
3. 작업 내용 입력 (예: "Go to GitHub and search for 'playwright'")

### 2. Co-Planning 단계

- 에이전트가 작업 계획 생성
- 사용자가 **승인** 또는 **수정** 가능
- **Approve Plan** 클릭

### 3. 실행 단계

- 에이전트가 브라우저 자동화 실행
- **Live View**: Docker 브라우저 실시간 확인
- 진행 상황 로그 확인

### 4. 결과 확인

- 작업 완료 시 결과 요약
- 스크린샷 및 액션 이력 저장
- 세션은 계속 유지 (추가 작업 가능)

### 사용 예제

**예제 1: GitHub 검색**
```
Task: "Go to GitHub and search for 'magentic-ui', click on the first repository"
```

**예제 2: 정보 수집 및 요약**
```
Task: "Visit Hacker News and tell me the top 5 post titles"
```
Magentic-UI 환경에서는 Vision 기반으로 페이지 내용을 읽고 요약할 수 있습니다.

**예제 3: 폼 작성**
```
Task: "Go to example.com/contact and fill the form with name 'Test User' and email 'test@example.com'"
```

---

## 문제 해결 과정 (핵심)

이 섹션은 **vLLM 전용이던 Magentic-UI를 LM Studio에서 작동시키기 위한 시행착오**를 기록합니다.

### 문제 1: Blank Screenshot 이슈

#### 증상
```
Agent: "I can't help with this blank image"
Model response: "The screenshot is empty"
```
- 모델이 스크린샷을 전혀 보지 못함
- 프롬프트 텍스트만 보고 hallucination 응답

#### 시도한 해결책 (실패)
1. **AGImage.resize() 메서드 확인**
   - autogen_core의 Image 클래스 조사
   - resize 메서드는 정상 작동 확인

2. **Screenshot 캡처 타이밍 조정**
   - `await asyncio.sleep(1.0)` 추가 (렌더링 대기)
   - `full_page=False` 설정
   - → **효과 없음**

3. **로컬 Playwright 테스트**
   ```python
   # debug_screenshot.py 작성
   screenshot_bytes = await page.screenshot()
   # Result: 28,851 bytes, 정상 캡처 확인
   ```
   - 스크린샷 자체는 정상

#### 실제 원인 발견 ⭐
```
LM Studio max_token = 4000
Vision 요청 필요 토큰 = 10,000+
→ 이미지 데이터가 truncate됨!
```

**Token 사용량 분석**:
- 1440x900 스크린샷 → ~10,000 tokens
- 프롬프트 + 컨텍스트 → ~1,500 tokens
- **총 필요**: ~11,500 tokens
- **LM Studio 설정**: 4,000 tokens
- **결과**: 이미지 데이터가 잘려서 blank

#### 최종 해결책
```
LM Studio max_token: 4000 → 15000
```
- 15,000 tokens로 증가
- **즉시 해결**
- 모델이 정상적으로 스크린샷 인식

**교훈**: Vision 모델은 기본 토큰 제한으로 작동하지 않음!

---

### 문제 2: Client Disconnected 반복

#### 증상
```
[LM STUDIO SERVER] Client disconnected. Stopping generation...
[LM STUDIO SERVER] Request completed in 25.3s
```
- Vision 요청 중 연결 끊김 메시지
- 작업은 계속되지만 비효율적

#### 원인 분석

**Prompt Processing 시간**:
```
Request start: 09:47:46
Prompt processing: 15-20초
Timeout trigger: 20초 (정확히 20초 후 disconnection)
```

**코드 확인**:
```python
# _fara_web_surfer.py:64
model_call_timeout: int = 20  # ← 20초
```

**문제**:
- Vision 요청의 프롬프트 처리에 15-20초 소요
- 20초 timeout이 너무 짧음
- Timeout 발생 → 재연결 → 재시도 → 비효율

#### 해결책

```python
# /opt/homebrew/lib/python3.11/site-packages/magentic_ui/agents/web_surfer/fara/_fara_web_surfer.py:64
model_call_timeout: int = 120  # 20 → 120초
```

**결과**:
- Client disconnected 메시지 사라짐
- 안정적인 Vision 요청 처리
- 성능 향상

---

### 문제 3: Proxy 불필요 발견

#### 초기 가정
```
LM Studio → XML <tool_call> 출력
→ Proxy middleware로 OpenAI format 변환 필요
```

#### 시도한 구현
```python
# fara_lmstudio_proxy.py
# XML → OpenAI Function Calling 변환
```

#### 실제 확인
```python
# Magentic-UI FARA agent 코드 확인
# → 자체적으로 <tool_call> XML 파싱 내장!
# Proxy가 오히려 충돌 유발
```

#### 최종 결론
```yaml
# Direct connection (No proxy)
base_url: http://127.0.0.1:1234/v1
```
- **Proxy 완전 제거**
- LM Studio → Magentic-UI 직접 연결
- 단순하고 안정적

---

## vLLM vs LM Studio 비교

### 성능 비교

| 항목 | vLLM | LM Studio |
|------|------|-----------|
| **추론 속도** | ⭐⭐⭐⭐⭐ (최고) | ⭐⭐⭐⭐ (우수) |
| **메모리 효율** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ (Quantized) |
| **GPU 지원** | NVIDIA CUDA only | NVIDIA CUDA, Apple Silicon Metal |
| **GPU 요구사항** | 24GB+ VRAM | 8GB+ VRAM |
| **설정 난이도** | ⭐ (어려움) | ⭐⭐⭐⭐⭐ (쉬움) |
| **크로스 플랫폼** | Linux only | Windows/macOS/Linux |
| **프로덕션 적합성** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| **개발 편의성** | ⭐⭐ | ⭐⭐⭐⭐⭐ |

### 사용 시나리오

**vLLM을 선택해야 하는 경우**:
- 대규모 프로덕션 배포
- 최고 성능 필요 (latency 최소화)
- Linux 서버 환경
- 대용량 GPU 사용 가능 (48GB+)

**LM Studio를 선택해야 하는 경우**:
- 개발/테스트/데모 환경 ⭐
- macOS 또는 Windows 사용
- GPU 메모리 제한 (8-16GB)
- 빠른 프로토타이핑
- 로컬 개인 사용

### 설정 비교

#### vLLM 설정 (복잡)
```bash
# 1. vLLM 설치 (Linux only)
pip install vllm

# 2. 모델 다운로드 (HuggingFace)
huggingface-cli download microsoft/Fara-7B

# 3. 서버 시작
vllm serve "microsoft/Fara-7B" \
  --port 5000 \
  --dtype auto \
  --gpu-memory-utilization 0.9 \
  --max-model-len 4096 \
  --tensor-parallel-size 2  # 멀티 GPU

# 4. Magentic-UI 설정
# base_url: http://localhost:5000/v1
```

#### LM Studio 설정 (간단) ⭐
```bash
# 1. LM Studio GUI에서 모델 다운로드 (원클릭)

# 2. Load Model 클릭

# 3. Start Server 클릭

# 4. Magentic-UI 설정
# base_url: http://127.0.0.1:1234/v1
```

---

## 트러블슈팅

### LM Studio 연결 실패

**증상**:
```
Connection refused to http://127.0.0.1:1234
```

**해결**:
1. LM Studio가 실행 중인지 확인
2. Local Server 탭에서 "Start Server" 클릭
3. 포트 1234가 사용 중이 아닌지 확인:
   ```bash
   lsof -i :1234
   ```
4. 방화벽 설정 확인

---

### Vision 요청 실패

**증상**:
```
Model response: "I cannot process this blank image"
```

**해결**:
1. **LM Studio max_token 확인** (가장 중요!)
   - Server Options → Max Tokens → **15000**

2. 모델이 Vision을 지원하는지 확인:
   ```bash
   # LM Studio에서 Fara-7B 로드 확인
   ```

3. 스크린샷 크기 확인:
   - 기본: 1440x900
   - 더 작은 해상도 시도 가능

---

### Docker 브라우저 실행 안 됨

**증상**:
```
Error: Cannot connect to Docker
```

**해결**:
1. Docker Desktop 실행 확인
2. Docker 이미지 확인:
   ```bash
   docker images | grep magentic-ui
   ```
3. 이미지가 없으면 자동 다운로드:
   ```bash
   magentic-ui --fara  # 첫 실행 시 자동 pull
   ```

---

### Timeout 오류

**증상**:
```
TimeoutError: Model call timeout (20s)
```

**해결**:
1. `_fara_web_surfer.py` 수정 (이미 적용됨):
   ```python
   model_call_timeout: int = 120
   ```
2. Magentic-UI 재시작

---

## 참고 자료

### 공식 문서
- [FARA-7B Paper](https://arxiv.org/abs/2511.19663)
- [FARA-7B Model](https://huggingface.co/microsoft/Fara-7B)
- [Magentic-UI GitHub](https://github.com/microsoft/magentic-ui)
- [LM Studio](https://lmstudio.ai/)

### 관련 프로젝트 문서
- [Playwright CLI 사용 가이드](./USAGE_GUIDE.md)
- [FARA Capability 분석](./FARA_Capability_분석_보고서.md)
- [FARA 설정 분석 보고서](./FARA_설정_분석_보고서.md)

---

**문서 작성일**: 2025-12-15
**마지막 업데이트**: 2025-12-15
**버전**: 1.0
