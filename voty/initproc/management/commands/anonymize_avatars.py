import os
from shutil import rmtree
from avatar.models import Avatar, avatar_storage
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


# django-avatar has an option AVATAR_EXPOSE_USERNAMES, which is unfortunately set by default,
# resulting in usernames being used as directory names for avatar storage. When a user's username
# is changed, the original avatar images don't move and can still be located through the Avatar
# objects, which store their filenames, but the cached resized images are only read and written
# under the current username. The cached images under the previous username aren't deleted when
# the username changes and thus lie around orphaned in storage, causing a privacy issue since
# they can't be deleted when the user is anonymized. We're solving that problem by renaming the
# directories from current usernames to user ids, moving any original avatar images under old
# usernames into the new directories, deleting any directories with old usernames, and setting
# AVATAR_EXPOSE_USERNAMES to False. All avatars for a user (including any cached resized images
# generated later) will then be in the new user id directories, where they can be deleted along
# with the originals when a user is anonymized.

class Command(BaseCommand):
    help = "Anonymize avatar filenames"

    def handle(self, *args, **options):
        base_dir = "avatars"
        for user in get_user_model().objects.all():
            old_absolute_path = avatar_storage.path(os.path.join(base_dir, str(user.username)))
            new_absolute_path = avatar_storage.path(os.path.join(base_dir, str(user.pk)))
            if os.path.exists(old_absolute_path):
                os.rename(old_absolute_path, new_absolute_path)

        for avatar in Avatar.objects.all():
            old_relative_path = avatar.avatar.name
            new_relative_path = os.path.join(base_dir, str(avatar.user.pk), os.path.basename(old_relative_path))

            new_absolute_path = avatar_storage.path(new_relative_path)
            old_absolute_path = avatar_storage.path(old_relative_path)

            if not os.path.exists(new_absolute_path):
                os.rename(old_absolute_path, new_absolute_path)

            avatar.avatar = new_relative_path
            avatar.save()

        for filename in os.listdir(avatar_storage.path(base_dir)):
            if not filename.isnumeric():
                old_username_dir = avatar_storage.path(os.path.join(base_dir, filename))
                print("deleting old username directory" + old_username_dir)
                rmtree(old_username_dir)
