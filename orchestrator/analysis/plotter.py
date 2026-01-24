import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

class PerformancePlotter:
    def __init__(self, csv_path="results/metrics.csv"):
        self.csv_path = csv_path
        sns.set_theme(style="whitegrid")

    def load_data(self):
        if not os.path.exists(self.csv_path):
            print(f"[Plotter] Error: No se encontró {self.csv_path}")
            return None
        return pd.read_csv(self.csv_path)

    def plot_latency_comparison(self):
        """Compara la latencia entre algoritmos."""
        df = self.load_data()
        if df is None or len(df) < 2: 
            print("[Plotter] Datos insuficientes para generar comparativa (se necesitan al menos 2 registros).")
            return

        plt.figure(figsize=(10, 6))
        sns.boxplot(x='algorithm', y='processing_time_ms', data=df)
        plt.title('Comparativa de Latencia de Procesamiento: SCAN vs C-SCAN')
        plt.ylabel('Tiempo (ms)')
        plt.savefig('results/latency_comparison.png')
        print("[Plotter] Gráfica de latencia generada.")

    def plot_head_trace(self, batch_id):
        """Dibuja el rastro del cabezal para un experimento específico."""
        # Esta gráfica requiere datos detallados de la secuencia de cilindros
        # que el motor procesó (se puede extraer del log de validación)
        pass