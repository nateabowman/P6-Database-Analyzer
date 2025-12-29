"""Main entry point for P6 Database Analyzer."""

import sys
import os
from PySide6.QtWidgets import QApplication
from gui.main_window import MainWindow
from utils.logging_config import setup_logging
from utils.metrics import get_metrics

# Initialize logging
logger = setup_logging(
    log_level=os.getenv('LOG_LEVEL', 'INFO'),
    use_json=os.getenv('LOG_JSON', 'false').lower() == 'true'
)

def main():
    """Main application entry point."""
    logger.info("Starting P6 Database Analyzer")
    metrics = get_metrics()
    
    app = QApplication(sys.argv)
    app.setApplicationName("P6 Database Analyzer")
    
    try:
        window = MainWindow()
        window.show()
        logger.info("Application window displayed")
        
        exit_code = app.exec()
        logger.info(f"Application exiting with code {exit_code}")
        return exit_code
    except Exception as e:
        logger.critical(f"Fatal error in application: {str(e)}", exc_info=True)
        raise
    finally:
        # Log final metrics
        metrics_summary = metrics.get_metrics_summary()
        logger.info(f"Final metrics: {metrics_summary}")


if __name__ == "__main__":
    main()

