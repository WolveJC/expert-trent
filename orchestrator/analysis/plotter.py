import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
from matplotlib.ticker import ScalarFormatter # Para manejar escalas pequeñas

class PerformancePlotter:
    def __init__(self, csv_path="results/metrics.csv"):
        self.csv_path = csv_path
        sns.set_theme(style="darkgrid", palette="magma") # Un tono más "Neon/Control Console"
        self.output_dir = os.path.dirname(self.csv_path)

    def load_data(self):
        if not os.path.exists(self.csv_path): return None
        try:
            return pd.read_csv(self.csv_path)
        except Exception as e:
            return None

    def plot_latency_comparison(self):
        df = self.load_data()
        if df is None or df.empty: return

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

        # 1. Boxplot con puntos individuales (para ver cada ejecución)
        sns.boxplot(x='algorithm', y='processing_time_ms', data=df, ax=ax1, width=0.5)
        sns.stripplot(x='algorithm', y='processing_time_ms', data=df, ax=ax1, color=".3", alpha=0.5)
        ax1.set_title('Dispersión de Latencia Real')
        ax1.set_ylabel('Tiempo (ms)')

        # 2. Barplot: Promedios
        sns.barplot(x='algorithm', y='processing_time_ms', data=df, ax=ax2, errorbar='sd', capsize=.1)
        ax2.set_title('Media de Ejecución C++')
        ax2.set_ylabel('Tiempo Promedio (ms)')

        # AJUSTE DE ESCALA: Si los tiempos son menores a 0.1ms, forzar formato decimal
        for ax in [ax1, ax2]:
            ax.yaxis.set_major_formatter(ScalarFormatter(useOffset=False))
            # Esto evita que Matplotlib oculte los decimales en el eje Y
            ax.ticklabel_format(style='plain', axis='y')

        plt.tight_layout()
        plot_path = os.path.join(self.output_dir, 'latency_comparison.png')
        plt.savefig(plot_path, dpi=100) # Buena resolución para la GUI
        plt.close()