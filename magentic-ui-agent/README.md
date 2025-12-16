# Magentic-UI Agent with LM Studio

FARA-7B 모델을 LM Studio에서 실행하고 Magentic-UI로 제어하는 설정입니다.

## 아키텍처

```
magentic-ui (8081) → LM Studio (1234)
```

### 왜 Proxy가 없나요?

Magentic-UI의 FARA 에이전트는 **FARA-7B의 `<tool_call>` XML 형식을 직접 파싱**합니다.

**작동 방식**:
```
1. LM Studio → "<tool_call>{...}</tool_call>" (XML)
2. Magentic-UI FARA Agent → XML 파싱 내장
3. 브라우저 동작 실행 ✅
```

Proxy는 불필요하며, 오히려 충돌을 유발했습니다.

## 설치

### 1. 의존성 설치

```bash
cd magentic-ui-agent
pip install -r requirements.txt
```

### 2. LM Studio 설정

1. LM Studio 실행
2. FARA-7B 모델 로드
3. 서버 시작 (포트 1234)
4. 확인:
   ```bash
   curl http://127.0.0.1:1234/v1/models
   ```

## 실행

### Magentic-UI 실행

```bash
cd magentic-ui-agent
magentic-ui --fara --port 8081 --config fara_config.yaml
```

브라우저에서 접속: **http://localhost:8081**

**주의**: Proxy는 사용하지 않습니다. LM Studio에 직접 연결합니다.

## 설정 파일

### fara_config.yaml

```yaml
base_url: http://127.0.0.1:1234/v1  # LM Studio 직접 연결
model: "microsoft_fara-7b"           # LM Studio 모델 이름 형식
```

**중요**: `base_url`은 LM Studio(포트 1234)를 직접 가리킵니다. Proxy는 사용하지 않습니다.

## 문제 해결

### Magentic-UI가 LM Studio에 연결하지 못함

**증상**: `Connection refused` 오류

**해결책**:
1. LM Studio가 실행 중인지 확인
2. 포트 1234에서 리스닝하는지 확인:
   ```bash
   curl http://127.0.0.1:1234/v1/models
   ```
3. `fara_config.yaml`의 `base_url`이 `http://127.0.0.1:1234/v1`인지 확인
4. 방화벽 설정 확인

### Tool calling이 작동하지 않음

**증상**: 에이전트가 도구를 사용하지 못함

**확인 사항**:
1. LM Studio가 `<tool_call>` 형식으로 응답하는지 확인
2. Magentic-UI 로그에서 "Error parsing thoughts and action" 확인
3. FARA-7B 모델이 올바르게 로드되었는지 확인

### 모델 이름 오류

**증상**: "Model not found"

**해결책**: `fara_config.yaml`에서 모델 이름 변경 시도
```yaml
# 옵션 1 (HuggingFace 형식)
model: "microsoft/Fara-7B"

# 옵션 2 (LM Studio 형식)
model: "microsoft_fara-7b"
```

## Vision 지원

현재 설정은 vision(이미지 입력)을 지원합니다.

**이미지 형식**: base64 인코딩된 PNG
```json
{
  "type": "image_url",
  "image_url": {"url": "data:image/png;base64,..."}
}
```

Playwright 에이전트와 동일한 방식으로 작동합니다.

## 비교: Playwright vs Magentic-UI

| 항목 | Playwright Agent | Magentic-UI Agent |
|------|------------------|-------------------|
| **위치** | `../playwright-agent/` | `./` (현재 폴더) |
| **실행** | `python run_agent.py --task "..."` | `magentic-ui --fara` |
| **UI** | 없음 (CLI) | 웹 UI (포트 8081) |
| **승인** | 없음 (자동 실행) | Co-planning (사용자 승인) |
| **속도** | 빠름 | 보통 (오케스트레이션 오버헤드) |
| **안전성** | 낮음 | 높음 (Action guards) |
| **학습** | 없음 | Plan learning |
| **병렬화** | 없음 | 다중 작업 동시 실행 |

**권장 사용**:
- **Playwright**: 빠른 자동화, 헤드리스 실행, 스크립트
- **Magentic-UI**: 복잡한 작업, 사용자 감독, 인터랙티브 계획

## 참고 자료

- [Magentic-UI GitHub](https://github.com/microsoft/magentic-ui)
- [FARA-7B Model](https://huggingface.co/microsoft/Fara-7B)
- [LM Studio Documentation](https://lmstudio.ai/docs)

## 라이선스

MIT (부모 프로젝트와 동일)
