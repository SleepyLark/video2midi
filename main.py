import logging
from src.controller import AppController

# change level to logging.INFO for deployment
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

logger.info("Starting app")

def main():
    app = AppController()
    app.start()

if __name__ == "__main__":
    main()