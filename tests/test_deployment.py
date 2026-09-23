from pathlib import Path


def test_docker_compose_file_is_present() -> None:
    compose_file = Path('infra/docker-compose.yml')
    assert compose_file.exists()
