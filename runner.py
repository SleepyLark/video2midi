import logging
from controller import AppController

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

logger.info("Starting app")

def main():
    app = AppController()
    app.start()

if __name__ == "__main__":
    main()