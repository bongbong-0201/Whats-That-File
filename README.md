
# 🕵️‍♂️ Whats That File? (AI File Detective)

**"이 파일... 지워도 되는 걸까?"**
스팀 게임 모드 파일, 정체불명의 시스템 파일 때문에 고민하지 마세요.
AI 탐정(Gemini)이 파일의 내부를 뜯어보고(Forensic), 삭제해도 안전한지 알려줍니다.

## ✨ 주요 기능
- **🤖 AI 정밀 분석:** Google Gemini 1.5/2.0 모델을 연동하여 파일의 정체와 용도를 설명합니다.
- **🛡️ 게임/모드 특화:** Unity 엔진(.resS, .assets), Steam 게임 파일 분석에 강력합니다.
- **📂 폴더 스캔:** 폴더 내에서 가장 수상한(용량이 큰) 파일을 자동으로 찾아 분석합니다.
- **⚡ 초고속 스캔:** 대용량 파일은 해시 계산을 건너뛰어 멈춤 없이 분석합니다.

## 🚀 설치 및 실행 방법

1. **설치**
   ```bash
   git clone [https://github.com/님의아이디/FileDetective.git](https://github.com/님의아이디/FileDetective.git)
   cd FileDetective
   pip install -r requirements.txt

    ```

2. **실행**
    ```bash
    python detective_gui.py
    ```


3. **API 키 설정**
* 실행 후 Google Gemini API Key를 입력하세요. (자동 저장됨)
* [Get API Key Here](https://aistudio.google.com/)



## 🛠️ 기술 스택 (Tech Stack)

* **Language:** Python 3.10+
* **GUI:** Tkinter
* **AI:** Google Gemini API
* **Forensic Libs:** pefile, filetype

## 🙌 Credits & Acknowledgements

이 프로젝트는 다음 오픈소스 프로젝트와 도구들의 도움을 받아 제작되었습니다.

- **Google Gemini**: AI Pair Programmer (Code Generation & Debugging)
- **File Extension Database**: [dyne/file-extension-list](https://github.com/dyne/file-extension-list)
  - 확장자 식별을 위한 데이터베이스(`extensions.json`)로 사용되었습니다.
  - License: CC0-1.0 (Public Domain)
- **Google Gemini API**: 파일 심층 분석을 위한 AI 모델

## 🤝 기여하기 (Contributing)

이 프로젝트는 이제 막 시작되었습니다! 버그 제보나 기능 추가는 언제든 환영합니다.
(This project assumes use of AI-assisted coding tools.)

## 📜 License
This project is licensed under the **MIT License**.

*Note: The `extensions.json` file included in this repository is sourced from [dyne/file-extension-list](https://github.com/dyne/file-extension-list) and is dedicated to the public domain (CC0-1.0).*



**"Special Thanks to: Gemini (AI Pair Programmer)"**