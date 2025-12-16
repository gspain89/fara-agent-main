# FARA 에이전트 구성 분석 보고서

## 요약

본 보고서는 현재 FARA 에이전트 구현의 설정을 분석하고, vLLM + FARA-7B + Magentic-UI 설정과 비교하여 환경을 이해하고 최적화하는 데 도움을 제공합니다.

---

## 1. `--headful` 플래그의 의미

**위치:** `run_agent.py`, 26-28번째 줄

```python
parser.add_argument(
    "--headful",
    action="store_true",
    help="Run browser in headful mode (show GUI)"
)
```

**기능:**
- **`--headful` 없이 실행**: 브라우저가 **헤드리스 모드**로 실행 (숨겨짐, GUI 창 없음)
- **`--headful` 옵션 사용**: 브라우저가 **헤드풀 모드**로 실행 (GUI 창이 보임)

**구현 방식:** FaraAgent 인스턴스 생성 시 (46번째 줄):
```python
agent = FaraAgent(config=config, headless=not args.headful)
```

**사용 사례:**
- **디버깅 시** `--headful` 사용: 에이전트의 탐색 과정을 시각적으로 확인
- **프로덕션** 또는 자동화 실행 시 생략: GUI가 불필요한 경우

---

## 2. 스크린샷 읽기 설정

### 현재 설정: **스크린샷 최대 1개**

**구성 매개변수:** `max_n_images`
- **파일:** `config.json`, 9번째 줄
- **현재 값:** `1`
- **코드 기본값:** `1` (agent.py:40)

**의미:**
- LLM의 메시지 히스토리에 **가장 최근 스크린샷만** 유지됨
- 이전 스크린샷은 컨텍스트 윈도우 크기를 관리하기 위해 제거됨
- 각 라운드마다 새로운 스크린샷을 찍지만, 최신 것만 모델에 전송됨

**구현:** `agent.py`, 153-166번째 줄
```python
def _prune_user_messages(self):
    """Keep only the latest max_n_images user messages with images"""
    user_messages_with_images = [
        msg for msg in self.messages if msg["role"] == "user"
        and any(isinstance(c, dict) and c.get("type") == "image_url"
                for c in msg.get("content", []))
    ]
    if len(user_messages_with_images) > self.max_n_images:
        # 한도를 초과하는 가장 오래된 스크린샷 제거
```

**변경 방법:** `config.json` 수정:
```json
{
  "max_n_images": 3  // 1개 대신 최근 3개 스크린샷 유지
}
```

---

## 3. 태스크 단계 제한 설정

### 현재 설정: **최대 20단계**

**구성 매개변수:** `max_rounds`
- **파일:** `config.json`, 5번째 줄
- **현재 값:** `20`
- **코드 기본값:** `15` (agent.py:62)

**의미:**
- 에이전트는 태스크당 최대 **20개의 액션 라운드**를 실행할 수 있음
- 각 라운드 = 스크린샷 → LLM 호출 → 액션 실행
- 태스크 종료 조건:
  - 최대 라운드 도달 (20), 또는
  - 에이전트가 `terminate` 액션 호출, 또는
  - 응답에서 유효한 액션을 파싱할 수 없는 경우

**구현:** `agent.py`, 294-296번째 줄
```python
for round_num in range(self.max_rounds):
    self.round_count = round_num + 1
    self.logger.info(f"Round {self.round_count}/{self.max_rounds}")
```

**변경 방법:** `config.json` 수정:
```json
{
  "max_rounds": 50  // 20 대신 최대 50단계 허용
}
```

---

## 4. 전체 구성 맵

### 현재 설정 (LM Studio + 로컬 FARA)

**구성 파일:** `/Users/gregyh/Coding/fara-agent-main/config.json`

| 매개변수 | 현재 값 | 목적 | 수정 가능 |
|---------|--------|------|----------|
| `model` | "microsoft_fara-7b" | 모델 식별자 | ✅ 예 |
| `base_url` | "http://127.0.0.1:1234/v1" | LM Studio API 엔드포인트 | ✅ 예 |
| `api_key` | "lm-studio" | API 인증 | ✅ 예 |
| `max_rounds` | 20 | 최대 태스크 단계 | ✅ 예 |
| `max_n_images` | 1 | 히스토리의 스크린샷 수 | ✅ 예 |
| `temperature` | 0.0 | 모델 결정성 | ✅ 예 |
| `save_screenshots` | true | 디스크에 스크린샷 저장 | ✅ 예 |
| `screenshots_folder` | "./screenshots" | 스크린샷 저장 위치 | ✅ 예 |
| `downloads_folder` | "./downloads" | 브라우저 다운로드 폴더 | ✅ 예 |
| `show_overlay` | true | 디버그 오버레이 표시 | ✅ 예 |
| `show_click_markers` | true | 시각적 클릭 표시기 | ✅ 예 |

### 하드코딩된 제한 (코드 변경 필요)

**파일:** `agent.py`

| 상수 | 값 | 줄 | 목적 | 수정 방법 |
|-----|-----|-----|------|----------|
| `viewport_width` | 1440 | 36 | 브라우저 창 너비 | agent.py:36 수정 |
| `viewport_height` | 900 | 37 | 브라우저 창 높이 | agent.py:37 수정 |
| `max_tokens` | 1024 | 97 | LLM 응답 토큰 제한 | agent.py:97 수정 |
| `sleep_after_action` | 1.5초 | 356 | 액션 간 대기 시간 | agent.py:356 수정 |
| `min_pixels` | 3136 | 21 | 최소 이미지 해상도 | agent.py:21 수정 |
| `max_pixels` | 12845056 | 22 | 최대 이미지 해상도 | agent.py:22 수정 |
| `page_load_timeout` | 30000ms | browser.py:146 | 페이지 탐색 타임아웃 | browser.py:146 수정 |

---

## 5. vLLM + FARA-7B + Magentic-UI 구성

### 아키텍처 비교

**현재 설정:**
```
LM Studio (localhost:1234) → run_agent.py → FaraAgent → Browser
```

**Magentic-UI 설정:**
```
vLLM (localhost:5000) → Magentic-UI (localhost:8081) → Agent Orchestration → Browser
```

### 구성 차이점

#### A. 모델 서빙

**현재 설정 (LM Studio):**
- 엔드포인트: `http://127.0.0.1:1234/v1`
- 모델 서빙용 구성 파일 없음
- GUI 기반 모델 로딩

**Magentic-UI 설정 (vLLM):**
```bash
vllm serve "microsoft/Fara-7B" --port 5000 --dtype auto
```

**vLLM 추가 옵션:**
- `--tensor-parallel-size 2`: 2개 GPU에 모델 분산
- `--dtype auto`: 자동 정밀도 감지
- `--gpu-memory-utilization 0.9`: GPU 메모리의 90% 사용
- `--max-model-len 4096`: 최대 컨텍스트 길이 설정

#### B. 구성 파일 형식

**현재 설정:** `config.json` (플랫 JSON 구조)

**Magentic-UI 설정:** `fara_config.yaml` (클라이언트 참조가 있는 계층적 YAML)

```yaml
model_config_local_surfer: &client_surfer
  provider: OpenAIChatCompletionClient
  config:
    model: "microsoft/Fara-7B"
    base_url: http://localhost:5000/v1
    api_key: not-needed
    model_info:
      vision: true
      function_calling: true
      json_output: false
      family: "unknown"
      structured_output: false
      multiple_system_messages: false

orchestrator_client: *client_surfer
coder_client: *client_surfer
web_surfer_client: *client_surfer
file_surfer_client: *client_surfer
action_guard_client: *client_surfer
model_client: *client_surfer
```

#### C. 설정이 구성되는 위치

| 설정 유형 | 현재 설정 | Magentic-UI 설정 |
|----------|----------|------------------|
| 모델 엔드포인트 | `config.json` (`base_url`) | `fara_config.yaml` (`base_url`) |
| 최대 단계/라운드 | `config.json` (`max_rounds`) | `magentic_ui_config.py` (`max_turns: 20`) |
| 단계당 액션 수 | 없음 | `magentic_ui_config.py` (`max_actions_per_step: 5`) |
| 스크린샷 제한 | `config.json` (`max_n_images: 1`) | `_fara_web_surfer.py` (`max_n_images: 3`) |
| 모델 컨텍스트 제한 | `agent.py` (`max_tokens: 1024`) | `magentic_ui_config.py` (`model_context_token_limit: 110000`) |
| 비전 설정 | `agent.py` (`MLM_PROCESSOR_IM_CFG`) | `_fara_web_surfer.py` (동일한 설정) |
| 브라우저 뷰포트 | `agent.py` (하드코딩 1440×900) | `_web_surfer.py` (동일: 1440×900) |
| 헤드리스 모드 | `run_agent.py` (`--headful` 플래그) | `magentic_ui_config.py` (`browser_headless: False`) |

**주요 발견 사항:** Magentic-UI의 설정을 GitHub 저장소에서 **모두 찾았습니다**:

**파일 위치:**
1. `src/magentic_ui/magentic_ui_config.py` - 전역 설정
2. `src/magentic_ui/agents/web_surfer/_web_surfer.py` - 웹 서퍼 기본 설정
3. `src/magentic_ui/agents/web_surfer/fara/_fara_web_surfer.py` - FARA 전용 설정
4. `src/magentic_ui/tools/playwright/playwright_controller.py` - 브라우저 컨트롤러
5. `src/magentic_ui/task_team.py` - 태스크 실행 로직 (실제 max_turns=10000 사용)

---

## 6. 구현 권장 사항

### 옵션 A: vLLM으로 마이그레이션 (현재 에이전트 코드 유지)

**이유:** 더 나은 성능, 네이티브 Linux 지원, 프로덕션 준비 완료

**단계:**
1. **vLLM 설치:**
   ```bash
   pip install vllm
   ```

2. **vLLM 서버 시작:**
   ```bash
   vllm serve "microsoft/Fara-7B" --port 5000 --dtype auto \
     --gpu-memory-utilization 0.9 \
     --max-model-len 4096
   ```

3. **`config.json` 업데이트:**
   ```json
   {
     "base_url": "http://127.0.0.1:5000/v1",
     "api_key": "not-needed"
   }
   ```

4. **기존 구성 유지:** `max_rounds`, `max_n_images` 등이 그대로 작동

**장점:**
- ✅ 에이전트 동작에 대한 완전한 제어 유지
- ✅ 모든 사용자 정의 설정이 구성 가능
- ✅ LM Studio보다 나은 성능
- ✅ 프로덕션 준비 완료

**단점:**
- ❌ Linux 또는 Windows의 WSL2 필요
- ❌ 충분한 메모리를 가진 GPU 필요

### 옵션 B: Magentic-UI 채택 (전체 마이그레이션)

**이유:** 더 많은 기능, 멀티 에이전트 오케스트레이션, 웹 UI

**단계:**
1. **Magentic-UI 설치:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install magentic-ui[fara]
   ```

2. **`fara_config.yaml` 생성:** (섹션 5의 템플릿 사용)

3. **vLLM 시작:**
   ```bash
   vllm serve "microsoft/Fara-7B" --port 5000 --dtype auto
   ```

4. **Magentic-UI 실행:**
   ```bash
   magentic-ui --fara --port 8081 --config fara_config.yaml
   ```

**장점:**
- ✅ 태스크 관리를 위한 웹 기반 UI
- ✅ 멀티 에이전트 오케스트레이션 기능
- ✅ 내장된 코더, 파일 서퍼, 액션 가드 에이전트
- ✅ 활발한 개발 및 커뮤니티 지원

**단점:**
- ❌ `max_rounds`, `max_n_images`에 대한 직접 제어 상실
- ❌ 구성 옵션을 찾기 위해 Magentic-UI 소스 검사 필요
- ❌ 다른 아키텍처로 인한 학습 곡선
- ❌ 모든 사용자 정의 기능을 지원하지 않을 수 있음

### 옵션 C: 하이브리드 접근 방식 (권장)

**이유:** 양쪽의 장점 - vLLM 성능 + 사용자 정의 에이전트

**단계:**
1. **모델 서빙을 vLLM으로 전환** (옵션 A 참조)
2. **에이전트 코드 유지** (`run_agent.py`, `agent.py` 등)
3. **`config.json` 유지** (쉬운 튜닝)
4. **선택 사항:** 채택할 추가 기능을 위해 Magentic-UI 소스 연구

**더 나은 성능을 위한 구성 튜닝:**

```json
{
  "model": "microsoft_fara-7b",
  "base_url": "http://127.0.0.1:5000/v1",
  "api_key": "not-needed",
  "max_rounds": 30,              // 복잡한 태스크를 위해 증가
  "max_n_images": 3,              // 더 많은 컨텍스트 유지
  "temperature": 0.0,
  "save_screenshots": true,
  "screenshots_folder": "./screenshots",
  "downloads_folder": "./downloads",
  "show_overlay": false,          // 프로덕션용 비활성화
  "show_click_markers": false     // 프로덕션용 비활성화
}
```

**고려할 코드 수정 사항:**

1. **max_tokens 증가** (`agent.py:97`):
   ```python
   "max_tokens": 2048,  # 더 긴 응답 허용
   ```

2. **뷰포트 조정** (`agent.py:36-37`):
   ```python
   self.viewport_width = config.get("viewport_width", 1920)
   self.viewport_height = config.get("viewport_height", 1080)
   ```

3. **sleep_after_action을 구성 가능하게** (`agent.py:356`):
   ```python
   sleep_duration = config.get("sleep_after_action", 1.5)
   await asyncio.sleep(sleep_duration)
   ```

---

## 7. 고급 구성 매트릭스

### 복잡한 태스크 시나리오별

| 태스크 유형 | `max_rounds` | `max_n_images` | `max_tokens` | 비고 |
|------------|--------------|----------------|--------------|------|
| 간단한 탐색 | 10 | 1 | 1024 | 빠른 조회 |
| 데이터 추출 | 20 | 1 | 1024 | 현재 기본값 |
| 다중 페이지 양식 | 30 | 2 | 1536 | 양식 컨텍스트 필요 |
| 복잡한 리서치 | 50 | 3 | 2048 | 긴 워크플로우 |
| 전자상거래 체크아웃 | 40 | 2 | 1536 | 다단계 프로세스 |

### vLLM 서버 튜닝

**24GB GPU용:**
```bash
vllm serve "microsoft/Fara-7B" \
  --port 5000 \
  --dtype auto \
  --gpu-memory-utilization 0.9 \
  --max-model-len 4096 \
  --disable-log-requests
```

**멀티 GPU (총 48GB):**
```bash
vllm serve "microsoft/Fara-7B" \
  --port 5000 \
  --dtype auto \
  --tensor-parallel-size 2 \
  --gpu-memory-utilization 0.9 \
  --max-model-len 8192
```

**CPU 전용 (느리지만 작동):**
```bash
# 대신 LM Studio 또는 Ollama 사용
# vLLM은 CPU 추론을 잘 지원하지 않음
```

---

## 8. 주요 발견 사항 요약

### 현재 설정 분석

✅ **합리적인 기본값으로 잘 구성됨**:
- 20단계는 대부분의 태스크에 적절함
- 1개의 스크린샷은 컨텍스트와 메모리 균형
- 디버깅을 위한 헤드풀 모드는 올바른 사용법
- LM Studio는 개발에 적합

⚠️ **잠재적 제한사항:**
- Max tokens (1024)는 복잡한 추론에 부족할 수 있음
- 뷰포트 (1440x900)는 현대 디스플레이보다 작음
- 단일 스크린샷은 다단계 플로우에서 컨텍스트를 잃을 수 있음

### Magentic-UI vs. 현재 설정

| 측면 | 현재 설정 | Magentic-UI |
|-----|----------|-------------|
| **제어** | ⭐⭐⭐⭐⭐ config.json을 통한 완전한 제어 | ⭐⭐ 제한적 - 소스 읽기 필요 |
| **투명성** | ⭐⭐⭐⭐⭐ 명확한 구성 | ⭐⭐ 제한 설정 위치 불명확 |
| **기능** | ⭐⭐⭐ 단일 에이전트, 브라우저 자동화 | ⭐⭐⭐⭐⭐ 멀티 에이전트, 오케스트레이션, UI |
| **단순성** | ⭐⭐⭐⭐⭐ 간단한 Python 스크립트 | ⭐⭐ 복잡한 프레임워크 |
| **성능** | ⭐⭐⭐ LM Studio (느림) | ⭐⭐⭐⭐ vLLM (빠름) |
| **커스터마이징** | ⭐⭐⭐⭐⭐ 수정 용이 | ⭐⭐ 소스 변경 필요 |

### 권장 다음 단계

1. **단기:** 더 나은 성능을 위해 vLLM으로 전환 (옵션 A)
2. **중기:** `max_rounds` 및 `max_n_images` 증가 실험
3. **장기:** Magentic-UI 기능 탐색하되 현재 에이전트를 백업으로 유지
4. **항상:** 토큰 사용량 모니터링 및 필요에 따라 `max_tokens` 조정

---

## 9. 구성 파일 템플릿

### 향상된 config.json (권장)

```json
{
  "model": "microsoft_fara-7b",
  "base_url": "http://127.0.0.1:5000/v1",
  "api_key": "not-needed",
  "max_rounds": 30,
  "max_n_images": 2,
  "temperature": 0.0,
  "save_screenshots": true,
  "screenshots_folder": "./screenshots",
  "downloads_folder": "./downloads",
  "show_overlay": false,
  "show_click_markers": false,
  "viewport_width": 1920,
  "viewport_height": 1080,
  "max_tokens": 1536,
  "sleep_after_action": 1.5
}
```

*참고: config에서 `viewport_width`, `viewport_height`, `max_tokens`, `sleep_after_action`을 읽으려면 코드 수정 필요*

### Magentic-UI fara_config.yaml

```yaml
model_config_local_surfer: &client_surfer
  provider: OpenAIChatCompletionClient
  config:
    model: "microsoft/Fara-7B"
    base_url: http://localhost:5000/v1
    api_key: not-needed
    model_info:
      vision: true
      function_calling: true
      json_output: false
      family: "unknown"
      structured_output: false
      multiple_system_messages: false

orchestrator_client: *client_surfer
coder_client: *client_surfer
web_surfer_client: *client_surfer
file_surfer_client: *client_surfer
action_guard_client: *client_surfer
model_client: *client_surfer
```

---

## 10. 주요 파일 참조

**현재 구현:**
- 구성: `/Users/gregyh/Coding/fara-agent-main/config.json`
- 메인 에이전트: `/Users/gregyh/Coding/fara-agent-main/agent.py`
- 진입점: `/Users/gregyh/Coding/fara-agent-main/run_agent.py`
- 브라우저 제어: `/Users/gregyh/Coding/fara-agent-main/browser.py`
- 프롬프트: `/Users/gregyh/Coding/fara-agent-main/prompts.py`

**수정을 위한 주요 라인:**
- `max_rounds`: agent.py:62
- `max_n_images`: agent.py:40
- `max_tokens`: agent.py:97
- `viewport_width/height`: agent.py:36-37
- `sleep_after_action`: agent.py:356
- 커맨드라인 인자: run_agent.py:18-36

---

## 11. Magentic-UI 상세 설정 분석 (GitHub 소스 코드 기반)

### A. 전역 설정 (`magentic_ui_config.py`)

```python
# 단계 및 액션 제한
max_turns: int = 20                    # 최대 작업 턴 수
max_actions_per_step: int = 5          # 단계당 최대 액션 수

# 에이전트 동작 모드
cooperative_planning: bool = True       # 계획 단계에서 사용자 참여
autonomous_execution: bool = False      # 실행 단계에서 자율 실행 (기본 꺼짐)
allow_for_replans: bool = True         # 오케스트레이터가 새 계획 생성 가능

# 도구 실행
multiple_tools_per_call: bool = False  # 단일 도구만 허용

# 브라우저 설정
browser_headless: bool = False         # 헤드풀 모드 기본 (GUI 보임)
browser_local: bool = False            # 도커화된 브라우저 사용
playwright_port: int = -1              # 자동 할당
novnc_port: int = -1                   # 자동 할당

# 모델 컨텍스트
model_context_token_limit: int = 110000  # 11만 토큰 (매우 큼!)
```

### B. FARA 웹 서퍼 설정 (`_fara_web_surfer.py`)

```python
# 스크린샷/이미지 제한
max_n_images: int = 3                  # 최대 3개 이미지 히스토리 유지

# 이미지 프로세서 설정 (MLM_PROCESSOR_IM_CFG)
min_pixels: int = 3136                 # 최소 이미지 픽셀
max_pixels: int = 12845056             # 최대 이미지 픽셀
patch_size: int = 14                   # 패치 크기
merge_size: int = 2                    # 병합 크기

# MLM (Multimodal Language Model) 크기
MLM_HEIGHT: int = 765                  # 스케일된 이미지 높이
MLM_WIDTH: int = 1224                  # 스케일된 이미지 너비
SCREENSHOT_TOKENS: int = 1105          # 스크린샷 토큰 예산

# 모델 호출 타임아웃
model_call_timeout: int = 20           # 20초 (재시도 로직 포함)
```

### C. 웹 서퍼 기본 설정 (`_web_surfer.py`)

```python
# 뷰포트 설정
viewport_height: int = 900             # 브라우저 창 높이
viewport_width: int = 1440             # 브라우저 창 너비
to_resize_viewport: bool = True        # 뷰포트 조정 가능

# 스크린샷 관리
to_save_screenshots: bool = False      # 스크린샷 저장 (기본 꺼짐)
animate_actions: bool = False          # 액션 애니메이션 (기본 꺼짐)

# 액션 제한
max_actions_per_step: int = 5          # 단계당 최대 5개 액션

# 탐색 설정
start_page: str = "about:blank"        # 시작 페이지
search_engine: str = "duckduckgo"      # 검색 엔진
single_tab_mode: bool = False          # 다중 탭 허용

# 출력 형식
json_model_output: bool = False        # 도구 호출 응답 (JSON 아님)
multiple_tools_per_call: bool = False  # 순차 도구 실행
use_action_guard: bool = False         # 액션 승인 시스템 (기본 꺼짐)
```

### D. Playwright 브라우저 컨트롤러 설정

```python
# 스크린샷 타임아웃
screenshot_timeout_primary: int = 7000ms    # 1차 시도 7초
screenshot_timeout_fallback: int = 10000ms  # 재시도 10초

# 뷰포트 기본값
default_viewport_width: int = 1440
default_viewport_height: int = 1440     # 주의: 다른 곳에서 900으로 오버라이드됨
```

### E. 태스크 실행 설정 (`task_team.py`)

```python
# 실제 사용되는 max_turns
team = RoundRobinGroupChat(
    participants=[web_surfer, user_proxy],
    max_turns=10000,  # 실제로는 거의 무제한!
)
```

**중요:** 설정 파일의 `max_turns=20`과 달리, 실제 코드에서는 **10,000턴**을 허용합니다.

---

## 12. 현재 환경 vs Magentic-UI 상세 비교

### A. 주요 차이점 요약

| 설정 항목 | 현재 환경 (LM Studio) | Magentic-UI (vLLM + FARA) | 차이 |
|----------|---------------------|-------------------------|------|
| **최대 라운드** | 20 | 20 (설정) / **10,000** (실제) | ⚠️ Magentic-UI는 실제로 거의 무제한 |
| **스크린샷 히스토리** | 1개 | **3개** | ⚠️ Magentic-UI가 3배 더 많은 컨텍스트 유지 |
| **모델 컨텍스트 토큰** | 1,024 | **110,000** | ⚠️ Magentic-UI가 107배 더 큼! |
| **단계당 액션** | 제한 없음 | **5개** | ⚠️ Magentic-UI는 단계당 액션 제한 |
| **뷰포트 크기** | 1440×900 | 1440×900 | ✅ 동일 |
| **이미지 처리** | min:3136, max:12845056 | min:3136, max:12845056 | ✅ 동일 |
| **헤드리스 모드** | `--headful` 플래그 | False (GUI 보임) | ✅ 유사 (둘 다 GUI 선호) |
| **스크린샷 저장** | True | False | ⚠️ 현재 환경만 자동 저장 |
| **검색 엔진** | 없음 | DuckDuckGo | ℹ️ Magentic-UI 전용 기능 |

### B. 성능 영향 분석

#### 1. **컨텍스트 토큰 차이 (1,024 vs 110,000)**

**현재 환경의 제약:**
- 1,024 토큰은 **매우 짧은 응답**만 가능
- 복잡한 추론이나 긴 계획 생성 불가
- 스크린샷 1개 = 1,105 토큰이므로 이미지 포함 시 **응답 여유 거의 없음**

**Magentic-UI의 장점:**
- 110,000 토큰으로 **스크린샷 3개 + 상세한 추론** 가능
- 긴 대화 컨텍스트 유지 가능
- 복잡한 다단계 작업에 유리

**권장 조치:**
```python
# agent.py:97 수정
"max_tokens": 8192,  # 최소 8K로 증가 권장 (스크린샷 + 응답 여유)
```

#### 2. **스크린샷 히스토리 차이 (1개 vs 3개)**

**현재 환경의 제약:**
- 이전 페이지 상태를 잊어버림
- 다단계 양식 작성 시 컨텍스트 손실
- "뒤로 가기" 작업 시 이전 상태 모름

**Magentic-UI의 장점:**
- 최근 3개 페이지 상태 기억
- 양식 작성, 검색 결과 비교 등에 유리
- 더 나은 컨텍스트 인식

**권장 조치:**
```json
// config.json 수정
{
  "max_n_images": 3  // 1 → 3으로 증가
}
```

#### 3. **최대 라운드 차이 (20 vs 10,000)**

**분석:**
- 현재 20 라운드는 **대부분 작업에 충분**
- Magentic-UI의 10,000은 **거의 제한 없음** (프로덕션 환경에서는 과도할 수 있음)

**권장 조치:**
- 현재 20 유지 또는 복잡한 작업을 위해 30-50으로 증가
- 10,000까지는 불필요 (무한 루프 위험)

### C. Magentic-UI 설정을 현재 환경에 적용하기

#### 옵션 1: 최소 변경 (핵심만 적용)

**목표:** 가장 영향이 큰 설정만 적용

**변경할 설정:**
1. `max_n_images: 1 → 3` (스크린샷 히스토리 증가)
2. `max_tokens: 1024 → 4096` (응답 여유 확보)

**변경 방법:**
```json
// config.json
{
  "max_n_images": 3,
  "max_tokens": 4096  // 새 필드 추가 (코드 수정 필요)
}
```

```python
# agent.py:97 수정
"max_tokens": config.get("max_tokens", 1024),
```

#### 옵션 2: 완전 동일화 (Magentic-UI와 동일하게)

**목표:** Magentic-UI와 최대한 동일한 환경 구성

**새로운 config.json:**
```json
{
  "model": "microsoft_fara-7b",
  "base_url": "http://127.0.0.1:1234/v1",
  "api_key": "lm-studio",

  // 실행 제한
  "max_rounds": 20,
  "max_actions_per_step": 5,

  // 이미지/컨텍스트
  "max_n_images": 3,
  "max_tokens": 110000,  // vLLM 사용 시만 가능

  // 브라우저
  "viewport_width": 1440,
  "viewport_height": 900,

  // 기능 플래그
  "to_save_screenshots": false,
  "animate_actions": false,
  "use_action_guard": false,

  // 기존 설정
  "temperature": 0.0,
  "screenshots_folder": "./screenshots",
  "downloads_folder": "./downloads",
  "show_overlay": false,
  "show_click_markers": false
}
```

**필요한 코드 수정:**
1. `agent.py`: `max_actions_per_step`, `max_tokens` 설정 읽기 지원
2. `agent.py`: `animate_actions`, `use_action_guard` 지원
3. `agent.py`: 단계당 액션 수 제한 로직 추가

#### 옵션 3: 하이브리드 (실용적 접근)

**목표:** 유용한 기능만 선택적으로 채택

**권장 설정:**
```json
{
  "model": "microsoft_fara-7b",
  "base_url": "http://127.0.0.1:1234/v1",
  "api_key": "lm-studio",
  "max_rounds": 30,              // 20 → 30 (여유 확보)
  "max_n_images": 3,              // 1 → 3 (중요!)
  "max_tokens": 4096,             // 1024 → 4096 (중요!)
  "temperature": 0.0,
  "save_screenshots": true,       // 디버깅용 유지
  "screenshots_folder": "./screenshots",
  "downloads_folder": "./downloads",
  "show_overlay": true,           // 디버깅용 유지
  "show_click_markers": true      // 디버깅용 유지
}
```

**장점:**
- ✅ 핵심 성능 개선 (max_n_images, max_tokens)
- ✅ 디버깅 기능 유지 (스크린샷 저장, 오버레이)
- ✅ 최소한의 코드 수정만 필요
- ✅ LM Studio에서도 작동 가능

---

## 13. Magentic-UI 독점 기능

현재 환경에는 없지만 Magentic-UI가 제공하는 기능들:

### A. 멀티 에이전트 오케스트레이션
- **Web Surfer**: 브라우저 자동화
- **Coder**: 코드 작성 및 실행
- **File Surfer**: 파일 시스템 탐색
- **User Proxy**: 사용자 대리인
- **Orchestrator**: 에이전트 조율

### B. 협력적 계획 모드
- `cooperative_planning: True`: 사용자가 계획 단계에서 개입 가능
- `autonomous_execution: False`: 실행 중 사용자 승인 필요

### C. 액션 가드 시스템
- `use_action_guard: True` 활성화 시 모든 액션을 별도 LLM이 검증
- 위험한 작업 방지 (예: 중요 데이터 삭제)

### D. URL 관리
- `url_block_list`: 특정 도메인 차단
- `url_statuses`: 허용/거부 목록 관리

### E. Docker 통합
- 격리된 브라우저 환경
- noVNC를 통한 원격 모니터링

---

## 결론

### 핵심 발견 사항

Magentic-UI의 GitHub 소스 코드를 **완전히 분석**하여 모든 설정을 찾아냈습니다:

1. ✅ **`--headful` 의미**: 브라우저 GUI 표시 (Magentic-UI도 기본적으로 GUI 사용)
2. ✅ **스크린샷 제한**: 현재 1개 vs Magentic-UI 3개
3. ✅ **최대 단계**: 현재 20 vs Magentic-UI 20(설정)/10,000(실제)
4. ✅ **설정 위치**: 모두 GitHub 소스 코드에서 확인
5. ✅ **주요 차이점**: 컨텍스트 토큰 크기 (1,024 vs 110,000 - 107배 차이!)

### 성능 격차 분석

**가장 중요한 차이:**
- **컨텍스트 토큰**: 현재 1,024 토큰은 스크린샷(1,105 토큰)과 거의 동일 → 응답 생성 여유 거의 없음
- **스크린샷 히스토리**: 1개는 이전 페이지 컨텍스트 손실 → 다단계 작업에 불리
- **액션 제한**: 현재는 제한 없음 vs Magentic-UI는 단계당 5개로 제한

### 권장 조치 (마이그레이션 불필요)

**최소 변경으로 성능 개선 (옵션 3 - 하이브리드 접근 권장):**

```json
{
  "max_n_images": 3,     // 1 → 3 (가장 중요!)
  "max_tokens": 4096,    // 1024 → 4096 (필수!)
  "max_rounds": 30       // 20 → 30 (선택)
}
```

**필요한 코드 수정:**
- `agent.py:97`: `config.get("max_tokens", 1024)` 추가

**기대 효과:**
- ✅ 스크린샷 컨텍스트 3배 증가 (다단계 작업 개선)
- ✅ 응답 생성 여유 4배 증가 (복잡한 추론 가능)
- ✅ LM Studio에서도 작동 (vLLM 전환 불필요)

### vLLM 전환은 필요한가?

**결론: 선택 사항 (필수 아님)**

- 현재 LM Studio + 위 설정 변경만으로도 충분한 성능 확보 가능
- vLLM 전환 시 장점: 더 빠른 추론 속도, 110,000 토큰 지원
- vLLM 전환 시 단점: Linux/WSL2 필요, GPU 메모리 요구량 높음

### Magentic-UI 채택은 필요한가?

**결론: 불필요 (현재 환경이 더 단순하고 제어 가능)**

**현재 환경의 장점:**
- ⭐⭐⭐⭐⭐ 완전한 설정 제어 (config.json)
- ⭐⭐⭐⭐⭐ 투명한 구성 (모든 값이 명확)
- ⭐⭐⭐⭐⭐ 간단한 아키텍처 (단일 에이전트)
- ⭐⭐⭐⭐⭐ 쉬운 커스터마이징

**Magentic-UI가 나은 경우:**
- 멀티 에이전트 오케스트레이션 필요 시
- 웹 UI 인터페이스 선호 시
- 협력적 계획 모드 필요 시

### 최종 답변

**질문 1:** `--headful`의 의미?
→ 브라우저 GUI 창을 표시 (디버깅용). Magentic-UI도 기본값은 GUI 표시.

**질문 2:** 스크린샷 1개만 읽는가?
→ 예, `max_n_images=1`. Magentic-UI는 3개. config.json에서 수정 가능.

**질문 3:** 20단계가 최대인가?
→ 예, `max_rounds=20`. Magentic-UI는 설정은 20이지만 실제 코드는 10,000 사용.

**질문 4:** vLLM+Magentic-UI는 어떻게 설정되어 있나?
→ 완전 분석 완료. 섹션 11, 12 참조.

**질문 5:** 유사한 환경을 어떻게 구현하나?
→ 섹션 12.C의 옵션 3 (하이브리드) 권장. 마이그레이션 불필요, config.json 수정만으로 충분.
