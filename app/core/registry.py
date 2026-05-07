from __future__ import annotations

from app.core.i18n import t
from app.services.base import BaseService
from app.services.bbr import BBRService
from app.services.bootstrap import BootstrapService
from app.services.docker import DockerService
from app.services.fail2ban import Fail2BanService
from app.services.firewall import FirewallService
from app.services.ssh_hardening import SSHHardeningService
from app.services.traffic_guard import TrafficGuardService


def build_service_registry() -> dict[int, BaseService]:
    services: list[BaseService] = [
        FirewallService(),
        SSHHardeningService(),
        Fail2BanService(),
        DockerService(),
        BBRService(),
        BootstrapService(),
        TrafficGuardService(),
    ]
    return {service.code: service for service in services}


def build_service_catalog(lang: str) -> list[tuple[int, str, str]]:
    return [
        (service.code, service.name, t(lang, f"service.{service.code}.description"))
        for service in build_service_registry().values()
    ]
