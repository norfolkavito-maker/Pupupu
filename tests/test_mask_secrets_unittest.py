import unittest

from app.zapret_manager.core.mask import (
    mask_secrets,
    mask_secrets_text,
    mask_mapping,
)


class TestMaskSecrets(unittest.TestCase):
    def test_shareable_masks_uuid(self):
        text = "id=123e4567-e89b-12d3-a456-426614174000"
        out = mask_secrets_text(text, mode="shareable_report")
        self.assertNotIn("123e4567-e89b-12d3-a456-426614174000", out)
        self.assertIn("***", out)

    def test_local_debug_preserves_uuid(self):
        text = "id=123e4567-e89b-12d3-a456-426614174000"
        out = mask_secrets_text(text, mode="local_debug")
        self.assertIn("123e4567-e89b-12d3-a456-426614174000", out)

    def test_shareable_masks_vless_link(self):
        text = "vless://123e4567-e89b-12d3-a456-426614174000@host.example:443?security=none#my"
        out = mask_secrets_text(text, mode="shareable_report")
        self.assertNotIn("123e4567-e89b-12d3-a456-426614174000", out)
        self.assertNotIn("@host.example:443", out)
        self.assertIn("vless://", out)
        self.assertIn("***", out)

    def test_local_debug_preserves_vless_link(self):
        text = "vless://123e4567-e89b-12d3-a456-426614174000@host.example:443?security=none#my"
        out = mask_secrets_text(text, mode="local_debug")
        self.assertIn("123e4567-e89b-12d3-a456-426614174000", out)
        self.assertIn("host.example", out)

    def test_shareable_masks_password_in_mapping(self):
        data = {"username": "user", "password": "secret"}
        out = mask_mapping(data, mode="shareable_report")
        self.assertEqual(out["username"], "user")
        self.assertEqual(out["password"], "***")

    def test_local_debug_preserves_password_in_mapping(self):
        data = {"username": "user", "password": "secret"}
        out = mask_mapping(data, mode="local_debug")
        self.assertEqual(out["username"], "user")
        self.assertEqual(out["password"], "secret")


if __name__ == "__main__":
    unittest.main()
