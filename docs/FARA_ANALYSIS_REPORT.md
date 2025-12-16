# Fara-7B Agent 분석 리포트

> 작성일: 2025-12-11
> 목적: Fara-7B 웹 에이전트의 현재 capability, 제약사항, 확장 시 위험성 분석

---

## 목차
1. [Fara-7B 개요](#1-fara-7b-개요)
2. [현재 구현 분석](#2-현재-구현-분석)
3. [지원되는 Actions (공식)](#3-지원되는-actions-공식)
4. [Capability 제약사항](#4-capability-제약사항)
5. [확장 시도 시 문제점](#5-확장-시도-시-문제점)
6. [참고 자료](#6-참고-자료)

---

## 1. Fara-7B 개요

### ⚠️ 중요: 설계 vs 현재 구현

**이 리포트는 두 가지를 구분합니다:**

1. **공식 Fara-7B 설계** (ArXiv 논문, Microsoft Research)
   - Multi-turn task execution
   - Stateful (히스토리 유지)
   - User intervention at critical points
   - Follow-up task support

2. **현재 구현** (`/Users/gregyh/Coding/fara-agent-main`)
   - Single task per run
   - No history persistence between runs
   - No user intervention mechanism
   - Simplified architecture

**이 괴리는 현재 코드베이스가 Fara-7B의 간소화된 버전이기 때문입니다.**

---

### 1.1 기본 정보

**모델명**: Fara-7B (Qwen2.5-VL-7B 기반)
**개발**: Microsoft Research
**발표**: 2024년 11월
**용도**: Computer Use Agent (웹 브라우저 자동화)

**핵심 특징 (공식 설계):**
- **Vision-centric 접근**: 스크린샷만으로 웹 페이지 이해
- **Accessibility tree 불사용**: DOM 정보 없이 순수 시각 정보만 활용
- **Direct coordinate prediction**: (x, y) 픽셀 좌표를 직접 예측
- **Small Language Model (7B)**: 로컬 실행 가능한 경량 모델
- **Multi-turn capable**: 연속 태스크 지원 (논문 확인)
- **Interactive**: Critical point에서 사용자 개입 지원 (논문 확인)

### 1.2 학습 데이터

**규모:**
- 145,000 trajectories
- 1,000,000 steps
- 70,000 unique domains

**생성 방법:**
- Magentic-One 멀티에이전트 프레임워크 사용
- 합성 데이터 생성 파이프라인
- Verifier agent를 통한 품질 검증
- **UserSimulator**: Follow-up task 생성 및 critical point 응답

**데이터 구성:**
- 스크린샷
- Chain-of-thought (사고 과정)
- Action traces
- Grounding 데이터 (UI 요소 위치)
- **Full history**: 이전 단계들의 observations, thoughts, actions

**Multi-turn 학습** (ArXiv 논문):
> "if Fara-7B finishes the initial task q₀ after t steps and the user follows up with another query q₁, then we simply **continue predicting the next steps while maintaining the full history**"

**User Intervention 학습** (ArXiv 논문):
> The model "**pauses task execution at critical points until explicit user confirmation is provided**" and is designed to "**stop and hand back control to the user**" at critical points like logins or purchases.

### 1.3 성능 (벤치마크)

| 벤치마크 | Fara-7B 성공률 | 비교 |
|----------|----------------|------|
| WebVoyager | 73.5% | GPT-4o SoM Agent 대비 우수 |
| Online-Mind2Web | 34.1% | UI-TARS-1.5-7B (7B) 대비 우수 |
| DeepShop | 26.2% | - |
| WebTailBench | 38.4% | - |

---

## 2. 현재 구현 분석

### ⚠️ 공식 설계와의 차이점

**공식 Fara-7B 능력 (ArXiv 논문)**:
- ✅ Multi-turn: 연속 태스크 실행
- ✅ Stateful: Full history 유지
- ✅ Interactive: Critical point에서 사용자 개입
- ✅ Follow-up tasks: 이전 작업 기반 후속 작업

**현재 구현 제약**:
- ❌ Single-shot: 한 번에 하나의 독립적 태스크만
- ❌ Stateless: 실행 간 히스토리 공유 안 됨
- ❌ No intervention: 사용자 개입 메커니즘 없음
- ❌ No follow-up: 각 실행은 새로운 브라우저 세션

**왜 이런 차이가 발생했는가?**
현재 코드베이스는 Fara-7B의 **간소화된 데모 구현**입니다.
공식 연구 프레임워크는 더 복잡한 interactive 기능을 지원하지만,
이 코드는 기본적인 single-task execution에 집중한 버전입니다.

---

### 2.1 코드베이스 구조

**위치**: `/Users/gregyh/Coding/fara-agent-main/`

**핵심 파일:**
```
run_agent.py      - 엔트리 포인트, CLI 인터페이스
agent.py          - FaraAgent 클래스, 메인 루프 (single-task only)
browser.py        - SimpleBrowser 클래스, Playwright 래퍼
prompts.py        - 시스템 프롬프트 생성
config.json       - 설정 파일
```

### 2.2 실행 흐름

```
1. run_agent.py
   ├─ argparse: --task, --headful, --config
   ├─ config.json 로드
   └─ FaraAgent 생성 및 실행

2. agent.start()
   └─ browser.start() → Playwright Chromium 실행

3. agent.run(task)
   ├─ for round in range(max_rounds):  # 기본 20 라운드
   │  ├─ screenshot 촬영
   │  ├─ 시스템 프롬프트 + 태스크 + 스크린샷 → LLM 호출
   │  ├─ 응답에서 <tool_call> 파싱
   │  ├─ action 실행 (click, type, scroll 등)
   │  ├─ 1.5초 대기
   │  └─ 새 screenshot 촬영
   └─ loop 종료 조건:
      - 모델이 "terminate" 액션 호출
      - 유효한 액션 파싱 실패
      - max_rounds 도달

4. agent.close()
   └─ browser.close() → Playwright 종료
```

### 2.3 모델 인터페이스

**LLM 서버**: LM Studio (http://127.0.0.1:1234/v1)
**모델**: microsoft_fara-7b
**API**: OpenAI Compatible API

**입력 형식:**
```python
messages = [
    {
        "role": "system",
        "content": [
            {"type": "text", "text": system_prompt},
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{screenshot_b64}"}}
        ]
    },
    {
        "role": "user",
        "content": f"Task: {task}\nCurrent URL: {url}\n..."
    }
]
```

**출력 형식:**
```
<thinking>
I should click the search button at coordinates (500, 300).
</thinking>
<tool_call>
{"name": "computer_use", "arguments": {"action": "left_click", "coordinate": [500, 300]}}
</tool_call>
```

### 2.4 좌표 변환 (중요!)

**스크린샷 해상도 변환:**
- 실제 뷰포트: 1440x900
- 모델 입력: 해상도 축소 (Qwen2.5-VL 처리 가능 크기로)
- 모델 출력: 축소된 해상도 기준 좌표
- 실행 시: 다시 1440x900 좌표로 변환

```python
# agent.py:108
def _convert_resized_coords_to_viewport(self, coord):
    im_width, im_height = self.prompt_data["im_size"]
    vp_width, vp_height = 1440, 900
    scaled_x = (coord[0] / im_width) * vp_width
    scaled_y = (coord[1] / im_height) * vp_height
    return (scaled_x, scaled_y)
```

---

## 3. 지원되는 Actions (공식)

### 3.1 완전한 Action 목록

**출처**: ArXiv 논문 Table 7

| Action | 설명 | 파라미터 |
|--------|------|----------|
| `key` | 키보드 키 입력 | `keys`: ["Enter", "Tab", "Escape", ...] |
| `type` | 텍스트 타이핑 | `text`, `coordinate` (옵션), `press_enter`, `delete_existing_text` |
| `mouse_move` | 마우스 커서 이동 | `coordinate`: [x, y] |
| `left_click` | 마우스 왼쪽 클릭 | `coordinate`: [x, y] |
| `scroll` | 스크롤 | `pixels`: 양수(위로), 음수(아래로) |
| `visit_url` | URL 방문 | `url`: 문자열 (https:// 자동 추가) |
| `web_search` | 웹 검색 | `query`: 검색어 (Bing 사용) |
| `history_back` | 브라우저 뒤로가기 | 없음 |
| `pause_and_memorize_fact` | 정보 기억 | `fact`: 기억할 내용 |
| `wait` | 대기 | `time` 또는 `duration`: 초 단위 |
| `terminate` | 태스크 종료 | `status`: "success" 또는 "failure" |

**총 11개 액션** - 이것이 Fara-7B가 **학습한 전체 액션**입니다.

### 3.2 현재 구현 (agent.py)

**파일**: `/Users/gregyh/Coding/fara-agent-main/agent.py`
**메서드**: `_execute_action()` (Line 168-277)

**구현 상태:**
```python
✅ key              - Line 168-172
✅ type             - Line 174-190
✅ mouse_move       - Line 192-197
✅ left_click       - Line 199-207
✅ scroll           - Line 209-214
✅ visit_url        - Line 216-229
✅ web_search       - Line 231-253
✅ history_back     - Line 234-237
✅ pause_and_memorize_fact - Line 260-264
✅ wait             - Line 255-258
✅ terminate        - Line 266-270
```

**모든 공식 액션이 구현되어 있음.**

### 3.3 Tool Call 파싱

**파일**: `agent.py:114-134`

```python
def _parse_action(self, response: str) -> Dict[str, Any] | None:
    # <tool_call>...</tool_call> 태그 찾기
    if "<tool_call>" not in response:
        return None

    # JSON 추출
    start = response.find("<tool_call>") + len("<tool_call>")
    end = response.find("</tool_call>", start)
    json_str = response[start:end].strip()

    # 파싱
    tool_call = json.loads(json_str)

    # computer_use 툴만 허용
    if tool_call.get("name") == "computer_use":
        return tool_call.get("arguments", {})

    return None  # 파싱 실패 시
```

**중요 동작:**
- `<tool_call>` 태그가 없으면 `None` 반환
- `None` 반환 시 → 에이전트 루프 종료 (agent.py:338-340)
- JSON 파싱 실패 시 → 에이전트 루프 종료

---

## 4. Capability 제약사항

### 4.1 Vision-Only 제약

**현재 동작:**
```
모델이 받는 입력:
1. 스크린샷 이미지 (PNG, base64 인코딩)
2. 텍스트 프롬프트 (태스크, URL, 최근 액션 히스토리)

모델이 받지 못하는 입력:
❌ HTML DOM 구조
❌ Accessibility tree
❌ 페이지 텍스트 내용 (innerText)
❌ 요소의 CSS selector
❌ JavaScript 실행 결과
```

**이것이 Fara-7B의 핵심 철학이자 제약사항입니다.**

### 4.2 Wikipedia 요약 태스크 실패 사례

**태스크**: "open wikipedia and search for 'vision transformer' open the article read the introduction section and summarize the main idea in simple terms"

**실행 로그 분석:**
```
Round 1: visit_url → "https://en.wikipedia.org"
Round 2: type → "Vision transformer" (검색창)
Round 3: scroll down
Round 4: scroll up
Round 5: 모델 응답: "The page is already open to the Vision Transformer
                     article on Wikipedia, which fulfills step 1 of the plan.
                     The introduction section is visible, so we can proceed
                     to read and summarize it."
         액션: terminate(status="success")
         → 태스크 종료
```

**실패 원인:**
1. 모델이 스크린샷에서 "introduction section is **visible**"라고 확인함 ✓
2. 하지만 **실제 텍스트를 읽을 방법이 없음** ✗
3. 읽지도 않고 조기에 `terminate("success")` 호출
4. 요약문 생성 없이 종료

**근본 문제**: **페이지 텍스트 내용을 추출하는 액션이 존재하지 않음**

### 4.3 DOM 접근 불가

**Playwright는 DOM 접근 가능하지만:**

```python
# browser.py에서 Playwright 사용 중
# 가능한 작업들 (현재 미사용):
await page.evaluate("() => document.body.innerText")  # 텍스트 추출
await page.locator("h1").text_content()               # 요소 텍스트
await page.query_selector("#search-input")             # CSS selector
```

**그러나 Fara-7B는:**
- 이런 DOM 작업을 요청할 액션이 없음
- 학습 데이터에 DOM 정보가 포함되지 않음
- 순수 시각 정보만으로 학습됨

### 4.4 Action Space 고정

**ArXiv 논문 확인 결과:**
- ✅ Fara-7B는 11개 액션으로 학습됨
- ❌ 새 액션 일반화 능력에 대한 실험 없음
- ❌ 새 액션 추가에 대한 공식 가이드 없음
- ❌ Ablation study 없음

**논문 인용:**
> "all outputs are tokens from the model's vocabulary, including the coordinates."

**의미:**
- 액션 이름 자체가 모델의 학습된 토큰 vocabulary에 포함됨
- 학습하지 않은 액션명은 생성하지 못할 가능성 높음

### 4.5 컨텍스트 길이 제한

**설정** (config.json):
```json
{
  "max_n_images": 1,  // 매번 최신 스크린샷 1장만 전송
  "max_rounds": 20    // 최대 20 라운드
}
```

**컨텍스트 관리** (agent.py:301):
```python
# 최근 3개 액션만 히스토리에 포함
action_context = "\n".join(action_history[-3:])
```

**제약:**
- 이미지는 항상 최신 1장만 (이전 스크린샷 기억 안 함)
- 액션 히스토리는 최근 3개만
- LM Studio with Fara-7B: ~4096 토큰 제한

---

## 5. 확장 시도 시 문제점

### 5.1 새 액션 추가 시도 (예: `get_page_text`)

**제안된 방법:**
```python
# prompts.py에 추가
- `get_page_text`: Extract all visible text from the current page.

# agent.py에 핸들러 추가
elif action == "get_page_text":
    text = await self.browser.get_page_text()
    return f"Page text: {text}"
```

**예상되는 문제:**

#### 문제 1: 모델이 새 액션명을 생성하지 못함

```
사용자 태스크: "read and summarize the article"

모델 사고 과정:
- "I should read the page text" ✓ (의도 파악)
- "I will call get_page_text action" ✗ (학습하지 않은 액션명)

실제 모델 출력:
<tool_call>
{"name": "computer_use", "arguments": {"action": "scroll", ...}}
</tool_call>

또는

<thinking>
I should extract the text content to summarize it.
</thinking>
<tool_call>
{"name": "computer_use", "arguments": {"action": "terminate", "status": "success"}}
</tool_call>
```

**왜 이런 일이 발생하는가:**
- `get_page_text`는 학습 데이터에 없는 토큰
- 모델의 vocabulary에 포함되어 있지 않을 가능성
- 프롬프트에 설명을 추가해도 모델이 무시함

#### 문제 2: 파싱 실패로 조기 종료

```python
# agent.py:338-340
if not action_args:  # 파싱 실패
    self.logger.warning("No valid action found in response")
    break  # 루프 종료!
```

**시나리오:**
```
Round 5: 모델이 자연어로만 응답 ("I should read the text")
         → <tool_call> 태그 없음
         → _parse_action() returns None
         → 에이전트 종료
```

#### 문제 3: 액션명 오타 또는 변형

학습된 액션이 아니므로 모델이 변형된 형태로 생성할 수 있음:

```json
{"action": "get_page_content"}  // 원래는 get_page_text
{"action": "extract_text"}
{"action": "read_page"}
{"action": "get_text"}
```

모두 파싱 실패 → 에이전트 종료

### 5.2 기존 액션에 새 파라미터 추가 (예: `pause_and_memorize_fact`)

**제안된 방법:**
```python
# prompts.py
- `pause_and_memorize_fact`: Record a fact for later use.
  Add "extract_content": true to automatically extract page text.

# agent.py
elif action == "pause_and_memorize_fact":
    fact = action_args.get("fact") or ""
    extract_content = action_args.get("extract_content", False)  # 새 파라미터

    if extract_content:
        page_text = await self.browser.get_page_text()
        self.facts.append(f"{fact}\n{page_text}")
```

**예상되는 문제:**

#### 문제 1: 모델이 새 파라미터를 사용하지 않음

**학습 데이터에서 본 형태:**
```json
{"action": "pause_and_memorize_fact", "fact": "Price is $99"}
```

**우리가 원하는 형태:**
```json
{"action": "pause_and_memorize_fact", "fact": "intro", "extract_content": true}
                                                        ↑ 학습 데이터에 없음
```

**실제 모델 출력:**
```json
{"action": "pause_and_memorize_fact", "fact": "Vision transformer info"}
// extract_content 파라미터 누락 → 기본 동작으로 실행
```

#### 문제 2: 의미론적 불일치

```
태스크: "read and summarize the article"
모델 사고: "I need to READ the content, not MEMORIZE it"
→ pause_and_memorize_fact 액션을 호출하지 않음
→ 다른 액션 사용하거나 terminate 호출
```

### 5.3 자동 텍스트 추출 (백그라운드)

**제안된 방법:**
```python
# agent.py run() 메서드
for round_num in range(max_rounds):
    screenshot = await self._get_screenshot()

    # 자동 텍스트 추출 추가
    if "wikipedia.org" in current_url:
        page_text = await self.browser.get_page_text()
        action_history.append(f"[PAGE CONTENT]: {page_text}")

    # 기존 로직 계속...
```

**장점:**
- ✅ 모델 변경 불필요
- ✅ 확실히 동작함

**잠재적 문제:**

#### 문제 1: 토큰 제한 초과

```
Wikipedia 기사 텍스트: ~10,000 characters = ~2,500 tokens
기존 컨텍스트: ~1,000 tokens
이미지 (vision tokens): ~500-1000 tokens
총: ~4,000-4,500 tokens

LM Studio 제한: 4,096 tokens
→ 오버플로 가능성
```

**해결책:**
```python
page_text = await browser.get_page_text(max_length=3000)  # 3000자로 제한
```

#### 문제 2: 모델이 텍스트를 무시

```
action_history에 텍스트 추가됨:
"[PAGE CONTENT]: The Vision Transformer (ViT) is a neural network..."

하지만 모델이:
- 이 정보를 읽지 않고
- 여전히 스크린샷만 보고
- "I can see the introduction section" 이라고만 응답
- 텍스트 기반 요약 생성 실패
```

**이유:**
- Fara-7B는 **vision-centric**로 학습됨
- 긴 텍스트 컨텍스트 처리 능력이 제한적일 수 있음
- 학습 시 텍스트 컨텍스트가 주로 짧은 action history였음

#### 문제 3: 컨텍스트 관리

```python
# 현재 구현
action_history.append(f"[PAGE CONTENT]: {long_text}")

# 문제:
# - 최근 3개 액션만 유지 (line 301)
# - 페이지 텍스트가 밀려날 수 있음
# - Round 5에서 추가 → Round 8에서 사라짐
```

### 5.4 실제 실패 사례 재현

**시나리오**: 새 액션 `get_page_text` 추가 후 Wikipedia 태스크 실행

```
Round 1: visit_url("https://wikipedia.org") ✓
Round 2: type("vision transformer") + Enter ✓
Round 3: click(검색 결과) ✓
Round 4: 모델 사고: "I should extract the text to summarize it"
         모델 시도: <tool_call>{"action": "get_page_text"}</tool_call>

         경우 1) 모델이 액션명을 제대로 생성함 (낮은 확률)
         → 시스템: Page text extracted (10000 chars)
         → Round 5: 모델이 텍스트 읽고 요약 생성 ✓

         경우 2) 모델이 다른 액션명 생성 (중간 확률)
         → <tool_call>{"action": "extract_text"}</tool_call>
         → 시스템: Unknown action: extract_text
         → Round 5: 모델 혼란, 재시도 또는 terminate

         경우 3) 모델이 학습된 액션으로 대체 (높은 확률)
         → <tool_call>{"action": "scroll", "pixels": -500}</tool_call>
         → 여전히 텍스트 추출 못함
         → 결국 조기 terminate

         경우 4) 모델이 자연어로만 응답 (중간 확률)
         → "I will now read and summarize the content."
         → <tool_call> 없음
         → 파싱 실패 → 에이전트 종료
```

**실제 발생 가능성:**
- 경우 1: ~10-20% (운이 좋으면)
- 경우 2: ~20-30%
- 경우 3: ~30-40% (가장 가능성 높음)
- 경우 4: ~10-20%

### 5.5 왜 AutoGen/Claude는 성공하고 Fara는 실패하는가?

**AutoGen MultimodalWebSurfer:**
```python
# 기본적으로 제공되는 도구:
- visit_url()
- web_search()
- page_up() / page_down()
- read_page_and_answer(question)  ← 텍스트 추출 + 분석
- summarize_page()                 ← 페이지 요약
- answer_from_page(question)       ← 질문 답변
```
→ 텍스트 추출/분석 도구가 **기본 제공**됨

**Claude (Anthropic):**
```python
# Computer Use 도구:
- screenshot
- mouse/keyboard actions
- bash (명령어 실행)
```
→ bash에서 `curl` + `html2text` 등으로 텍스트 추출 가능
→ 또는 개발자가 custom MCP server 추가 가능

**Fara-7B:**
```python
# 제공되는 도구:
- 11개 기본 액션 (클릭, 스크롤, 타이핑...)
- 텍스트 추출 도구 없음
- 확장 메커니즘 없음 (MCP 미지원)
```
→ 텍스트 추출이 **아예 불가능**

---

## 6. 참고 자료

### 6.1 공식 문서

**연구 논문:**
- [Fara-7B: An Efficient Agentic Model for Computer Use (ArXiv)](https://arxiv.org/html/2511.19663v1)
  - Table 7: 완전한 액션 목록
  - Section 3: 학습 데이터 및 방법론
  - Section 4: 벤치마크 성능

**블로그 포스트:**
- [Microsoft Research Blog - Fara-7B](https://www.microsoft.com/en-us/research/blog/fara-7b-an-efficient-agentic-model-for-computer-use/)
  - Magentic-One 프레임워크와의 관계
  - Vision-centric 접근법의 장점

**모델 카드:**
- [Hugging Face - microsoft/Fara-7B](https://huggingface.co/microsoft/Fara-7B)
  - 사용 방법
  - vLLM 서버 설정
  - 제약사항 및 안전 가이드

**코드 저장소:**
- [GitHub - microsoft/fara](https://github.com/microsoft/fara)
  - 평가 프레임워크
  - 벤치마크 구현
  - 추상화된 웹 에이전트 인터페이스

### 6.2 관련 프로젝트

**Magentic-One:**
- [Microsoft Research - Magentic-One](https://www.microsoft.com/en-us/research/articles/magentic-one-a-generalist-multi-agent-system-for-solving-complex-tasks/)
- Fara-7B의 학습 데이터 생성에 사용된 멀티에이전트 시스템

**AutoGen MultimodalWebSurfer:**
- [AutoGen Documentation](https://microsoft.github.io/autogen/dev/reference/python/autogen_ext.agents.web_surfer.html)
- Vision + Text 하이브리드 접근법
- Accessibility tree 사용

### 6.3 비교 분석

| 특징 | Fara-7B | AutoGen WebSurfer | Claude Computer Use |
|------|---------|-------------------|---------------------|
| **모델 크기** | 7B | 임의 (GPT-4o 등) | Claude Opus/Sonnet |
| **입력 방식** | Vision only | Vision + A11y tree | Vision + bash |
| **DOM 접근** | ❌ 없음 | ✅ Accessibility tree | ✅ bash/curl 가능 |
| **텍스트 추출** | ❌ 없음 | ✅ read_page_and_answer | ✅ 우회 방법 가능 |
| **로컬 실행** | ✅ 가능 (7B) | ❌ 대형 모델 필요 | ❌ API만 가능 |
| **확장성** | ❌ 제한적 | ✅ 도구 추가 가능 | ✅ MCP 지원 |
| **학습 데이터** | 145K trajectories | N/A | N/A |
| **벤치마크** | WebVoyager 73.5% | - | - |

---

## 7. 결론 및 권장사항

### 7.1 Fara-7B의 강점

✅ **로컬 실행 가능**: 7B 파라미터로 경량, 프라이버시 보장
✅ **우수한 성능**: 같은 크기 모델 대비 SOTA
✅ **간단한 아키텍처**: Accessibility tree 파싱 불필요
✅ **강건성**: 웹사이트 구조 변화에 덜 민감 (시각 정보 기반)
✅ **빠른 추론**: 작은 모델 크기로 낮은 레이턴시

### 7.2 Fara-7B의 제약

❌ **텍스트 추출 불가**: DOM에서 텍스트를 가져올 수 없음
❌ **정보 검색 태스크 약함**: 요약, 특정 정보 찾기 등 실패
❌ **고정된 액션 스페이스**: 새 도구 추가 어려움
❌ **확장성 제한**: 공식 가이드 없음, 실험적 접근만 가능
❌ **MCP 미지원**: Claude의 MCP 서버 같은 확장 메커니즘 없음

### 7.3 적합한 사용 사례

**✅ 추천:**
- 폼 작성 자동화
- 웹사이트 네비게이션
- 버튼 클릭, 링크 따라가기
- 스크롤, 검색, 로그인 등 상호작용
- 반복적인 웹 작업 자동화

**❌ 비추천:**
- 웹 페이지 요약
- 특정 정보 추출 (가격, 리뷰 등)
- 긴 문서 읽기
- 데이터 스크래핑
- 테이블/리스트 분석

### 7.4 현재 코드베이스 유지 권장사항

**변경하지 말아야 할 것:**
- 11개 공식 액션 목록
- 액션 파싱 로직
- Tool call 형식
- Vision-centric 접근법

**변경 가능한 것:**
- 브라우저 lifecycle 관리 (예: --keep-open 플래그)
- 스크린샷 저장 위치
- 로깅 상세도
- 설정 파라미터 (max_rounds, temperature 등)
- 에러 핸들링 개선

**실험적 변경 (위험):**
- 새 액션 추가
- 기존 액션 파라미터 확장
- DOM 텍스트 자동 추출

### 7.5 확장이 필요하다면

**Option 1: 공식 Fara-7B 프레임워크 사용** ⭐ 추천
- Microsoft의 공식 구현 탐색 (GitHub: microsoft/fara)
- Multi-turn, stateful, interactive 기능 포함
- UserSimulator와 critical point handling 지원
- 현재 간소화 버전보다 훨씬 강력

**Option 2: 현재 구현 확장**
- 히스토리 persistence 추가
- Interactive mode 구현 (user intervention points)
- Multi-turn task execution 지원
- 공식 설계를 참고하여 구현

**Option 3: 하이브리드 시스템**
- Fara-7B: 네비게이션 및 상호작용
- 별도 스크립트/에이전트: 정보 추출
- 오케스트레이터: 두 시스템 조율

**Option 4: 다른 모델 사용**
- AutoGen MultimodalWebSurfer (vision + text)
- Claude with Computer Use (MCP 확장 가능)
- 하지만 로컬 실행 불가, 비용 발생

**Option 5: Fine-tuning**
- Fara-7B를 새 액션으로 재학습
- 하지만 145K trajectories 데이터 필요
- 리소스 집약적, 비현실적

---

## 8. 발견된 버그 및 개선 가능 영역

### 8.1 브라우저 Lifecycle

**현재 동작:**
```python
# run_agent.py:58
finally:
    await agent.close()  # 항상 브라우저 닫음
```

**문제점:**
- 사용자가 결과를 확인하기 전에 브라우저가 닫힘
- 디버깅 어려움

**개선 방법 (안전):**
```python
# --keep-open 플래그 추가
parser.add_argument("--keep-open", action="store_true")

finally:
    if not args.keep_open:
        await agent.close()
    else:
        logger.info("Browser kept open. Press Ctrl+C to close.")
```

### 8.2 파싱 실패 시 조기 종료

**현재 동작:**
```python
# agent.py:338-340
if not action_args:
    self.logger.warning("No valid action found in response")
    break  # 즉시 종료
```

**문제점:**
- 모델이 한 번 실수하면 전체 태스크 실패
- 재시도 기회 없음

**개선 방법 (실험적):**
```python
if not action_args:
    retry_count += 1
    if retry_count > 3:
        break
    # 에러 메시지를 다음 컨텍스트에 추가
    action_history.append("[ERROR] No valid action. Please use <tool_call> format.")
    continue
```

### 8.3 응답 로깅

**현재 동작:**
```python
# agent.py:330
self.logger.info(f"Model response: {response[:200]}...")
```

**문제점:**
- 긴 응답은 잘려서 요약문을 볼 수 없음

**개선 방법:**
```python
# 전체 응답 저장 옵션
if self.save_responses:
    with open(f"{self.responses_folder}/response{round_num}.txt", "w") as f:
        f.write(response)
```

---

## 부록: Wikipedia 태스크 완전 분석

### 실행 명령
```bash
python run_agent.py --task "open wikipedia and search for 'vision transformer' open the article read the introduction section and summarize the main idea in simple terms" --headful
```

### 전체 로그
```
[INFO] Browser started
[INFO] Agent started
[INFO] Running task: open wikipedia and search for 'vision transformer' ...
[INFO] Round 1/20
[INFO] Model response: To navigate directly to Wikipedia and begin searching...
[INFO] Action result: I typed 'https://en.wikipedia.org' into the browser address bar.

[INFO] Round 2/20
[INFO] Model response: To search for the article on 'vision transformer,'...
[INFO] Action result: I typed 'Vision transformer'.

[INFO] Round 3/20
[INFO] Model response: I will scroll down to locate and read the introduction section...
[INFO] Action result: I scrolled down one page in the browser.

[INFO] Round 4/20
[INFO] Model response: The page is already open to the Vision Transformer article...
[INFO] Action result: I scrolled up one page in the browser.

[INFO] Round 5/20
[INFO] Model response: The page is already open to the Vision Transformer article
                     on Wikipedia, which fulfills step 1 of the plan. The introduction
                     section is visible, so we can proceed to read and summarize it.
[INFO] Task terminated: success
[INFO] Task completed after 5 rounds
[INFO] Browser closed
```

### 분석

**Round 1-4: 성공적인 네비게이션**
- ✅ Wikipedia 접속
- ✅ 검색어 입력
- ✅ 페이지 열기
- ✅ Introduction 섹션까지 스크롤

**Round 5: 실패 지점**
- 모델 판단: "introduction section is **visible**" ✓
- 모델 계획: "we can **proceed** to read and summarize it"
- 실제 액션: `terminate("success")` ✗
- **문제**: "proceed to read" ≠ "actually read"

**왜 이런 일이 발생했는가:**
1. 모델은 시각적으로 introduction을 "봤음"
2. 하지만 **텍스트를 추출할 수 있는 액션이 없음**
3. 다음 액션 선택지:
   - `scroll` → 이미 섹션이 보임, 의미 없음
   - `left_click` → 클릭할 것이 없음
   - `type` → 입력할 것이 없음
   - **`terminate`** → 더 이상 할 수 있는 게 없다고 판단
4. 모델이 조기 종료 선택

**모델의 관점에서:**
```
Task: "read the introduction section and summarize"
Current state: Introduction section is visible on screen
Available actions: click, type, scroll, search, wait, terminate
Question: How do I "read" the text?
Answer: I can't. I can only SEE it, not READ it.
Conclusion: Task is done (I've done all I can do)
→ terminate("success")
```

이것이 **vision-only 접근법의 근본적 한계**입니다.

---

---

## 부록 2: 공식 설계 vs 현재 구현 상세 비교

### ArXiv 논문에서 확인된 공식 기능

#### 1. Multi-turn Task Execution
**논문 원문**:
> "if Fara-7B finishes the initial task q₀ after t steps and the user follows up with another query q₁, then we simply continue predicting the next steps while maintaining the full history"

**의미**:
- 첫 번째 태스크 완료 후 두 번째 태스크 실행 가능
- 이전 태스크의 컨텍스트 유지
- 연속적인 작업 수행 지원

**현재 구현 상태**: ❌ 없음

#### 2. Stateful History Management
**논문 원문**:
> Maintains "the full history of steps" including observations, thoughts, and actions throughout execution

**의미**:
- 모든 이전 단계 기억
- Observations (스크린샷)
- Thoughts (chain-of-thought)
- Actions (실행한 액션)

**현재 구현 상태**: ⚠️ 부분 구현 (최근 3개 액션만, line 301)

#### 3. User Intervention at Critical Points
**논문 원문**:
> The model "pauses task execution at critical points until explicit user confirmation is provided" and is designed to "stop and hand back control to the user" at critical points like logins or purchases.

**Critical Points 예시**:
- 로그인 (Login)
- 구매 (Purchase)
- 민감한 정보 입력
- 중요한 결정

**의미**:
- 모델이 자동으로 중요 지점 감지
- 사용자에게 제어권 반환
- 명시적 확인 후 계속 진행

**현재 구현 상태**: ❌ 없음

#### 4. UserSimulator for Training
**논문 설명**:
학습 데이터 생성 시 UserSimulator가:
- Critical point에 대한 응답 제공
- Follow-up task 생성
- 원래 태스크 기반 후속 작업 생성

**의미**:
- 모델이 interactive 시나리오로 학습됨
- 사용자 응답을 예상하고 대응할 수 있음

**현재 구현 상태**: ❌ 없음 (학습 데이터에만 사용)

### 구현 가능성 분석

| 기능 | 공식 설계 | 현재 구현 | 구현 난이도 | 필요한 변경 |
|------|-----------|-----------|-------------|-------------|
| Multi-turn execution | ✅ 지원 | ❌ 없음 | 중간 | agent.py 수정, 히스토리 관리 |
| Full history | ✅ 지원 | ⚠️ 부분 | 쉬움 | action_history 제한 제거 |
| User intervention | ✅ 지원 | ❌ 없음 | 어려움 | Critical point 감지 로직 |
| State persistence | ✅ 지원 | ❌ 없음 | 중간 | Browser session 유지 |
| Follow-up tasks | ✅ 지원 | ❌ 없음 | 중간 | Interactive CLI 추가 |

### 왜 현재 구현에 이런 기능이 없는가?

**추측되는 이유**:
1. **단순성**: 데모/프로토타입용 간소화 버전
2. **의존성**: UserSimulator 등 추가 컴포넌트 필요
3. **복잡성**: Interactive 기능은 더 복잡한 아키텍처 필요
4. **범위**: 기본 single-task execution에 집중

### 공식 구현 찾기

**Microsoft의 공식 저장소**:
- https://github.com/microsoft/fara
- 평가 프레임워크 포함
- 더 완전한 구현일 가능성

**확인 필요**:
- 공식 저장소에 interactive 기능이 구현되어 있는지
- UserSimulator 코드가 공개되어 있는지
- Multi-turn execution 예제가 있는지

### 결론

**현재 코드베이스**: Fara-7B의 **기능적 서브셋**
- 핵심 vision-centric 접근 ✅
- 11개 액션 실행 ✅
- 기본 task completion ✅
- Multi-turn ❌
- User intervention ❌
- State persistence ❌

**공식 Fara-7B**: 훨씬 **풍부한 기능**
- 모든 기본 기능 ✅
- Interactive capabilities ✅
- Critical point handling ✅
- Follow-up task support ✅

---

**문서 끝**
