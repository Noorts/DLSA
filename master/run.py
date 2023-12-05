from logging.config import dictConfig

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "master.main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_config=dictConfig(
            {
                "version": 1,
                "disable_existing_loggers": False,
                "formatters": {
                    "default": {
                        "format": "[%(levelname)s] [%(asctime)s] [%(name)s] %(message)s",
                        "datefmt": "%y-%m-%d %H:%M:%S",
                    }
                },
                "handlers": {
                    "console": {
                        "class": "logging.StreamHandler",
                        "formatter": "default",
                    },
                },
                "root": {
                    "level": "INFO",
                    "handlers": ["console"],
                },
            }
        ),
    )
