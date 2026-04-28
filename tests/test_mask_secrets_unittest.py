import unittest


from app.zapret_manager.core.mask import mask_secrets_text, mask_secrets


class TestMaskSecrets(unittest.TestCase):
    def test_masks_uuid(self):
        s = "id=123e4567-e89b-12d3-a456-426614174000"
        out = mask_secrets_text(s)
        self.assertNotIn("e89b-12d3-a456-426614174000", out)
        self.assertIn("123e4567-****-****-****-4000", out)

    def test_masks_vless_link(self):
        s = "vless://123e4567-e89b-12d3-a456-426614174000@example.com:443?encryption=none"
        out = mask_secrets_text(s)
        self.assertNotIn("123e4567-e89b-12d3-a456-426614174000", out)
        self.assertIn("vless://***@", out)

    def test_masks_password_in_dict(self):
        data = {"password": "secret", "nested": {"uuid": "123e4567-e89b-12d3-a456-426614174000"}}
        out = mask_secrets(data)
        self.assertEqual(out["password"], "***")
        self.assertEqual(out["nested"]["uuid"], "***")


if __name__ == "__main__":
    unittest.main()
