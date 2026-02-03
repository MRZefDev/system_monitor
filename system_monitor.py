import logging
import platform
import time
import sys
from logging.handlers import RotatingFileHandler
from typing import Dict, Any
import psutil
import GPUtil

LOG_FILENAME = "system_monitor.log"
LOG_FORMAT = "%(asctime)s | %(levelname)s | %(message)s"

class SystemMonitor:
    """
    - A class to monitor and log system resources (CPU, RAM, GPU).
    Designed for continuous background operation.
    - Sistem kaynaklarini (CPU, RAM, GPU) izlemek ve kaydetmek icin kullanilan bir sinif.
    Sürekli arka plan calismasi icin tasarlanmistir.
    """
        
    def __init__(self, interval: int = 5, log_file: str = LOG_FILENAME):
        self.interval = interval
        self.log_file = log_file
        self.logger = self._setup_logger()
        self.os_info = self._get_os_info()
    def _setup_logger(self) -> logging.Logger:
        """
        - Sets up the logger configuration. 
        Uses RotatingFileHandler to manage file size (max 5MB, keeps 3 backups).
        - Gunluk kaydedici yapilandirmasini ayarlar.
        Dosya boyutunu yonetmek icin RotatingFileHandler kullanir (maksimum 5 MB, 3 yedekleme tutar).
        """
        logger = logging.getLogger("SystemMonitor")
        logger.setLevel(logging.INFO)        
        handler = RotatingFileHandler(self.log_file, maxBytes=5*1024*1024, backupCount=3, encoding="utf-8")
        formatter = logging.Formatter(LOG_FORMAT, datefmt="%Y-%m-%d %H:%M:%S")
        handler.setFormatter(formatter)        
        logger.addHandler(handler)
        return logger

    def _get_os_info(self) -> Dict[str, Any]:
        """
        - Retrieves static operating system information once during initialization.
        - Baslatma sirasinda kez statik isletim sistemi bilgilerini alir.
        """
        return {
            "OS": platform.system(),
            "Version": platform.version(),
            "Arch": platform.machine(),
            "Cores": psutil.cpu_count(logical=True),
            "Total_RAM": f"{round(psutil.virtual_memory().total / (1024**3), 2)} GB"
        }

    def _get_gpu_info(self) -> Dict[str, Any]:
        """
        - Safely retrieves GPU information using GPUtil.
        - GPUtil kullanarak GPU bilgilerini güvenli bir şekilde alir.
        """
        gpu_data = {"usage": 0.0, "name": "N/A"}
        try:
            gpus = GPUtil.getGPUs()
            if gpus:
                gpu = gpus[0]
                gpu_data["usage"] = round(gpu.load * 100, 2)
                gpu_data["name"] = gpu.name
        except Exception as e:
            self.logger.debug(f"Could not retrieve GPU info: {e}")
        return gpu_data

    def fetch_metrics(self) -> Dict[str, Any]:
        """
        - Collects real-time system metrics.
        - Gerçek zamanli sistem ölçümlerini toplar.
        """
        cpu_usage = psutil.cpu_percent(interval=None) 
        ram = psutil.virtual_memory()
        gpu_info = self._get_gpu_info()
        return {
            "cpu_usage": cpu_usage,
            "ram_usage": ram.percent,
            "ram_used": round(ram.used / (1024**2), 2),
            "ram_free": round(ram.available / (1024**2), 2),
            "gpu_usage": gpu_info["usage"],
            "gpu_name": gpu_info["name"]
        }

    def log_system_info(self):
        """
        - Logs the static system information at startup.
        - Başlangicta statik sistem bilgilerini kaydeder."""
        header = f"--- MONITOR STARTED ---\nSystem Info: {self.os_info}"
        self.logger.info(header)
    def run(self):
        """
        - Starts the main monitoring loop.
        - Ana izleme döngüsünü baslatir.
        """
        print(f"System monitoring service started. (Log file: {self.log_file})")
        print("Press CTRL+C to exit.\n")        
        self.log_system_info()

        try:
            while True:
                metrics = self.fetch_metrics()
                
                log_msg = (
                    f"CPU: {metrics['cpu_usage']}% | "
                    f"RAM: {metrics['ram_usage']}% ({metrics['ram_used']}MB Used) | "
                    f"GPU: {metrics['gpu_usage']}% ({metrics['gpu_name']})"
                )
                self.logger.info(log_msg)

                sys.stdout.write(f"\r[LIVE] CPU: {metrics['cpu_usage']}% | RAM: {metrics['ram_usage']}% | GPU: {metrics['gpu_usage']}%   ")
                sys.stdout.flush()

                time.sleep(self.interval)

        except KeyboardInterrupt:
            print("\n\nStopping service...")
            self.logger.info("--- MONITOR STOPPED ---")
        except Exception as e:
            self.logger.critical(f"Unexpected error: {e}")
            print(f"\nAn error occurred: {e}")

if __name__ == "__main__":
    monitor = SystemMonitor(interval=5)
    monitor.run()