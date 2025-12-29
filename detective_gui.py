import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox
import threading
import json
import os
import detective

class DetectiveApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🕵️‍♂️ AI File Detective (v1.2 - Model Selector)")
        self.root.geometry("800x900")
        
        self.config_file = "config.json"
        
        # 디자인 테마
        self.bg_color = "#2b2b2b"
        self.btn_color = "#404040"
        self.root.configure(bg=self.bg_color)

        # 1. 타이틀
        tk.Label(root, text="🕵️‍♂️ 파일 탐정 수사본부", 
                 font=("Malgun Gothic", 20, "bold"), 
                 bg=self.bg_color, fg="#00ff00").pack(pady=20)

        # 2. 설정 영역 (API 키 + 모델 선택)
        setting_frame = tk.Frame(root, bg=self.bg_color)
        setting_frame.pack(pady=5)
        
        # [API 키 입력]
        tk.Label(setting_frame, text="🔑 API Key:", font=("Malgun Gothic", 10, "bold"), 
                 bg=self.bg_color, fg="yellow").grid(row=0, column=0, padx=5, sticky="e")
        
        self.api_entry = tk.Entry(setting_frame, width=30, show="*")
        self.api_entry.grid(row=0, column=1, padx=5)

        # [모델 선택 콤보박스]
        tk.Label(setting_frame, text="🧠 Model:", font=("Malgun Gothic", 10, "bold"), 
                 bg=self.bg_color, fg="#00ffff").grid(row=0, column=2, padx=5, sticky="e")
        
        # 구글 공식 문서 기반 모델 리스트
        self.model_list = [

            "gemini-2.5-pro",
            "gemini-2.5-flash-lite",      
            "gemini-2.5-flash",        
            "gemini-3-flash-preview",   
            "gemini-3-pro-preview"        
        ]
        self.model_combo = ttk.Combobox(setting_frame, values=self.model_list, state="readonly", width=20)
        self.model_combo.current(0)
        self.model_combo.grid(row=0, column=3, padx=5)

        # [저장된 설정 불러오기]
        self.load_settings()

        # 3. 버튼 영역
        btn_frame = tk.Frame(root, bg=self.bg_color)
        btn_frame.pack(pady=15)

        tk.Button(btn_frame, text="📄 파일 선택", command=self.select_file,
                  font=("Malgun Gothic", 12), width=15, height=2,
                  bg=self.btn_color, fg="white", relief="flat").pack(side="left", padx=10)

        tk.Button(btn_frame, text="📂 폴더 선택", command=self.select_folder,
                  font=("Malgun Gothic", 12), width=15, height=2,
                  bg=self.btn_color, fg="white", relief="flat").pack(side="left", padx=10)

        # 4. 상태 메시지
        self.status_label = tk.Label(root, text="분석할 대상을 선택하세요.", 
                                     font=("Malgun Gothic", 10),
                                     bg=self.bg_color, fg="#aaaaaa")
        self.status_label.pack(pady=5)

        # 5. 결과 창
        self.result_area = scrolledtext.ScrolledText(root, width=95, height=40, 
                                                     font=("Consolas", 10), 
                                                     bg="#1e1e1e", fg="#dcdcdc")
        self.result_area.pack(pady=10, padx=20)
        self.result_area.insert(tk.END, ">>> AI Detective Ready.\n")

    def select_file(self):
        f = filedialog.askopenfilename(title="파일 선택")
        if f: self.run_analysis(f)

    def select_folder(self):
        f = filedialog.askdirectory(title="폴더 선택")
        if f: self.run_analysis(f)

    def run_analysis(self, target_path):
        self.result_area.delete(1.0, tk.END)
        self.status_label.config(text=f"🔍 분석 중... {os.path.basename(target_path)}")
        self.result_area.insert(tk.END, f"🚀 [수사 개시] {target_path}\n\n")
        
        threading.Thread(target=self._worker, args=(target_path,), daemon=True).start()

    def _worker(self, target_path):
        try:
            # 1. 파일/폴더 분석
            if os.path.isdir(target_path):
                largest_file = None
                max_size = 0
                count = 0
                for root, _, files in os.walk(target_path):
                    for f in files:
                        count += 1
                        fp = os.path.join(root, f)
                        try:
                            s = os.path.getsize(fp)
                            if s > max_size: max_size = s; largest_file = fp
                        except: pass
                
                if largest_file:
                    self.update_text(f"📂 [폴더] 총 {count}개 파일.\n🎯 [대표 분석] {os.path.basename(largest_file)}\n{'-'*60}\n")
                    dt = detective.FileDetective(largest_file)
                    res = dt.run_investigation()
                else:
                    self.update_text("❌ 빈 폴더입니다.\n"); return
            else:
                dt = detective.FileDetective(target_path)
                res = dt.run_investigation()

            # 기본 결과 출력
            self.update_text(json.dumps(res, indent=4, ensure_ascii=False) + "\n\n" + "="*60 + "\n")
            
            # 2. AI 호출 (모델명 사용)
            api_key = self.api_entry.get().strip()
            selected_model = self.model_combo.get()

            if api_key:
                # 설정 저장
                self.save_settings(api_key, selected_model)

                self.update_status(f"🤖 AI({selected_model}) 분석 중...")
                self.update_text(f"🤖 [AI 탐정] 모델: {selected_model}\n분석을 시작합니다...\n")
                
                # consult_ai에 모델명 전달
                ai_report = dt.consult_ai(api_key, model_name=selected_model)
                
                self.update_text("\n" + "="*20 + " 🧠 AI 리포트 " + "="*20 + "\n")
                self.update_text(ai_report)
                self.update_status("✅ 분석 완료!")
            else:
                self.update_text("\n💡 API 키를 입력하면 AI 분석이 가능합니다.")
                self.update_status("✅ 완료 (AI 미사용)")

        except Exception as e:
            self.update_text(f"\n❌ 오류: {str(e)}")
            self.update_status("오류 발생")

    # --- 설정 관리 ---
    def load_settings(self):
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    # 키 복원
                    if "api_key" in data: self.api_entry.insert(0, data["api_key"])
                    # 모델 복원
                    if "model" in data and data["model"] in self.model_list:
                        self.model_combo.set(data["model"])
        except: pass

    def save_settings(self, api_key, model):
        try:
            data = {"api_key": api_key, "model": model}
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
        except: pass

    def update_text(self, text):
        self.result_area.insert(tk.END, text)
        self.result_area.see(tk.END)

    def update_status(self, text):
        self.status_label.config(text=text)

if __name__ == "__main__":
    root = tk.Tk()
    app = DetectiveApp(root)
    root.mainloop()