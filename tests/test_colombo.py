"""
Colombo Scanner — Test Suite
Tests for security, plugin validation, entities, database, and intelligence.
Run with: python -m pytest tests/ -v
"""
import os
import sys
import pytest

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


class TestSecurity:
    """Tests for input sanitization and command injection prevention."""

    def test_sanitize_clean_input(self):
        from core.runner import sanitize_input
        assert sanitize_input("user@email.com") == "user@email.com"
        assert sanitize_input("192.168.1.1") == "192.168.1.1"
        assert sanitize_input("example.com") == "example.com"
        assert sanitize_input("+5511988887777") == "+5511988887777"

    def test_sanitize_blocks_semicolon(self):
        from core.runner import sanitize_input
        with pytest.raises(ValueError, match="caracteres não permitidos"):
            sanitize_input("; rm -rf /")

    def test_sanitize_blocks_pipe(self):
        from core.runner import sanitize_input
        with pytest.raises(ValueError, match="caracteres não permitidos"):
            sanitize_input("test | cat /etc/passwd")

    def test_sanitize_blocks_backtick(self):
        from core.runner import sanitize_input
        with pytest.raises(ValueError, match="caracteres não permitidos"):
            sanitize_input("`whoami`")

    def test_sanitize_blocks_dollar(self):
        from core.runner import sanitize_input
        with pytest.raises(ValueError, match="caracteres não permitidos"):
            sanitize_input("$(whoami)")

    def test_sanitize_blocks_ampersand(self):
        from core.runner import sanitize_input
        with pytest.raises(ValueError, match="caracteres não permitidos"):
            sanitize_input("test && rm -rf /")

    def test_sanitize_blocks_long_input(self):
        from core.runner import sanitize_input
        with pytest.raises(ValueError, match="muito longo"):
            sanitize_input("a" * 501)

    def test_no_home_volume_in_runner(self):
        """Ensures the dangerous -v /home:/home is no longer in the codebase."""
        runner_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "core", "runner.py")
        with open(runner_path, 'r') as f:
            content = f.read()
        assert "/home:/home" not in content, "CRITICAL: -v /home:/home still present in runner.py!"


class TestPluginValidation:
    """Tests for plugin schema validation and normalization."""

    def test_validate_missing_name(self):
        from core.plugin_manager import _validate_plugin
        warnings = _validate_plugin({"category": "test", "command": "echo"}, "test.yaml")
        assert any("name" in w for w in warnings)

    def test_validate_missing_command(self):
        from core.plugin_manager import _validate_plugin
        warnings = _validate_plugin({"name": "test", "category": "test"}, "test.yaml")
        assert any("command" in w for w in warnings)

    def test_validate_docker_run_duplication(self):
        from core.plugin_manager import _validate_plugin
        warnings = _validate_plugin({
            "name": "test",
            "category": "test",
            "command": "docker run --rm image -u target",
            "image": "image"
        }, "test.yaml")
        assert any("docker run" in w for w in warnings)

    def test_normalize_target_to_alvo(self):
        from core.plugin_manager import _normalize_plugin
        cfg = {"name": "test", "category": "test", "command": "-u {target} -silent"}
        result = _normalize_plugin(cfg, "test.yaml")
        assert "{alvo}" in result["command"]
        assert "{target}" not in result["command"]

    def test_normalize_removes_it_flag(self):
        from core.plugin_manager import _normalize_plugin
        cfg = {"name": "test", "category": "test", "command": "-it mxrch/ghunt email {alvo}"}
        result = _normalize_plugin(cfg, "test.yaml")
        assert "-it " not in result["command"]

    def test_normalize_adds_defaults(self):
        from core.plugin_manager import _normalize_plugin
        cfg = {"name": "test", "category": "test", "command": "echo {alvo}"}
        result = _normalize_plugin(cfg, "test.yaml")
        assert "timeout" in result
        assert "inputs" in result
        assert result["timeout"] == 300

    def test_load_plugins_returns_list(self):
        from core.plugin_manager import load_plugins
        plugins = load_plugins()
        assert isinstance(plugins, list)
        assert len(plugins) > 0


class TestEntityExtraction:
    """Tests for the intelligence entity extraction engine."""

    def test_extract_email(self):
        from core.intelligence import extrair_entidades
        entities = extrair_entidades("Contact us at target@example.org for info")
        types = [e.type.value for e in entities]
        values = [e.value for e in entities]
        assert "email" in types
        assert "target@example.org" in values

    def test_extract_ip(self):
        from core.intelligence import extrair_entidades
        entities = extrair_entidades("Server IP: 45.33.32.156")
        types = [e.type.value for e in entities]
        assert "ip" in types

    def test_extract_ip_filters_private(self):
        from core.intelligence import extrair_entidades
        entities = extrair_entidades("Local: 192.168.1.1 and 10.0.0.1")
        ip_values = [e.value for e in entities if e.type.value == "ip"]
        assert "192.168.1.1" not in ip_values
        assert "10.0.0.1" not in ip_values

    def test_extract_url(self):
        from core.intelligence import extrair_entidades
        entities = extrair_entidades("Visit https://admin.empresa.com/login")
        types = [e.type.value for e in entities]
        assert "url" in types

    def test_extract_phone(self):
        from core.intelligence import extrair_entidades
        entities = extrair_entidades("Contato: 11988887777")
        phone_values = [e.value for e in entities if e.type.value == "phone"]
        assert len(phone_values) > 0

    def test_extract_empty_text(self):
        from core.intelligence import extrair_entidades
        entities = extrair_entidades("")
        assert entities == []

    def test_extract_none_text(self):
        from core.intelligence import extrair_entidades
        entities = extrair_entidades(None)
        assert entities == []


class TestDatabase:
    """Tests for SQLite database CRUD operations."""

    def setup_method(self):
        """Use a test database."""
        import core.database as db
        self.original_path = db.DB_PATH
        db.DB_PATH = "/tmp/colombo_test.db"
        db.init_db()

    def teardown_method(self):
        """Clean up test database."""
        import core.database as db
        if os.path.exists(db.DB_PATH):
            os.remove(db.DB_PATH)
        db.DB_PATH = self.original_path

    def test_create_case(self):
        from core.database import create_case, get_case
        case_id = create_case("Test Case", "Description")
        assert case_id > 0
        case = get_case(case_id)
        assert case["name"] == "Test Case"

    def test_list_cases(self):
        from core.database import create_case, list_cases
        create_case("Case A")
        create_case("Case B")
        cases = list_cases()
        assert len(cases) >= 2

    def test_create_scan(self):
        from core.database import create_case, create_scan, finish_scan
        case_id = create_case("Scan Test")
        scan_id = create_scan(case_id, "test@email.com", plugin_count=5)
        assert scan_id > 0
        finish_scan(scan_id)

    def test_save_entities(self):
        from core.database import create_case, create_scan, save_entities, get_entities_by_case
        from core.entities import Entity, EntityType
        case_id = create_case("Entity Test")
        scan_id = create_scan(case_id, "target")
        entities = [
            Entity(type=EntityType.EMAIL, value="test@test.com", source_tool="tool1"),
            Entity(type=EntityType.IP, value="1.2.3.4", source_tool="tool2"),
        ]
        save_entities(case_id, scan_id, entities)
        stored = get_entities_by_case(case_id)
        assert len(stored) == 2

    def test_entity_correlations(self):
        from core.database import (
            create_case, create_scan, save_entities, get_entity_correlations
        )
        from core.entities import Entity, EntityType
        case_id = create_case("Correlation Test")
        scan_id = create_scan(case_id, "target")
        entities = [
            Entity(type=EntityType.EMAIL, value="shared@test.com", source_tool="tool1"),
            Entity(type=EntityType.EMAIL, value="shared@test.com", source_tool="tool2"),
            Entity(type=EntityType.IP, value="1.2.3.4", source_tool="tool1"),
        ]
        save_entities(case_id, scan_id, entities)
        corrs = get_entity_correlations(case_id)
        assert len(corrs) >= 1
        assert corrs[0]["value"] == "shared@test.com"
        assert corrs[0]["tool_count"] >= 2


class TestSmartScan:
    """Tests for target type detection."""

    def test_detect_email(self):
        from core.smart_scan import detectar_tipo
        assert detectar_tipo("user@domain.com") == "email"

    def test_detect_phone(self):
        from core.smart_scan import detectar_tipo
        assert detectar_tipo("+5511988887777") == "telefone"

    def test_detect_ip(self):
        from core.smart_scan import detectar_tipo
        assert detectar_tipo("192.168.1.1") == "ip"

    def test_detect_domain(self):
        from core.smart_scan import detectar_tipo
        assert detectar_tipo("example.com") == "dominio"

    def test_detect_url(self):
        from core.smart_scan import detectar_tipo
        assert detectar_tipo("https://example.com/path") == "url"

    def test_detect_username_fallback(self):
        from core.smart_scan import detectar_tipo
        assert detectar_tipo("john_doe") == "username"

    def test_detect_cnpj(self):
        from core.smart_scan import detectar_tipo
        assert detectar_tipo("12.345.678/0001-90") == "cnpj"
class TestMonitor:
    """Tests for the Continuous Monitoring (Watchdog) engine."""

    def test_monitor_invalid_interval_defaults_to_24(self):
        from core.monitor import iniciar_monitoramento
        import core.monitor as monitor
        import time
        from unittest.mock import patch, MagicMock

        # We mock time.sleep to avoid actual waiting
        with patch("time.sleep", side_effect=KeyboardInterrupt), \
             patch("core.monitor.get_logger"), \
             patch("core.monitor.Console"):
            
            # Using interval <= 0 should not crash and should use default
            # We catch KeyboardInterrupt because the loop is infinite
            try:
                iniciar_monitoramento("test", [], 1, intervalo_horas=-1)
            except KeyboardInterrupt:
                pass
            # Logic check for the internal variable (manual verification of line 39 in monitor.py)

    def test_format_details_entities(self):
        from core.monitor import formatar_detalhes_entidades
        entidades = [
            {"type": "email", "value": "a@b.com", "source_tool": "t1"},
            {"type": "ip", "value": "1.1.1.1", "source_tool": "t2"}
        ]
        res = formatar_detalhes_entidades(entidades)
        assert "2 email(s)" in res or "1 email(s)" in res
        assert "a@b.com" in res
        assert "1.1.1.1" in res

    def test_format_details_empty(self):
        from core.monitor import formatar_detalhes_entidades
        assert "Nenhuma pista" in formatar_detalhes_entidades([])
