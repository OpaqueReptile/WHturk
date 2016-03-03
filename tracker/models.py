from __future__ import unicode_literals

from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext as _
# Create your models here.

@python_2_unicode_compatible
class System(models.Model):
    #A system has many characters, but a character only has one system
    #A system has a name
    name = models.CharField(max_length=20, unique=True)
    sysid = models.CharField(max_length=20, unique=True)
    color_code = models.CharField(max_length=10 )
    #A system has many connections, and a connection has two systems
    def __str__(self):
        return self.name

@python_2_unicode_compatible
class Character(models.Model):
    #a character has a name
    name = models.CharField(max_length=20,unique=True)
    #a character has a system, a system has many characters
    location = models.ForeignKey(System, on_delete=models.PROTECT, blank=True, null=True)
    #what kind of ship is our character in
    ship = models.CharField(max_length=20, blank=True, null=True)
    #how many points do they have currently
    points = models.FloatField(default=100000.0)
    #how many lifetime points
    lifetime_points = models.FloatField(default=0.0)
    def __str__(self):
        return self.name

@python_2_unicode_compatible
class Connection(models.Model):
    #A connection consists of two systems
    #System_A must be alphabetically first, or uniqueness cannot be confirmed
    system_A = models.ForeignKey(System, on_delete=models.PROTECT, related_name="System_A")
    system_B = models.ForeignKey(System, on_delete=models.PROTECT, related_name="System_B")
    last_updated = models.DateTimeField()
    verification_count = models.IntegerField()
    can_timeout = models.BooleanField()

    def clean(self, *args, **kwargs):
        if( self.system_A.name > self.system_B.name):
            raise ValidationError(
                _('Invalid alphabet: %(A) is less than %(B)'),
                code='invalid',
                params={'A': self.system_A.name,'B': self.system_B.name},
                )
        super(Connection,self).clean(*args, **kwargs)

    class Meta:
        unique_together = ("system_A", "system_B")

    def __str__(self):
        return self.system_A.name + " <-> " + self.system_B.name
