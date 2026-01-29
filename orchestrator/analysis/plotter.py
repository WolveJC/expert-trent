import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

class PerformancePlotter:
    def __init__(self, csv_path="results/metrics.csv"):
        self.csv_path = csv_path
        # Estética moderna para los gráficos
        sns.set_theme(style="darkgrid", palette="viridis")
        self.output_dir = os.path.dirname(self.csv_path)

    def load_data(self):
        if not os.path.exists(self.csv_path):
            print(f"[Plotter] Error: No se encontró {self.csv_path}")
            return None
        try:
            return pd.read_csv(self.csv_path)
        except Exception as e:
            print(f"[Plotter] Error al leer CSV: {e}")
            return None

    def plot_latency_comparison(self):
        """Genera un Boxplot y un Barplot de los tiempos de respuesta."""
        df = self.load_data()
        if df is None or df.empty:
            return

        # Creamos una figura con dos subgráficos
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

        # 1. Boxplot: Distribución y Outliers
        sns.boxplot(x='algorithm', y='processing_time_ms', data=df, ax=ax1)
        ax1.set_title('Distribución de Latencia (Variabilidad)')
        ax1.set_ylabel('Tiempo (ms)')

        # 2. Barplot: Promedios con barras de error
        sns.barplot(x='algorithm', y='processing_time_ms', data=df, ax=ax2, capsize=.1)
        ax2.set_title('Promedio de Tiempo por Algoritmo')
        ax2.set_ylabel('Media de Tiempo (ms)')

        plt.tight_layout()
        
        # Guardar resultado
        plot_path = os.path.join(self.output_dir, 'latency_comparison.png')
        plt.savefig(plot_path)
        plt.close() # Importante para liberar memoria en la GUI
        print(f"[Plotter] Gráficas de rendimiento actualizadas en {plot_path}")

    def plot_throughput_trend(self):
        """Dibuja la tendencia de rendimiento a lo largo del tiempo."""
        df = self.load_data()
        if df is None or len(df) < 2: return

        plt.figure(figsize=(10, 5))
        df['idx'] = range(len(df))
        sns.lineplot(x='idx', y='processing_time_ms', hue='algorithm', data=df, marker='o')
        
        plt.title('Evolución del Tiempo de Procesamiento por Test')
        plt.xlabel('Número de Experimento')
        plt.ylabel('Tiempo (ms)')
        
        plot_path = os.path.join(self.output_dir, 'performance_trend.png')
        plt.savefig(plot_path)
        plt.close()