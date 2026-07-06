# EchoLens AI 광고 프로젝트

EchoLens AI Smart Glasses를 주제로 한 10초 이내 멀티모달 광고 제작 프로젝트이다. 여행자는 여행 자체에 집중하고, AI가 여행자의 시선을 기록해 하나의 여행 영상으로 완성한다는 브랜드 메시지를 전달한다.

> **핵심 메시지:** “액션캠 없이 여행을 기록하는 시대가 왔다.”  
> **슬로건:** *Travel Free. Record Smart.*

## 목차

- [프로젝트 소개](#프로젝트-소개)
- [결과물](#결과물)
- [폴더 구조](#폴더-구조)
- [사용 AI 및 도구](#사용-ai-및-도구)
- [제작 과정](#제작-과정)
- [Prompt Engineering](#prompt-engineering)
- [실행 및 확인 방법](#실행-및-확인-방법)
- [기능 요구사항 체크리스트](#기능-요구사항-체크리스트)
- [제약사항 대응](#제약사항-대응)
- [보너스 과제](#보너스-과제)
- [제출 전 최종 체크리스트](#제출-전-최종-체크리스트)
- [최종 결과](#최종-결과)

## 프로젝트 소개

| 항목 | 내용 |
|---|---|
| 브랜드 | EchoLens |
| 제품 | EchoLens AI Smart Glasses |
| 광고 목적 | 브랜드 인지도 향상 |
| 타겟 | 여행 크리에이터, 일반 여행객 |
| USP | 액션캠 없이 여행자의 시선을 AI가 자동으로 기록하고 최고의 여행 영상으로 완성한다. |
| Tone & Manner | Apple의 프리미엄 감성, GoPro의 역동적인 여행, 영화 같은 시네마틱 연출 |
| Brand Story | 여행자는 경험에 집중하고, AI는 여행자의 시선을 기록해 하나의 여행 이야기로 완성한다. |
| Core Value | 여행 몰입, 자연스러운 기록, 스마트한 완성 |
| 광고 구성 | Scene 1~5, 총 10초 이내 |
| 화면 비율 | 16:9 |

## 결과물

### 최종 광고 영상

- [16:9 버전 — EchoLens_AI_Travel_Commercial_10s.mp4](02_광고_영상/EchoLens_AI_Travel_Commercial_10s.mp4)
- [9:16 버전 — EchoLens_AI_Travel_Commercial_9x16.mp4](02_광고_영상/EchoLens_AI_Travel_Commercial_9x16.mp4)

| 버전 | 경로 | 실제 확인 규격 |
|---|---|---|
| 16:9 | `02_광고_영상/EchoLens_AI_Travel_Commercial_10s.mp4` | MP4, 10초, 1920×1080, 30fps, H.264 |
| 9:16 | `02_광고_영상/EchoLens_AI_Travel_Commercial_9x16.mp4` | MP4, 10초, 1080×1920, 30fps |

### 문서

- [최종 스토리보드](01_스토리보드_기획/EchoLens_스토리보드.md)
- [스토리보드 PDF](01_스토리보드_기획/EchoLens_스토리보드.pdf)
- [브랜드 아이덴티티](01_스토리보드_기획/01_브랜드_아이덴티티.md)
- [Style Guide](03_제작_자료/Prompts/style_guide.md)
- [Image Prompt Guide](03_제작_자료/Prompts/image_prompts.md)
- [Video Prompt Guide](03_제작_자료/Prompts/video_prompts.md)
- [Audio Prompt Guide](03_제작_자료/Prompts/audio_prompts.md)
- [Prompt Revision](03_제작_자료/Prompts/prompt_revision.md)
- [제작 과정 기록](03_제작_자료/제작_과정.md)

### 저장소에서 확인되는 영상

| Scene | 실제 파일 | 확인 상태 |
|---|---|---|
| Scene 2 | [scene02_motion.mp4](03_제작_자료/Videos/scene02_motion.mp4) | 파일 확인, Windows 메타데이터상 약 3초 |
| Scene 3 | [scene03_motion.mp4](03_제작_자료/Videos/scene03_motion.mp4) | 파일 확인, Windows 메타데이터상 약 3초 |
| Scene 3 Pika 재제작 | [scene03_pika_remake.mp4](03_제작_자료/Videos/scene03_pika_remake.mp4) | 파일 확인, 5초, 784×470, 30fps |
| Scene 4 | [scene04_motion.mp4](03_제작_자료/Videos/scene04_motion.mp4) | 파일 확인, Windows 메타데이터상 약 3초 |

Scene 1·5 개별 영상, 이미지 원본, 오디오 원본과 CapCut 프로젝트 파일은 현재 저장소에서 확인되지 않는다. 최종 합본 영상은 `02_광고_영상/EchoLens_AI_Travel_Commercial_10s.mp4`에서 확인된다.

대표 이미지는 현재 저장소에 포함되어 있지 않으며, 최종 광고 영상과 Scene 2~4 원본 영상으로 결과물을 확인한다.

## 폴더 구조

```text
.
├─ README.md
├─ 01_스토리보드_기획/
│  ├─ 01_브랜드_아이덴티티.md
│  ├─ 02_스토리보드.md
│  ├─ EchoLens_스토리보드.md
│  └─ EchoLens_스토리보드.pdf
├─ 02_광고_영상/
│  ├─ EchoLens_AI_Travel_Commercial_10s.mp4
│  └─ EchoLens_AI_Travel_Commercial_9x16.mp4
├─ 03_제작_자료/
│  ├─ Assets/
│  ├─ Images/
│  ├─ Videos/
│  │  ├─ scene02_motion.mp4
│  │  ├─ scene03_motion.mp4
│  │  ├─ scene03_pika_remake.mp4
│  │  └─ scene04_motion.mp4
│  ├─ Prompts/
│  │  ├─ style_guide.md
│  │  ├─ image_prompts.md
│  │  ├─ video_prompts.md
│  │  ├─ audio_prompts.md
│  │  └─ prompt_revision.md
│  └─ 제작_과정.md
```

기본 제작 자료 경로는 `03_제작_자료/`로 통일한다.

## 사용 AI 및 도구

| 단계 | 도구 | 선택 이유 | 장점 | 확인된 한계 |
|---|---|---|---|---|
| 이미지 생성 | ChatGPT 이미지 생성 | 사실적인 이미지와 일관된 시네마틱 스타일 생성 | Scene별 영어 Prompt와 Negative Prompt를 함께 관리 가능 | 캐릭터와 제품 디자인의 일관성을 Prompt로 반복 관리해야 함 |
| 영상 생성 | Kling AI | 정지 이미지를 자연스러운 카메라 움직임으로 변환 | 여행 장면의 역동성과 짧은 모션 구현 | 크레딧 제약이 있어 생성 범위를 조정해야 했음 |
| 비교 영상 생성 | Pika | 동일 스토리보드의 Scene 3 비교 실험과 보너스 과제 수행 | 자연스러운 셀피 움직임 | 인물 및 제품 디자인 일관성 부족 |
| 오디오 기획 | Suno AI | 초기 10초 BGM Prompt 기록 | 시네마틱하고 점차 고조되는 음악 방향을 Prompt로 정리 가능 | 최종 영상의 실제 BGM 소스로는 사용하지 않음 |
| BGM·영상 편집 | CapCut | 라이브러리 BGM `Cinematic Epic Inspiration` 적용 및 생성 결과 통합 | 컷 편집, 전환, 색보정, 오디오 레벨 조정과 Export 가능 | 핵심 시각 요소 생성에는 사용하지 않음 |

최종 오디오는 CapCut 라이브러리 BGM `Cinematic Epic Inspiration`만 사용했다. Suno AI Prompt와 Scene별 내레이션 문구는 기획 기록이며, TTS 내레이션은 실제로 생성하거나 최종 영상에 사용하지 않았다.

### 최종 영상 기준 Scene 구성

| 시간 | 실제 Scene | 화면 내용 |
|---|---|---|
| 0~3초 | Scene 3 | 해안 절벽의 여행 크리에이터와 EchoLens 착용 장면 |
| 3~6초 | Scene 2 | 바다·도시·산의 3분할 1인칭 POV 여행 장면 |
| 6~8초 | Scene 4 | 여행 클립을 정리하는 EchoLens AI 편집 UI |
| 8~10초 | Scene 5 | EchoLens 로고, 슬로건, CTA 브랜드 엔딩 |

Scene 1의 공항 POV 장면은 최종 영상에 사용하지 않았다. Scene 2~4에는 `KlingAI 3.0` 워터마크가 표시된다.

최종 브랜드 엔딩에는 `EchoLens`, `Travel Free. Record Smart.`, `Start your journey with EchoLens.`가 화면 문구로 표시된다. 브랜드 철학, USP와 핵심 메시지 전문은 별도 화면 문구로 표시되지 않고 제품 착용, 여행 장면, AI 편집 UI의 흐름으로 전달된다.

## 제작 과정

```text
Image 생성 → Video 생성 → Audio 기획 → CapCut BGM·편집 → Export
```

1. 브랜드 아이덴티티와 Style Guide를 기준으로 Scene별 이미지 Prompt를 작성했다.
2. Kling AI용 카메라 움직임과 장면 전환 Prompt를 작성하고 영상으로 변환했다.
3. Suno AI용 BGM Prompt와 내레이션 문구를 기획 기록으로 남겼으며, 최종 영상에는 CapCut 라이브러리의 `Cinematic Epic Inspiration`만 사용했다. TTS 내레이션은 사용하지 않았다.
4. CapCut에서 생성 결과물을 배열하고 컷 편집, 전환, 색보정, 오디오 레벨, 브랜드 엔딩을 조정했다.
5. Scene 3을 오프닝으로 재구성하고 Scene 5는 정지 이미지와 Fade 효과로 처리한 뒤 10초 MP4로 Export했다.

세부 기록은 [제작 과정 문서](03_제작_자료/제작_과정.md)에 정리되어 있다.

## Prompt Engineering

Scene 1의 초기 Prompt는 1인칭 POV와 EchoLens 착용 장면을 동시에 요구했다. 1인칭 시점에서는 착용자의 얼굴과 제품 노출이 자연스럽지 않아, 수정 후 Prompt에서는 POV 여행 시작에만 집중하고 제품 노출을 Scene 3으로 분리했다.

```text
수정 전: first-person POV + wearing EchoLens AI smart glasses
수정 후: first-person POV + no visible smart glasses
```

전체 수정 전·후 Prompt와 결과 차이는 [Prompt Revision](03_제작_자료/Prompts/prompt_revision.md)에서 확인할 수 있다.

## 실행 및 확인 방법

이 프로젝트는 실행형 프로그램이 아니라 광고 제작 결과와 Markdown 기록으로 구성된다.

1. GitHub에서 [최종 스토리보드](01_스토리보드_기획/EchoLens_스토리보드.md)를 연다.
2. `03_제작_자료/Prompts/`에서 이미지·영상·오디오 Prompt와 수정 기록을 확인한다.
3. `03_제작_자료/Videos/`에서 저장소에 포함된 Scene 2~4 Kling 원본 영상을 확인한다.
4. [16:9 최종 광고](02_광고_영상/EchoLens_AI_Travel_Commercial_10s.mp4)와 [9:16 최종 광고](02_광고_영상/EchoLens_AI_Travel_Commercial_9x16.mp4)를 재생해 10초 구성, 브랜드 엔딩, 슬로건과 CTA를 확인한다.

## 기능 요구사항 체크리스트

완료 표시는 프로젝트 문서와 사용자 확인을 기준으로 하며, 원본 파일의 저장소 포함 여부는 [결과물](#결과물)에 별도로 표시했다.

- [x] 브랜드 정의
- [x] 캠페인 목표 및 핵심 메시지
- [x] 스토리보드 작성
- [x] Scene별 필수 필드 작성
- [x] Prompt 수정 전/후 기록
- [x] 이미지 AI 사용
- [x] 비디오 AI 사용
- [x] 오디오 생성 소스 사용
- [x] 10초 이하 광고
- [x] AI 생성 시각 요소
- [x] 청각 요소 포함
- [x] 마지막 구간 브랜드명/슬로건/CTA 포함

## 제약사항 대응

| 제약사항 | 적용 내용 |
|---|---|
| 직접 촬영 영상 미사용 | 핵심 시각 요소는 직접 촬영 없이 생성형 AI 결과물을 사용했다. |
| 유료 스톡 영상 미사용 | 유료 스톡 영상 대신 생성형 AI 시각 요소를 사용했다. |
| CapCut 사용 범위 | 컷 편집, 전환, 색보정, 오디오 레벨 조정과 Export에 사용했다. |
| Kling 크레딧 부족 대응 | Scene 수를 조정하고 Scene 3을 오프닝으로 재구성했다. |
| Scene 5 처리 | 추가 영상을 생성하지 않고 정지 이미지와 Fade 효과로 구성했다. |
| Character Consistency 활용 | 동일한 인물, 복장, 제품 디자인, 색감 키워드를 반복해 Scene 간 일관성을 관리했다. |

## 보너스 과제

| 항목 | 수행 여부 |
|---|---|
| Lip-sync | 미수행 |
| 동일 스토리보드 다른 도구 재제작 | 수행 — Scene 3을 Pika로 재제작 |
| 플랫폼별 화면비 버전 제작 | 수행 — 9:16 세로 버전 제작 완료 |

### Scene 3 도구 비교

| 항목 | Kling AI | Pika |
|------|-----------|------|
| 재제작 Scene | Scene 3 | Scene 3 |
| 생성 방식 | Image to Video | Text to Video |
| 장점 | 높은 일관성 | 자연스러운 셀피 움직임 |
| 한계 | 크레딧 제한 | 인물 및 제품 디자인 일관성 부족 |

Pika 결과는 해안 절벽, 셀피 구도, AI 스마트글래스 콘셉트를 유지했다. 다만 생성형 AI 특성으로 Kling 원본의 남성 인물이 여성 인물로 바뀌고, 슬림한 안경이 넓은 바이저형 디자인으로 달라졌다. Pika는 최종 광고 교체가 아니라 비교 실험 및 보너스 과제 수행 목적으로만 사용했다.

9:16 버전은 CapCut에서 16:9 원본을 기반으로 Scene별 확대와 위치를 조정해 제작했으며, Shorts, Reels, TikTok 세로 화면 활용을 목적으로 한다.

## 제출 전 최종 체크리스트

- [x] 최종 광고 영상 MP4 존재
- [x] 최종 영상 10초 이내
- [x] 1080p / 30fps / H.264 기준 Export
- [x] 브랜드명, 슬로건, CTA 포함
- [x] TTS 내레이션 미사용 기록
- [x] CapCut BGM 사용 기록
- [x] Scene 1 최종 미사용 기록
- [x] Scene 5 정지 이미지 Fade 처리 기록
- [x] Scene 3 Pika 비교 재제작 완료
- [x] 9:16 플랫폼별 화면비 버전 제작 완료
- [x] 스토리보드 PDF 생성 완료

## 최종 결과

초기 스토리보드는 Scene 1~5 순서로 기획했다. 최종 EchoLens 광고는 제품 소개(Scene 3)를 오프닝으로 시작하고, 세계 여행 하이라이트(Scene 2), AI 자동 편집 UI(Scene 4), 브랜드 엔딩(Scene 5)으로 마무리된다. Scene 1은 최종 영상에 사용하지 않았고, Scene 5는 별도 영상 생성 없이 정지 이미지와 Fade 효과로 처리했다.

최종 광고 영상은 [02_광고_영상/EchoLens_AI_Travel_Commercial_10s.mp4](02_광고_영상/EchoLens_AI_Travel_Commercial_10s.mp4)에 저장되어 있다. 실제 파일은 MP4, 10초, 1920×1080, 30fps, H.264로 확인된다. 실제 순서는 Scene 3(0-3초), Scene 2(3-6초), Scene 4(6-8초), Scene 5(8-10초)이며 Scene 1은 사용하지 않았다. Scene 5는 정지 이미지 Fade로 처리했고, CapCut 라이브러리 BGM `Cinematic Epic Inspiration`을 사용했다. TTS 내레이션은 사용하지 않았다.

플랫폼별 화면비 보너스 과제로 [9:16 세로 버전](02_광고_영상/EchoLens_AI_Travel_Commercial_9x16.mp4)을 추가 제작했다. 이 파일은 MP4, 10초, 1080×1920, 30fps로 확인되며 Shorts, Reels, TikTok 세로 화면에 활용할 수 있다.
