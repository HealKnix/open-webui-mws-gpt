import uvicorn

from .config import get_settings


def main() -> None:
    settings = get_settings()
    uvicorn.run(
        "terminal_orchestrator.main:app",
        host=settings.listen_host,
        port=settings.listen_port,
        log_config=None,
        access_log=False,
    )


if __name__ == "__main__":
    main()
