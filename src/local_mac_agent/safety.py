from __future__ import annotations


class SafetyGuard:
    SAFE = "safe"
    REQUIRES_CONFIRMATION_STATE = "requires_confirmation"
    BLOCKED = "blocked"

    SAFE_ACTIONS = frozenset(
        {
            "read",
            "open",
            "summarize",
            "search",
            "organize",
            "index",
            "draft",
            "create_log",
            "retrieve",
            "classify",
            "explain",
            "copy",
            "paste",
            "scroll",
        }
    )
    REQUIRES_CONFIRMATION = frozenset(
        {
            "delete",
            "send_email",
            "send_message",
            "purchase",
            "publish",
            "overwrite",
            "move_sensitive_file",
            "edit_system_settings",
            "share_file",
            "install_software",
            "run_script",
            "submit_form",
            "schedule_external_event",
            "modify_document",
        }
    )
    BLOCKED_BY_DEFAULT = frozenset(
        {
            "export_credentials",
            "exfiltrate_data",
            "disable_security",
            "wipe_directory",
            "run_untrusted_script",
            "modify_without_user_intent",
            "bypass_permissions",
            "hidden_persistence",
            "surveillance_without_indicator",
        }
    )

    def classify_action(self, action_name: str) -> str:
        normalized = action_name.strip().lower()
        if normalized in self.SAFE_ACTIONS:
            return self.SAFE
        if normalized in self.BLOCKED_BY_DEFAULT:
            return self.BLOCKED
        return self.REQUIRES_CONFIRMATION_STATE

    def requires_confirmation(self, action_name: str) -> bool:
        return self.classify_action(action_name) == self.REQUIRES_CONFIRMATION_STATE

    def is_blocked(self, action_name: str) -> bool:
        return self.classify_action(action_name) == self.BLOCKED

    def assert_allowed(self, action_name: str, confirmed: bool = False) -> bool:
        classification = self.classify_action(action_name)
        if classification == self.BLOCKED:
            raise PermissionError(f"Action is blocked by default: {action_name}")
        if classification == self.REQUIRES_CONFIRMATION_STATE and not confirmed:
            raise PermissionError(f"Action requires confirmation: {action_name}")
        return True
