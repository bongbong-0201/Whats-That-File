import os
import sys
import datetime
import hashlib
import json
import re
import filetype
import pefile
import zipfile
import xml.etree.ElementTree as ET
import google.generativeai as genai

class FileDetective:
    # 확장자 사전 (클래스 변수)
    EXTENSION_DB = {}

    def __init__(self, file_path):
        self.file_path = os.path.abspath(file_path)
        self.file_name = os.path.basename(file_path)
        self.report = {}
        
        # 확장자 사전 로드 (최초 1회)
        if not FileDetective.EXTENSION_DB:
            self._load_extension_db()

    def _load_extension_db(self):
        """같은 폴더에 있는 extensions.json 파일을 로드"""
        db_path = os.path.join(os.path.dirname(__file__), "extensions.json")
        try:
            if os.path.exists(db_path):
                with open(db_path, 'r', encoding='utf-8') as f:
                    FileDetective.EXTENSION_DB = json.load(f)
        except Exception:
            pass # 없으면 없는 대로 진행

    def run_investigation(self):
        """수사를 시작하고 결과(딕셔너리)를 반환"""
        if not os.path.exists(self.file_path):
            return {"error": "파일을 찾을 수 없습니다."}

        # 1. 기본 신상 정보
        self.report['basic_info'] = {
            'name': self.file_name,
            'path': self.file_path,
            'size_bytes': os.path.getsize(self.file_path),
            'extension': os.path.splitext(self.file_name)[1].lower()
        }

        # 2. 시간의 흔적
        stats = os.stat(self.file_path)
        self.report['time_evidence'] = {
            'created': self._format_time(stats.st_ctime),
            'modified': self._format_time(stats.st_mtime),
            'last_accessed': self._format_time(stats.st_atime)
        }

        # 3. 출생의 비밀 (ADS & 경로)
        self.report['origin_evidence'] = self._get_origin_info()

        # 4. 유전자 정보 (매직 넘버 & 해시)
        self.report['structure_evidence'] = self._get_structure_info()

        # [NEW] 사전 검색 & 카테고리 확인
        clean_ext = self.report['basic_info']['extension'].replace('.', '').lower()
        
        # filetype 라이브러리가 찾은 진짜 확장자가 있으면 그걸 우선시함
        real_ext = self.report['structure_evidence']['guessed_ext']
        if real_ext == 'unknown':
            real_ext = clean_ext

        # DB 조회
        db_data = FileDetective.EXTENSION_DB.get(real_ext)
        if db_data:
            # 데이터가 리스트면 첫 번째 항목 사용 (예: ["code", "web"] -> "code")
            category = db_data if isinstance(db_data, str) else db_data
            self.report['category_info'] = {
                "type": category,
                "found": True
            }
        else:
            self.report['category_info'] = {"type": "unknown", "found": False}


        # 5. 심층 분석 (개발자의 자백, 오피스, 압축 등)
        if real_ext in ['exe', 'dll', 'sys', 'msi']:
            self.report['developer_confession'] = self._get_pe_metadata()
        
        elif real_ext in ['pptx', 'docx', 'xlsx']:
            self.report['office_metadata'] = self._get_office_metadata()
            
        elif real_ext in ['zip', 'apk', 'jar']: # APK, JAR도 ZIP 구조
            self.report['zip_contents'] = self._get_zip_contents()
            
        else:
            # 텍스트 파일 등은 내용 읽기 (10KB 미만은 통째로, 그 외는 추출)
            if self.report['basic_info']['size_bytes'] < 10240: 
                try:
                    with open(self.file_path, 'r', encoding='utf-8', errors='ignore') as f:
                         self.report['internal_strings'] = [f.read()]
                except:
                    self.report['internal_strings'] = self._extract_strings(limit_mb=1)
            else:
                self.report['internal_strings'] = self._extract_strings(limit_mb=1)

        # 6. 주변 탐문 수사 (같은 폴더 파일들)
        self.report['neighborhood'] = self._get_neighbors()

        # 7. 추적 링크 생성
        search_query = self.file_name
        if self.report['origin_evidence'].get('steam_context'):
            game_id = self.report['origin_evidence']['steam_context'].get('game_id')
            if game_id:
                search_query += f" steam {game_id}"
        
        self.report['trace_link'] = f"https://www.google.com/search?q={search_query}"

        return self.report

    # --- Helper Methods ---
    def _format_time(self, timestamp):
        return datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')

    def _get_origin_info(self):
        evidence = {'download_source': None, 'steam_context': None}
        ads_path = self.file_path + ":Zone.Identifier"
        if os.path.exists(ads_path):
            try:
                with open(ads_path, 'r', encoding='utf-8', errors='ignore') as f:
                    match = re.search(r'HostUrl=(.+)', f.read())
                    if match: evidence['download_source'] = match.group(1).strip()
            except: pass
        
        if "steamapps" in self.file_path.lower():
            match = re.search(r'content\\(\d+)\\(\d+)', self.file_path)
            if match:
                evidence['steam_context'] = {'game_id': match.group(1), 'mod_id': match.group(2)}
        return evidence

    def _get_structure_info(self):
        kind = filetype.guess(self.file_path)
        mime = kind.mime if kind else "unknown"
        ext = kind.extension if kind else "unknown"

        # 300MB 이상 해시 생략
        limit_size = 300 * 1024 * 1024 
        file_size = self.report['basic_info']['size_bytes']
        
        if file_size < limit_size:
            sha256 = hashlib.sha256()
            try:
                with open(self.file_path, "rb") as f:
                    for b in iter(lambda: f.read(4096), b""): sha256.update(b)
                f_hash = sha256.hexdigest()
            except: f_hash = "Error"
        else:
            f_hash = "Skipped (Too Large)"

        return {'real_type': mime, 'guessed_ext': ext, 'file_hash_sha256': f_hash}

    def _get_pe_metadata(self):
        data = {}
        try:
            pe = pefile.PE(self.file_path)
            if hasattr(pe, 'FileInfo'):
                for entry in pe.FileInfo[0]:
                    if hasattr(entry, 'StringTable'):
                        for st in entry.StringTable:
                            for k, v in st.entries.items():
                                key = k.decode('utf-8', errors='ignore')
                                val = v.decode('utf-8', errors='ignore')
                                if key in ['CompanyName', 'FileDescription', 'OriginalFilename', 'ProductName']:
                                    data[key] = val
        except: pass
        return data

    def _get_office_metadata(self):
        metadata = {}
        try:
            if zipfile.is_zipfile(self.file_path):
                with zipfile.ZipFile(self.file_path, 'r') as z:
                    if 'docProps/core.xml' in z.namelist():
                        with z.open('docProps/core.xml') as f:
                            root = ET.parse(f).getroot()
                            ns = {'dc': 'http://purl.org/dc/elements/1.1/', 'cp': 'http://schemas.openxmlformats.org/package/2006/metadata/core-properties'}
                            creator = root.find('dc:creator', ns)
                            title = root.find('dc:title', ns)
                            if creator is not None: metadata['author'] = creator.text
                            if title is not None: metadata['title'] = title.text
        except: pass
        return metadata

    def _get_zip_contents(self):
        contents = {"file_list": []}
        try:
            with zipfile.ZipFile(self.file_path, 'r') as z:
                l = z.namelist()
                contents['file_list'] = l[:10]
                if len(l) > 10: contents['file_list'].append(f"...외 {len(l)-10}개")
        except: contents['error'] = "압축 열기 실패"
        return contents

    def _extract_strings(self, limit_mb=1):
        strings = []
        try:
            with open(self.file_path, 'rb') as f:
                content = f.read(limit_mb * 1024 * 1024)
                matches = re.findall(b'[a-zA-Z0-9\s_\-\.\(\)]{4,}', content)
                for m in matches[:20]:
                    try: 
                        d = m.decode('ascii').strip()
                        if len(d) > 3: strings.append(d)
                    except: pass
        except: pass
        return strings

    def _get_neighbors(self):
        neighbors = []
        try:
            folder = os.path.dirname(self.file_path)
            files = os.listdir(folder)
            for f in files[:5]:
                if f != self.file_name: neighbors.append(f)
            if len(files) > 5: neighbors.append("...")
        except: pass
        return neighbors
    
   # 기존 consult_ai 메서드를 이걸로 교체하세요!
    def consult_ai(self, api_key, model_name="gemini-1.5-flash"):
        """수집된 증거를 Gemini에게 보내 분석 요청 (모델 선택 가능)"""
        if not self.report:
            return "❌ 먼저 수사를 진행해야 합니다."

        try:
            import google.generativeai as genai
            import copy

            # 1. 설정
            genai.configure(api_key=api_key)
            
            # 2. 모델 선택 (사용자가 선택한 모델명 적용) 👈 여기가 핵심!
            model = genai.GenerativeModel(model_name)

            # 3. 데이터 다이어트 (429 에러 방지용)
            ai_data = copy.deepcopy(self.report)
            if 'internal_strings' in ai_data and ai_data['internal_strings']:
                if isinstance(ai_data['internal_strings'], list):
                    ai_data['internal_strings'] = [s[:200] for s in ai_data['internal_strings'][:20]]
                elif isinstance(ai_data['internal_strings'], str):
                    ai_data['internal_strings'] = ai_data['internal_strings'][:2000]

            # 4. 프롬프트
            prompt = f"""
            당신은 20년 경력의 '디지털 포렌식 전문가'입니다.
            현재 시각은 2025년 12월입니다.
            
            ## 분석 대상 데이터
            {json.dumps(ai_data, indent=2, ensure_ascii=False)}

            ## 작성 양식 (한국어)
            1. 🕵️‍♂️ **파일의 정체:** (확장자, 경로, 문자열 등을 종합하여 추리)
            2. 🧬 **출처 및 용도:** (어떤 프로그램/게임의 부속품인지)
            3. ⚠️ **삭제 안전성:** [안전 / 주의 / 위험] (이유 포함)
            4. 💡 **전문가 조언:** (한 줄 요약)
            """

            response = model.generate_content(prompt)
            return response.text

        except Exception as e:
            return f"❌ AI 오류 ({model_name}): {str(e)}"

# CLI 테스트용 코드
if __name__ == "__main__":
    raw = input("파일 경로 입력: ").replace('"', '').replace("'", "").replace("&", "").strip()
    if os.path.isdir(raw):
        print("📂 폴더입니다. (GUI 버전을 사용하세요)")
    else:
        d = FileDetective(raw)
        print(json.dumps(d.run_investigation(), indent=2, ensure_ascii=False))