from django.core.management.base import BaseCommand, CommandError
from tracker.models import Connection, System
from django.utils import timezone

class Command(BaseCommand):
    help = "Creates example wormhole connections between market hubs for testing"
    def handle(self, *args, **options):
        now = timezone.now()
        jita = System.objects.get(name="Jita")
        hek = System.objects.get(name="Hek")
        dodixie = System.objects.get(name="Dodixie")
        amarr = System.objects.get(name="Amarr")
        j1 = System.objects.get(name="J100001")
        j2 = System.objects.get(name="J100009")
        j3 = System.objects.get(name="J100015")
        j4 = System.objects.get(name="J100033")

        #jita to dixie
        con1 = Connection(system_A=j1,system_B=jita,last_updated=timezone.now(),verification_count=1,can_timeout=True)
        con2 = Connection(system_A=j1,system_B=j2,last_updated=timezone.now(),verification_count=1,can_timeout=True)
        con3 = Connection(system_A=dodixie,system_B=j2,last_updated=timezone.now(),verification_count=1,can_timeout=True)
        #amarr to hek
        con4 = Connection(system_A=amarr,system_B=j3,last_updated=timezone.now(),verification_count=1,can_timeout=True)
        con5 = Connection(system_A=j3,system_B=j4,last_updated=timezone.now(),verification_count=1,can_timeout=True)
        con6 = Connection(system_A=hek,system_B=j4,last_updated=timezone.now(),verification_count=1,can_timeout=True)

        con1.save()
        con2.save()
        con3.save()
        con4.save()
        con5.save()
        con6.save()

        self.stdout.write( self.style.SUCCESS("Finished making test connections."))

