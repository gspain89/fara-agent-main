# Fara-7B Agent 사용 가이드

## 📋 목차
- [기본 설정](#기본-설정)
- [실행 명령어](#실행-명령어)
- [종료 명령어](#종료-명령어)
- [10가지 실전 예제](#10가지-실전-예제)
- [플래그 설명](#플래그-설명)
- [트러블슈팅](#트러블슈팅)

---

## 기본 설정

### 필수 조건
1. **LM Studio** 실행 중이어야 함 (http://127.0.0.1:1234)
2. **Fara-7B 모델** 로드됨
3. **Python 환경** 활성화
4. **의존성 설치** 완료 (Playwright, asyncio 등)

### 시작 전 체크리스트
```bash
# 1. 프로젝트 디렉토리로 이동
cd /Users/gregyh/Coding/fara-agent-main

# 2. LM Studio가 실행 중인지 확인
curl http://127.0.0.1:1234/v1/models

# 3. (선택) 가상환경 활성화
# source venv/bin/activate  # 있다면
```

---

## 실행 명령어

### 기본 형식
```bash
python run_agent.py --task "작업 내용" [옵션]
```

### 사용 가능한 플래그
| 플래그 | 설명 | 기본값 |
|--------|------|--------|
| `--task` | 수행할 작업 (필수) | - |
| `--headful` | 브라우저 GUI 표시 | headless (GUI 없음) |
| `--keep-open` | 작업 완료 후 브라우저 유지 | 자동 종료 |
| `--config` | 설정 파일 경로 | config.json |

### 추천 사용법
```bash
# 디버깅/확인용 (브라우저 보이면서 유지)
python run_agent.py --task "작업" --headful --keep-open

# 일반 사용 (브라우저 숨김, 자동 종료)
python run_agent.py --task "작업"

# 헤드풀 모드만 (브라우저 보이지만 작업 후 자동 종료)
python run_agent.py --task "작업" --headful
```

---

## 종료 명령어

### 정상 종료
작업이 완료되면 자동으로 종료됩니다.

### 강제 종료
```bash
# 실행 중인 터미널에서
Ctrl + C

# --keep-open 사용 시:
# 1차 Ctrl+C: 브라우저 창 그대로 유지, 대기 중
# 2차 Ctrl+C: 브라우저 종료 및 프로그램 종료
```

### 백그라운드 프로세스 종료
```bash
# Python 프로세스 찾기
ps aux | grep "python run_agent.py"

# PID로 종료
kill -9 [PID]

# 또는 모든 Python 프로세스 종료 (주의!)
pkill -f "python run_agent.py"
```

### Chromium 좀비 프로세스 정리
```bash
# Playwright Chromium 프로세스 찾기
ps aux | grep chromium

# 종료
pkill -f chromium

# 또는 Playwright 캐시 정리
rm -rf ~/Library/Caches/ms-playwright
```

### LM Studio 종료
```bash
# LM Studio GUI에서 종료하거나

# 프로세스 종료
pkill -f "LM Studio"
```

---

## ⚠️ 중요: 현재 구현의 제약사항

### 현재 불가능한 작업
❌ **로그인이 필요한 작업** - 세션 유지 안 됨
❌ **텍스트 읽기/요약** - DOM 텍스트 추출 불가
❌ **연속 작업** - 한 번에 하나의 독립적 태스크만
❌ **사용자 개입 후 계속** - 중간에 멈추고 재개 불가

### 현재 가능한 작업
✅ **공개 정보 검색** - 로그인 불필요
✅ **웹사이트 네비게이션** - 클릭, 스크롤
✅ **폼 작성** - 타이핑, 버튼 클릭
✅ **스크린샷 기반 확인** - 페이지 도달 여부

---

## 10가지 실전 예제 (로그인 불필요)

### 지원되는 11개 액션
Fara-7B가 사용할 수 있는 액션:
1. `visit_url` - URL 방문
2. `web_search` - 웹 검색
3. `left_click` - 클릭
4. `type` - 텍스트 입력
5. `scroll` - 스크롤
6. `mouse_move` - 마우스 이동
7. `key` - 키보드 입력
8. `history_back` - 뒤로가기
9. `pause_and_memorize_fact` - 정보 저장
10. `wait` - 대기
11. `terminate` - 종료

---

### 예제 1: GitHub 공개 저장소 검색 (로그인 불필요)
**액션 사용**: `visit_url`, `type`, `left_click`
**적합성**: ✅ 완벽 (공개 접근)

```bash
cd /Users/gregyh/Coding/fara-agent-main

python run_agent.py \
  --task "Go to GitHub and search for 'playwright python' in the search box, then click on the first repository" \
  --headful --keep-open
```

**예상 동작**:
- GitHub.com 방문 (로그인 불필요)
- 검색창에 "playwright python" 입력
- 첫 번째 공개 저장소 클릭
- README가 보이는 페이지 도달

**주의**:
- ⚠️ README 내용을 "읽거나" "요약"하는 것은 불가능 (DOM 텍스트 추출 불가)
- ✅ 페이지 도달 및 시각적 확인만 가능

---

### 예제 2: Google 검색 및 결과 확인
**액션 사용**: `visit_url`, `type`, `key`, `left_click`
**적합성**: ✅ 완벽 (로그인 불필요)

```bash
python run_agent.py \
  --task "Go to Google and search for 'python tutorial for beginners', then click on the first result" \
  --headful --keep-open
```

**예상 동작**:
- Google.com 방문
- 검색창에 "python tutorial for beginners" 입력
- Enter 또는 검색 버튼 클릭
- 첫 번째 검색 결과 클릭

**실제 사용 예**:
- 특정 정보의 최상위 검색 결과 확인
- 웹사이트 접근성 테스트
- SEO 순위 확인 (수동)

---

### 예제 3: Google Maps 위치 검색 (로그인 불필요)
**액션 사용**: `visit_url`, `type`, `key`, `wait`
**적합성**: ✅ 좋음 (공개 지도)

```bash
python run_agent.py \
  --task "Go to Google Maps and search for 'Eiffel Tower Paris', wait 3 seconds for the map to load" \
  --headful --keep-open
```

**예상 동작**:
- Google Maps 열기
- 검색창에 "Eiffel Tower Paris" 입력
- Enter 키
- 지도 로딩 대기 (3초)

**실제 사용 예**:
- 특정 장소의 지도 위치 확인
- 여러 위치 비교 (스크린샷 저장)

**제약**:
- ⚠️ 경로 안내, 리뷰 읽기 등은 불가 (텍스트 추출 불가)

---

### 예제 4: YouTube 비디오 검색 (로그인 불필요)
**액션 사용**: `visit_url`, `type`, `key`, `scroll`, `left_click`
**적합성**: ✅ 좋음 (공개 비디오)

```bash
python run_agent.py \
  --task "Go to YouTube, search for 'machine learning tutorial', scroll down to see more results" \
  --headful --keep-open
```

**예상 동작**:
- YouTube.com 방문 (로그인 불필요)
- 검색창에 "machine learning tutorial" 입력
- 검색 실행
- 페이지 스크롤하여 더 많은 비디오 확인

**실제 사용 예**:
- 특정 주제의 비디오 검색 결과 확인
- 썸네일 및 제목 시각적 확인

**제약**:
- ⚠️ 비디오 재생, 댓글 읽기 불가
- ⚠️ 제목이나 설명 텍스트 추출 불가
- ✅ 클릭하여 비디오 페이지 이동까지는 가능

---

### 예제 5: Stack Overflow 검색 (로그인 불필요)
**액션 사용**: `visit_url`, `type`, `key`, `left_click`
**적합성**: ✅ 완벽 (공개 질문)

```bash
python run_agent.py \
  --task "Go to Stack Overflow and search for 'python asyncio error', then click on the first question" \
  --headful --keep-open
```

**예상 동작**:
- StackOverflow.com 방문
- 검색창에 "python asyncio error" 입력
- 첫 번째 질문 클릭
- 질문 페이지 도달 (답변 보임)

**실제 사용 예**:
- 특정 에러의 관련 질문 찾기
- 해결책이 있는지 시각적 확인
- 스크린샷으로 나중에 참고

**제약**:
- ⚠️ 답변 내용 읽기/요약 불가 (텍스트 추출 불가)
- ✅ 질문 페이지 도달 및 답변 존재 여부 확인 가능

---

### 예제 6: Twitter/X 공개 검색 (로그인 불필요)
**액션 사용**: `visit_url`, `type`, `key`
**적합성**: ✅ 좋음 (공개 트윗 검색)

```bash
python run_agent.py \
  --task "Go to Twitter and search for 'AI news' without logging in" \
  --headful --keep-open
```

**예상 동작**:
- Twitter.com 방문
- 검색 아이콘/창 찾기
- "AI news" 입력
- 검색 결과 페이지 표시 (일부 공개 트윗)

**실제 사용 예**:
- 특정 해시태그 트렌드 확인
- 공개 트윗 검색 결과 확인

**제약**:
- ⚠️ 로그인 없이는 제한된 결과만 표시
- ❌ 로그인 후 작업 불가 (세션 유지 안 됨)
- ⚠️ 트윗 내용 읽기 불가 (텍스트 추출 불가)

---

### 예제 7: Reddit 공개 서브레딧 검색 (로그인 불필요)
**액션 사용**: `visit_url`, `type`, `key`, `left_click`
**적합성**: ✅ 완벽 (공개 서브레딧)

```bash
python run_agent.py \
  --task "Go to Reddit, search for 'MachineLearning' subreddit, and click on it" \
  --headful --keep-open
```

**예상 동작**:
- Reddit.com 방문 (로그인 불필요)
- 검색창에 "MachineLearning" 입력
- r/MachineLearning 서브레딧 클릭
- 서브레딧 메인 페이지 표시

**실제 사용 예**:
- 특정 주제 커뮤니티 찾기
- 서브레딧 존재 여부 확인

**제약**:
- ⚠️ 포스트 내용 읽기 불가
- ⚠️ 댓글 확인 불가
- ✅ 서브레딧 레이아웃 및 인기 포스트 제목 시각적 확인 가능

---

### 예제 8: Hacker News 브라우징 (로그인 불필요)
**액션 사용**: `visit_url`, `scroll`, `left_click`, `history_back`
**적합성**: ✅ 완벽 (모든 콘텐츠 공개)

```bash
python run_agent.py \
  --task "Visit Hacker News, scroll down to see more posts, click on the 5th post title, then go back to the main page" \
  --headful --keep-open
```

**예상 동작**:
- news.ycombinator.com 방문
- 페이지 스크롤
- 5번째 포스트 제목 클릭
- 외부 링크 또는 토론 페이지 열림
- 뒤로가기로 Hacker News 메인 복귀

**실제 사용 예**:
- 인기 기술 뉴스 확인
- 특정 순위의 포스트 접근
- 네비게이션 테스트

**제약**:
- ⚠️ 댓글 내용 읽기 불가
- ⚠️ 기사 요약 불가
- ✅ 제목 및 점수 시각적 확인 가능

---

### 예제 9: 위키피디아 검색 및 네비게이션
**액션 사용**: `visit_url`, `type`, `key`, `left_click`, `scroll`
**적합성**: ✅ 완벽 (모든 콘텐츠 공개)

```bash
python run_agent.py \
  --task "Go to Wikipedia and search for 'Artificial Intelligence', click on the article, and scroll to see the table of contents" \
  --headful --keep-open
```

**예상 동작**:
- Wikipedia.org 방문
- 검색창에 "Artificial Intelligence" 입력
- 기사 클릭
- 목차까지 스크롤

**실제 사용 예**:
- 특정 주제 위키 기사 찾기
- 기사 구조 확인 (목차)
- 여러 언어 버전 비교

**제약**:
- ⚠️ 기사 내용 읽기/요약 불가 (치명적 제약!)
- ✅ 기사 존재 여부, 구조, 이미지 등 시각적 확인 가능

**참고**: 이것이 리포트의 Wikipedia 실패 사례입니다!

---

### 예제 10: 공개 폼 작성 테스트
**액션 사용**: `visit_url`, `type`, `left_click`, `scroll`
**적합성**: ✅ 좋음 (로그인 불필요한 폼)

```bash
python run_agent.py \
  --task "Go to example form at 'https://www.w3schools.com/html/html_forms.asp', scroll to find a text input, and type 'Test Input'" \
  --headful --keep-open
```

**예상 동작**:
- W3Schools 폼 예제 페이지 방문
- 페이지 스크롤
- 텍스트 입력 필드 찾기
- "Test Input" 타이핑

**실제 사용 예**:
- 웹 폼 자동화 테스트
- 입력 필드 찾기 능력 테스트
- UI/UX 테스트 자동화

**확장 가능성**:
- ✅ 드롭다운 선택
- ✅ 체크박스/라디오 버튼 클릭
- ✅ 제출 버튼 클릭
- ⚠️ 실제 제출 결과 확인은 제한적

---

## 플래그 설명

### --task (필수)
에이전트가 수행할 작업을 자연어로 기술합니다.

**✅ 좋은 예시 (실제 동작 가능):**
```bash
--task "Go to GitHub and search for 'fastapi'"
--task "Visit Google and search for 'weather Tokyo', then click the first result"
--task "Go to Wikipedia and search for 'Python programming', click the article"
```

**❌ 나쁜 예시 (현재 구현으로 불가능):**
```bash
--task "Do something"
# → 너무 모호함

--task "Read this article and summarize it in Korean"
# → 텍스트 추출/요약 불가 (치명적 제약)

--task "Login to Twitter and post a tweet"
# → 로그인 후 작업 불가 (세션 유지 안 됨)

--task "Go to Amazon, add item to cart, then checkout"
# → 다단계 작업 실패 가능성 높음, 로그인 필요

--task "Compare prices on 3 different websites"
# → 가격 텍스트 추출 불가
```

**⚠️ 주의사항:**
- 로그인이 필요한 작업은 **절대 불가**
- 텍스트 읽기/요약은 **절대 불가**
- 클릭, 스크롤, 타이핑, 네비게이션 위주로 작성

### --headful
브라우저 창을 표시합니다.

**사용 시기:**
- ✅ 디버깅할 때
- ✅ 에이전트 동작을 시각적으로 확인하고 싶을 때
- ✅ 데모/프레젠테이션용
- ❌ 백그라운드 자동화 작업 (느려짐)

### --keep-open
작업 완료 후 브라우저를 닫지 않고 유지합니다.

**사용 시기:**
- ✅ 최종 결과를 육안으로 확인하고 싶을 때
- ✅ 에이전트가 올바른 페이지에 도달했는지 검증
- ✅ 스크린샷 촬영 필요
- ❌ 자동화 스크립트 (메모리 누수 가능)

**종료 방법:**
```bash
# --keep-open 사용 시 표시되는 메시지:
# ============================================================
# Browser kept open (--keep-open flag)
# You can inspect the browser window now
# Press Ctrl+C to close the browser and exit
# ============================================================

# Ctrl+C 누르면 브라우저 종료 및 프로그램 종료
```

### --config
기본값이 아닌 다른 설정 파일을 사용합니다.

```bash
python run_agent.py \
  --task "작업" \
  --config custom_config.json
```

---

## 트러블슈팅

### 문제 1: "Connection refused" 에러
**원인**: LM Studio가 실행되지 않았거나 모델이 로드되지 않음

**해결:**
```bash
# LM Studio 상태 확인
curl http://127.0.0.1:1234/v1/models

# 응답이 없으면:
# 1. LM Studio 실행
# 2. Fara-7B 모델 로드
# 3. Local Server 시작 (포트 1234)
```

### 문제 2: "No valid action found in response"
**원인**: 모델이 유효한 <tool_call> 형식으로 응답하지 않음

**해결:**
- 더 구체적인 태스크 작성
- LM Studio에서 temperature를 0.0으로 설정 (config.json)
- 모델이 제대로 로드되었는지 확인

### 문제 3: 브라우저가 열리지 않음
**원인**: Playwright 설치 문제

**해결:**
```bash
# Playwright 재설치
pip install playwright
python -m playwright install chromium
```

### 문제 4: "Task terminated: success" but nothing happened
**원인**: 태스크가 Fara-7B의 capability를 벗어남

**대표적인 실패 사례:**
```bash
# 실패 예제 1: 텍스트 읽기
--task "Go to Wikipedia and read the introduction, then summarize it"
# → Round 5에서 "introduction is visible"만 확인하고 terminate
# → 텍스트 읽기 불가, 요약 없이 종료

# 실패 예제 2: 로그인 후 작업
--task "Login to Twitter and check my notifications"
# → 로그인 버튼까지는 도달하지만 실제 로그인 불가
# → 세션 유지 안 됨

# 실패 예제 3: 정보 추출
--task "Find the price of iPhone 15 on Amazon"
# → 제품 페이지까지 도달 가능
# → 가격 텍스트 추출 불가 (DOM 접근 없음)
```

**해결:**
- `FARA_ANALYSIS_REPORT.md` 참조
- Section 7.3 "적합한 사용 사례" 확인
- **클릭/스크롤/타이핑/네비게이션 위주로 제한**
- **로그인 불필요한 공개 작업만**

### 문제 5: 작업이 너무 느림
**원인**: headful 모드 사용 또는 네트워크 지연

**해결:**
```bash
# headless 모드로 실행 (더 빠름)
python run_agent.py --task "작업"

# temperature 낮추기 (config.json)
"temperature": 0.0

# max_rounds 줄이기
"max_rounds": 10
```

### 문제 6: 메모리 누수 / 좀비 프로세스
**원인**: --keep-open 사용 후 제대로 종료하지 않음

**해결:**
```bash
# 모든 관련 프로세스 정리
pkill -f "python run_agent.py"
pkill -f chromium

# Playwright 캐시 정리
rm -rf ~/Library/Caches/ms-playwright
```

---

## 로그 확인

### 스크린샷 저장 위치
```bash
cd /Users/gregyh/Coding/fara-agent-main/screenshots

# 최신 스크린샷 보기
ls -lt | head -10
```

### 다운로드 파일 위치
```bash
cd /Users/gregyh/Coding/fara-agent-main/downloads

ls -lt
```

---

## 성능 최적화 팁

### 1. headless 모드 사용
```bash
# GUI 없이 실행 (2배 이상 빠름)
python run_agent.py --task "작업"
```

### 2. Temperature 0으로 설정
```json
// config.json
{
  "temperature": 0.0  // 일관된 결과
}
```

### 3. max_rounds 조정
```json
// 간단한 작업은 rounds 줄이기
{
  "max_rounds": 10  // 기본 20
}
```

### 4. 구체적인 태스크 작성
```bash
# 나쁜 예
--task "Find something on Google"

# 좋은 예
--task "Go to Google and search for 'python tutorial', then click the first result"
```

---

## 예제 실행 체크리스트

실행 전 확인사항:
- [ ] LM Studio 실행 중 (http://127.0.0.1:1234)
- [ ] Fara-7B 모델 로드됨
- [ ] 터미널에서 프로젝트 디렉토리로 이동
- [ ] (옵션) --headful 플래그로 시각적 확인
- [ ] (옵션) --keep-open 플래그로 결과 확인

실행 예시:
```bash
cd /Users/gregyh/Coding/fara-agent-main

python run_agent.py \
  --task "Go to GitHub and search for 'pytorch'" \
  --headful --keep-open
```

작업 완료 후:
- [ ] 브라우저에서 결과 확인
- [ ] Ctrl+C로 종료 (--keep-open 사용 시)
- [ ] screenshots/ 폴더에서 과정 확인

---

## 부록: 현실적인 사용 사례 가이드

### ✅ 완벽하게 작동하는 작업

**1. 공개 정보 검색 및 네비게이션**
- Google/Bing 검색 → 결과 클릭
- Wikipedia 기사 찾기 → 섹션으로 스크롤
- GitHub 저장소 검색 → 저장소 열기
- Stack Overflow 질문 검색 → 질문 페이지 열기

**2. 웹사이트 탐색**
- Hacker News 브라우징 → N번째 포스트 클릭
- Reddit 서브레딧 찾기 → 메인 페이지 열기
- YouTube 검색 → 비디오 목록 확인

**3. 폼 상호작용 (로그인 불필요)**
- 검색창에 텍스트 입력
- 버튼 클릭
- 드롭다운 선택
- 체크박스/라디오 버튼

### ⚠️ 제한적으로 작동하는 작업

**1. 시각적 확인만 가능**
- 페이지 레이아웃 확인 ✅
- 이미지 존재 여부 ✅
- 버튼/링크 위치 파악 ✅
- 하지만 텍스트 내용 읽기 ❌

**2. 첫 단계만 가능**
- 로그인 페이지까지 이동 ✅
- 로그인 버튼 클릭 ✅
- 하지만 실제 로그인 및 이후 작업 ❌

**3. 네비게이션만 가능**
- 제품 페이지 도달 ✅
- 가격 위치 시각적 확인 ✅
- 하지만 가격 값 추출 ❌

### ❌ 절대 작동하지 않는 작업

**1. 텍스트 추출/분석**
```bash
# 모두 실패
--task "Read and summarize this article"
--task "Extract the product price"
--task "Get the top 3 comments"
--task "Compare information from two pages"
```

**2. 로그인 필요 작업**
```bash
# 모두 실패 (로그인까지는 가능하지만 이후 불가)
--task "Login and check my messages"
--task "Post a tweet"
--task "Upload a file to Drive"
--task "Send an email"
```

**3. 복잡한 다단계 작업**
```bash
# 실패 가능성 높음
--task "Compare prices across 3 websites and tell me the cheapest"
--task "Find all broken links on this page"
--task "Download the PDF and extract text"
```

### 💡 현실적인 활용 방안

**1. 반복적인 네비게이션 자동화**
- 매일 특정 페이지 방문하여 스크린샷 저장
- 정기적인 웹사이트 접근성 테스트

**2. 탐색 경로 기록**
- 복잡한 웹사이트의 네비게이션 경로 문서화
- UI 변경 사항 모니터링 (시각적)

**3. 기본 폼 테스트**
- 검색 기능 동작 여부 확인
- 버튼 클릭 가능성 테스트

**4. 스크린샷 기반 비교**
- 다양한 검색어에 대한 결과 페이지 캡처
- 시간대별 웹사이트 레이아웃 변화 추적

---

## 결론: 현재 구현의 한계

현재 구현(`fara-agent-main`)은:
- ✅ **네비게이션 자동화**: 우수
- ✅ **시각적 확인**: 가능
- ⚠️ **정보 추출**: 불가능 (치명적)
- ❌ **로그인 작업**: 불가능
- ❌ **연속 작업**: 불가능

**공식 Fara-7B 설계**는 더 많은 기능을 지원하지만,
이 코드베이스는 **간소화된 데모 버전**입니다.

자세한 내용은 `FARA_ANALYSIS_REPORT.md` 참조.

---

**문서 버전**: 2.0
**작성일**: 2025-12-11
**업데이트**:
- v1.0: --keep-open 플래그 추가
- v2.0: 현실적인 예제로 전면 개편, 제약사항 명확화
