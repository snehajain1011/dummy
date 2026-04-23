# telemetry.py

import sys
import csv
import time
from loguru import logger

class Telemetry:
    def __init__(self, output_filename="performance_log.csv", level="INFO"):
        self.log_data = []
        self.output_filename = output_filename

        logger.remove()
        logger.add(sys.stderr, level=level)
        self.logger = logger
        self.logger.info("Telemetry initialized. Logs will be saved to CSV on exit.")

    async def _handle_metric_event(self, task, metrics):
        """
        Handles various Pipecat metric events and normalizes them into CSV-friendly format.
        """
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        service_name = getattr(metrics, "name", "unknown")
        data = getattr(metrics, "data", {})

        ttft = data.get("ttft") or data.get("ttfb") or 0.0
        processing_time = data.get("processing_time") or 0.0

        log_entry = {
            "timestamp": timestamp,
            "service": service_name,
            "ttft_seconds": round(ttft, 4) if ttft else None,
            "processing_time_seconds": round(processing_time, 4) if processing_time else None
        }
        self.log_data.append(log_entry)
        self.logger.info(f"PERF: {service_name} | TTFT: {ttft:.4f}s | Processing: {processing_time:.4f}s")

    def save_to_csv(self):
        """
        Saves collected telemetry data to CSV file.
        """
        if not self.log_data:
            self.logger.warning("No telemetry data collected, skipping CSV export.")
            return

        keys = self.log_data[0].keys()
        try:
            with open(self.output_filename, 'w', newline='') as output_file:
                dict_writer = csv.DictWriter(output_file, fieldnames=keys)
                dict_writer.writeheader()
                dict_writer.writerows(self.log_data)
            self.logger.info(f"✅ Performance logs successfully saved to {self.output_filename}")
        except Exception as e:
            self.logger.error(f"❌ Failed to save performance logs to CSV: {e}")

    def attach_to(self, task, pipeline):
        """
        Attaches telemetry to real Pipecat metric events with minimal changes to main file.
        """
        self.logger.info("Registering telemetry event handlers for Pipecat metrics...")

        metric_events = [
            "stop_ttfb_metrics",          # Time to first byte metrics
            "stop_processing_metrics",    # Processing duration metrics
            "start_tts_usage_metrics",    # TTS usage stats
            "start_llm_usage_metrics",    # LLM usage stats
        ]

        for event_name in metric_events:
            try:
                task.add_event_handler(event_name, self._handle_metric_event)
                self.logger.debug(f"Attached telemetry to event: {event_name}")
            except Exception as e:
                self.logger.warning(f"Could not attach to event {event_name}: {e}")

        # Ensure CSV is saved at program exit
        import atexit
        atexit.register(self.save_to_csv)
