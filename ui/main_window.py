import customtkinter as ctk
import threading
import time
import os
import pandas as pd
from PIL import Image

# Importaciones de tu lógica de orquestación
from orchestrator.supervisor import EngineSupervisor
from orchestrator.producer import ShmProducer
from orchestrator.collector import ShmCollector
from orchestrator.generators.scenarios import ScenarioGenerator
from orchestrator.analysis.plotter import PerformancePlotter

class DiskSimGUI(ctk.CTk):
    def __init__(self, engine_path=None):
        super().__init__()

        self.title("DISK SCHEDULER - NEON CONTROL CONSOLE")
        self.geometry("1200x800")
        
        # Backend Components
        self.supervisor = EngineSupervisor(engine_path=engine_path)
        self.generator = ScenarioGenerator(max_cylinders=500)
        self.results_path = "results/metrics.csv"
        self.plot_path = "results/latency_comparison.png"

        self._setup_layout()
        self._setup_canvas()

    def _setup_layout(self):
        self.grid_columnconfigure(1, weight=3)
        self.grid_rowconfigure(0, weight=1)

        # --- PANEL LATERAL ---
        self.sidebar = ctk.CTkFrame(self, width=250, corner_radius=0, fg_color="#1A1A1A")
        self.sidebar.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
        
        ctk.CTkLabel(self.sidebar, text="SYSTEM\nORACLE", font=("Orbitron", 24, "bold"), text_color="#00F0FF").pack(pady=30)

        self.algo_menu = ctk.CTkOptionMenu(self.sidebar, values=["SCAN", "C-SCAN"], fg_color="#333", button_color="#005FB8")
        self.algo_menu.pack(pady=10, padx=20)

        self.scenario_menu = ctk.CTkOptionMenu(self.sidebar, values=["Random", "Locality", "Killer"], fg_color="#333")
        self.scenario_menu.pack(pady=10, padx=20)

        self.requests_slider = ctk.CTkSlider(self.sidebar, from_=20, to=500, number_of_steps=48)
        self.requests_slider.pack(pady=(20, 0), padx=20)
        self.slider_label = ctk.CTkLabel(self.sidebar, text="Carga: 150 Req")
        self.slider_label.pack(pady=5)
        self.requests_slider.configure(command=lambda v: self.slider_label.configure(text=f"Carga: {int(v)} Req"))

        self.run_button = ctk.CTkButton(self.sidebar, text="EJECUTAR SECUENCIA", font=("Roboto", 14, "bold"),
                                       fg_color="#005FB8", hover_color="#007FFF", height=45,
                                       command=self.start_simulation_thread)
        self.run_button.pack(pady=40, padx=20)

        # --- ÁREA CENTRAL ---
        self.main_view = ctk.CTkFrame(self, fg_color="#0A0A0A")
        self.main_view.grid(row=0, column=1, sticky="nsew", padx=15, pady=15)
        
        self.tabview = ctk.CTkTabview(self.main_view, segmented_button_selected_color="#00F0FF")
        self.tabview.pack(expand=True, fill="both", padx=10, pady=5)
        self.tabview.add("Trace Map")
        self.tabview.add("Analytics")

        # --- CONSOLA ---
        self.console_box = ctk.CTkTextbox(self.main_view, height=140, font=("JetBrains Mono", 12), 
                                         fg_color="#050505", text_color="#00FF41", border_color="#333", border_width=1)
        self.console_box.pack(fill="x", padx=10, pady=10)
        self.log("NUCLEO LISTO. Inserte parámetros de simulación.")

    def _setup_canvas(self):
        self.canvas = ctk.CTkCanvas(self.tabview.tab("Trace Map"), bg="#050505", highlightthickness=0)
        self.canvas.pack(expand=True, fill="both")
        self.canvas.create_line(50, 550, 750, 550, fill="#333", width=2)
        for i in range(0, 501, 100):
            x = 50 + (i * (700/500))
            self.canvas.create_text(x, 570, text=str(i), fill="#666", font=("Arial", 10))

    def log(self, msg):
        self.console_box.insert("end", f"[{time.strftime('%H:%M:%S')}] {msg}\n")
        self.console_box.see("end")

    def animate_trace(self, sequence):
        self.canvas.delete("trace")
        if not sequence: return
        width, margin_x = 700, 50
        step_y = 480 / len(sequence)
        
        def draw_step(i, px, py):
            if i >= len(sequence):
                self.log("Visualización de rastro completada.")
                self.update_analytics() # Actualiza analytics al terminar
                self.after(800, lambda: self.tabview.set("Analytics"))
                return
            nx = margin_x + (sequence[i] * (width / 500))
            ny = py + step_y
            self.canvas.create_line(px, py, nx, ny, fill="#00F0FF", width=2, tags="trace")
            self.canvas.create_oval(nx-3, ny-3, nx+3, ny+3, fill="#FFF", outline="#00F0FF", tags="trace")
            self.after(15, lambda: draw_step(i + 1, nx, ny))

        start_x = margin_x + (sequence[0] * (width / 500))
        draw_step(1, start_x, 40)

    def update_analytics(self):
        """Genera datos, limpia la pestaña y construye la vista de reporte + imagen"""
        for widget in self.tabview.tab("Analytics").winfo_children():
            widget.destroy()

        # Contenedor con Scroll para albergar reporte e imagen
        scroll_frame = ctk.CTkScrollableFrame(self.tabview.tab("Analytics"), fg_color="transparent")
        scroll_frame.pack(expand=True, fill="both", padx=5, pady=5)

        # 1. Generar la gráfica físicamente
        try:
            plotter = PerformancePlotter(self.results_path)
            plotter.plot_latency_comparison()
        except Exception as e:
            self.log(f"Error al generar gráfico: {e}")

        # 2. SECCIÓN: TABLA COMPARATIVA
        report_text = self._get_comparison_data()
        comparison_box = ctk.CTkTextbox(scroll_frame, height=120, font=("JetBrains Mono", 13),
                                        fg_color="#121212", border_color="#00F0FF", border_width=1)
        comparison_box.pack(fill="x", padx=10, pady=10)
        comparison_box.insert("0.0", report_text)
        comparison_box.configure(state="disabled")

        # 3. SECCIÓN: VISUALIZACIÓN DE IMAGEN (Matplotlib)
        if os.path.exists(self.plot_path):
            try:
                raw_img = Image.open(self.plot_path)
                # Ajustar imagen a un tamaño visible en el frame
                ctk_img = ctk.CTkImage(light_image=raw_img, dark_image=raw_img, size=(700, 450))
                img_label = ctk.CTkLabel(scroll_frame, image=ctk_img, text="")
                img_label.pack(pady=10)
            except Exception as e:
                self.log(f"Error al cargar PNG: {e}")
                self._show_error_label(scroll_frame, "Error al procesar archivo de imagen.")
        else:
            self._show_error_label(scroll_frame, "Archivo de analítica no encontrado.")

    def _get_comparison_data(self):
        """Extrae métricas del CSV para el reporte de texto"""
        try:
            df = pd.read_csv(self.results_path)
            if len(df) < 2: return "Esperando más datos para comparativa..."
            stats = df.groupby('algorithm')['processing_time_ms'].mean()
            
            res = ">>> REPORTE DE EFICIENCIA DEL SISTEMA <<<\n"
            if "scan" in stats and "c-scan" in stats:
                s, cs = stats['scan'], stats['c-scan']
                diff = abs(s - cs)
                best = "C-SCAN" if cs < s else "SCAN"
                perc = (diff / max(s, cs)) * 100
                res += f"- SCAN promedio: {s:.3f} ms\n- C-SCAN promedio: {cs:.3f} ms\n"
                res += f"- CONCLUSIÓN: {best} es {perc:.1f}% más rápido en este escenario."
            else:
                res += f"Algoritmo actual: {df['algorithm'].iloc[-1].upper()}\n"
                res += f"Tiempo promedio: {stats.iloc[0]:.3f} ms\n"
                res += "Consejo: Ejecute el otro algoritmo para obtener comparativa."
            return res
        except:
            return "Error al leer métricas. Asegúrese de que results/metrics.csv existe."

    def _show_error_label(self, parent, text):
        ctk.CTkLabel(parent, text=f"⚠ {text}", font=("Orbitron", 14), text_color="#FF4B4B").pack(pady=50)

    def start_simulation_thread(self):
        self.run_button.configure(state="disabled", text="PROCESANDO...")
        self.tabview.set("Trace Map")
        threading.Thread(target=self.run_simulation, daemon=True).start()

    def run_simulation(self):
        mode = self.algo_menu.get().lower()
        scenario_name = self.scenario_menu.get().lower()
        count = int(self.requests_slider.get())

        try:
            self.log(f"Iniciando Motor C++: Modo {mode.upper()}")
            self.supervisor.cleanup_shm()
            self.supervisor.start_engine(algorithm=mode)
            time.sleep(0.5) 

            producer = ShmProducer()
            collector = ShmCollector(log_file=self.results_path)
            scenarios = {"random": self.generator.random_requests, 
                         "locality": self.generator.locality_burst, 
                         "killer": self.generator.scan_killer}
            
            requests = scenarios[scenario_name](count=count)
            cyl_list = [r['cylinder'] for r in requests]
            target_idx = producer.write_batch(requests)

            if collector.wait_for_completion(target_idx):
                collector.collect_metrics(requests[0]['batch_id'], mode, 0) # El motor C++ ya mide su tiempo
                collector.save_to_csv()
                self.after(0, lambda: self.animate_trace(cyl_list))
            else:
                self.log("ERROR: Timeout del Motor C++.")
        except Exception as e:
            self.log(f"CRITICAL ERROR: {str(e)}")
        finally:
            self.supervisor.stop_engine()
            self.after(0, lambda: self.run_button.configure(state="normal", text="EJECUTAR SECUENCIA"))

if __name__ == "__main__":
    app = DiskSimGUI()
    app.mainloop()