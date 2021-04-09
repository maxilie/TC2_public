from django.contrib.auth.models import User
from django.core.management.base import BaseCommand


class Command(BaseCommand):

    def handle(self, *args, **options):
        ADMIN_EMAIL = 'any_email@gmail.com'
        ADMIN_USERNAME = 'admin'
        ADMIN_PASSWORD = 'yo&rP@ssw0rd_'
        print('Creating account for %s (%s)' % (ADMIN_USERNAME, ADMIN_EMAIL))
        User.objects.create_superuser(email=ADMIN_EMAIL, username=ADMIN_USERNAME, password=ADMIN_PASSWORD)
