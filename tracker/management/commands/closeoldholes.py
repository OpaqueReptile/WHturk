from django.core.management.base import BaseCommand, CommandError
from tracker.models import Connection
from django.utils import timezone

class Command(BaseCommand):
    help = "Closes wormhole connections that haven't been updated in more than 8 hours"
    def handle(self, *args, **options):
        now = timezone.now()
        for con in Connection.objects.filter(can_timeout=True):
            elapsed = now - con.last_updated
            if elapsed.total_seconds() > 28800:
                self.stdout.write("Deleting connection: " + str(con))
                con.delete()


        self.stdout.write( self.style.SUCCESS("Finished cleaning up holes."))

