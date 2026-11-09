import unittest

from discordrpc.types import Application, AssetManager, User


class UserAvatarDecorationTests(unittest.TestCase):
    def test_avatar_decoration_present(self):
        user = User({
            "id": "1",
            "username": "test",
            "avatar_decoration_data": {"asset": "a_dummy123"},
        })
        self.assertEqual(
            user.avatar_decoration,
            "https://cdn.discordapp.com/avatar-decoration-presets/a_dummy123.png?size=1024",
        )

    def test_avatar_decoration_null(self):
        user = User({"id": "1", "username": "test", "avatar_decoration_data": None})
        self.assertEqual(user.avatar_decoration, "")

    def test_avatar_decoration_missing_asset(self):
        user = User({"id": "1", "username": "test", "avatar_decoration_data": {}})
        self.assertEqual(user.avatar_decoration, "")

    def test_avatar_decoration_empty_user(self):
        self.assertEqual(User({}).avatar_decoration, "")

    def test_animated_avatar_still_gif(self):
        user = User({"id": "1", "username": "test", "avatar": "a_abcdef123456"})
        self.assertEqual(
            user.avatar,
            "https://cdn.discordapp.com/avatars/1/a_abcdef123456.gif?size=1024",
        )


class ApplicationCoverTests(unittest.TestCase):
    def test_cover_present(self):
        app = Application({"id": "123456789", "name": "test", "cover_image": "deadbeef"})
        self.assertEqual(
            app.cover,
            "https://cdn.discordapp.com/app-icons/123456789/deadbeef.png?size=1024&keep_aspect_ratio=true",
        )

    def test_cover_missing(self):
        app = Application({"id": "123456789", "name": "test"})
        self.assertEqual(app.cover, "")

    def test_cover_null(self):
        app = Application({"id": "123456789", "name": "test", "cover_image": None})
        self.assertEqual(app.cover, "")

    def test_icon_default_size_1024(self):
        app = Application({"id": "123456789", "name": "test", "icon": "c0ffee"})
        self.assertEqual(
            app.icon,
            "https://cdn.discordapp.com/app-icons/123456789/c0ffee.png?size=1024",
        )


class AssetManagerTests(unittest.TestCase):
    def test_empty_assets_list(self):
        self.assertEqual(len(AssetManager(123456789, [])), 0)

    def test_no_assets_list_does_not_crash(self):
        self.assertEqual(len(AssetManager(123456789)), 0)

    def test_get_by_name(self):
        am = AssetManager(123456789, [
            {"id": 1, "name": "cat"},
            {"id": 2, "name": "dog"},
        ])
        self.assertEqual(am.get("cat").name, "cat")
        self.assertIsNone(am.get("nonexistent"))
        self.assertEqual(am.names, ["cat", "dog"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
