import datetime
import calendar

from django.db import models
from django.contrib.auth.models import User
from six import python_2_unicode_compatible
from django.conf import settings
from .modelComparators import compareEntry
from functools import cmp_to_key

import random

@python_2_unicode_compatible
class Role(models.Model):
    fullName = models.CharField(max_length=256)
    shortName = models.CharField(max_length=100)
    sex = models.CharField(max_length=1)
    born = models.DateField(null=True, blank=True)
    died = models.DateField(null=True, blank=True)
    lastUpdateDate = models.DateTimeField()
    lastUpdateUser = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="rolesLastUpdatedBy", related_query_name="roleLastUpdatedBy")
    newTo = models.ManyToManyField(User, blank=True, related_name="rolesNotYetSeenBy", related_query_name="roleNotYetSeenBy")

    def getShortName(self):
        return self.shortName

    def getLastUpdateDate(self):
        return self.lastUpdateDate.strftime('%d.%m.%Y')

    def getLastUpdateTime(self):
        return self.lastUpdateDate.strftime('%H:%M')

    def getFormBirthDate(self):
        return '{0.day:02d}.{0.month:02d}.{0.year:4d}'.format(self.born)

    def getFormDeathDate(self):
        return '{0.day:02d}.{0.month:02d}.{0.year:4d}'.format(self.died)

    def getPreferredPic(self):
        fav = Picture.objects.filter(role=self, favorite=True)
        if fav:
            return fav.first()
        else:
            pics = Picture.objects.filter(role=self)
            if pics:
                return random.choice(pics)
            else:
                pic = Picture()
                pic.destination='default.png'
                return pic

    def getFavoritePic(self):
        fav = Picture.objects.filter(role=self, favorite=True)
        if fav:
            return fav.first()

    def getRelationsOf(self):
        relations = list(Relation.objects.filter(models.Q(source=self) | models.Q(target=self)).order_by('pk'))
        relationships = [r.getRelationship(self) for r in relations]
        sorted(relationships, key=lambda rel : rel.type)
        return relationships

    def __str__(self):
        return self.shortName

    def __repr__(self):
        return self.shortName

class Relation(models.Model):
    type = models.CharField(max_length=100)
    reverseType = models.CharField(max_length=100)
    source = models.ForeignKey(Role, on_delete=models.CASCADE, related_name="relationSources", related_query_name="relationSource")
    target = models.ForeignKey(Role, on_delete=models.CASCADE, related_name="relationTargets", related_query_name="relationTarget")

    def setType(self, type):
        self.type = type
        if self.type == 'parent':
            self.reverseType = 'child'
        elif self.type == 'child':
            self.reverseType = 'parent'
        else:
            self.reverseType = self.type

    def setTypeFromDirection(self, role, type):
        if self.target == role and type == 'parent':
            self.setType('child')
        elif self.target == role and type == 'child':
            self.setType('parent')
        else:
            self.setType(type)

    def getType(self, source):
        if source == self.source:
            return self.type
        elif source == self.target:
            return self.reverseType

    def getTarget(self, source):
        if source == self.source:
            return self.target
        elif source == self.target:
            return self.source

    def getRelationship(self, source):
        if source == self.source:
            return Relationship(self)
        elif source == self.target:
            return Relationship(self, True)

    def __str__(self):
        return self.source.__str__() + ' is ' + self.type + ' of ' + self.target.__str__()

    def __repr__(self):
        return self.source.__str__() + ' is ' + self.type + ' of ' + self.target.__str__()

class Relationship():
    def __init__(self, relation, reverse=False):

        if reverse:
            self.type = relation.getType(relation.target)
            self.source = relation.target
            self.target = relation.source
        else:
            self.type = relation.getType(relation.source)
            self.source = relation.source
            self.target = relation.target

    def __str__(self):
        return self.source.__str__() + ' is ' + self.type + ' of ' + self.target.__str__()

    def __repr__(self):
        return self.source.__str__() + ' is ' + self.type + ' of ' + self.target.__str__()

@python_2_unicode_compatible
class Picture(models.Model):

    destination = models.CharField(max_length=40)
    role = models.ForeignKey(Role, on_delete=models.CASCADE, null = False)
    favorite = models.BooleanField(default=False)

    def isFavorite(self):
        return self.favorite

    def __str__(self):
        return self.destination


@python_2_unicode_compatible
class Chapter(models.Model):
    name = models.CharField(max_length=256)

    def __str__(self):
        return self.name

    def getStartYear(self):
        first_post = self.post_set.aggregate(models.Min('year'))
        first_talk = self.talk_set.aggregate(models.Min('year'))
        if first_post['year__min'] and first_talk['year__min']:
            if first_post['year__min'] < first_talk['year__min']:
                return first_post['year__min']
            else:
                return first_talk['year__min']
        elif first_post['year__min']:
            return first_post['year__min']
        else:
            return first_talk['year__min']

    def getEndYear(self):
        last_post = self.post_set.aggregate(models.Max('year'))
        last_talk = self.talk_set.aggregate(models.Max('year'))
        if last_post['year__max'] and last_talk['year__max']:
            if last_post['year__max'] < last_talk['year__max']:
                return last_post['year__max']
            else:
                return last_talk['year__max']
        elif last_post['year__max']:
            return last_post['year__max']
        elif last_talk['year__max']:
            return last_talk['year__max']
        else:
            return datetime.datetime.now().year

    def getLastEntry(self):
        entries = self.getEntries()
        if len(entries) > 0:
            return entries[-1]
        else:
            return None

    def getUpdates(self, user):
        last_posts = list(self.post_set.filter(newTo=user))
        last_talks = list(self.talk_set.filter(newTo=user))
        entries = last_posts + last_talks
        return sorted(entries, key=cmp_to_key(compareEntry))[:min(len(entries), 5)]

    def getEntries(self):
        posts = list(self.post_set.order_by('order'))
        talks = list(self.talk_set.order_by('order'))
        return sorted(posts+talks, key=cmp_to_key(compareEntry))

    def getLength(self):
        return self.post_set.count() + self.talk_set.count()

    def hasNews(self, user):
        for entry in self.getEntries():
            if user in entry.newTo.all():
                return True
        return False


@python_2_unicode_compatible
class Entry(models.Model):
    chapter = models.ForeignKey(Chapter, on_delete=models.CASCADE)
    order= models.CharField(max_length=512, default='1')
    lastUpdateDate = models.DateTimeField()
    year = models.IntegerField(default=0, blank=True, null=True)


    def __str__(self):
        return self.chapter.name+": "+str(self.year)

    def getLastUpdateDate(self):
        return self.lastUpdateDate.strftime('%d.%m.%Y')

    def getLastUpdateTime(self):
        return self.lastUpdateDate.strftime('%H:%M')

    class Meta:
        abstract = True


@python_2_unicode_compatible
class Post(Entry):
    text = models.TextField()
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, blank=True, null=True)
    roleName = models.CharField(max_length=100, blank=True, null=True)
    picture = models.ForeignKey(Picture, on_delete=models.SET_NULL, blank=True, null=True)
    youtube = models.CharField(max_length=1024, blank=True, null=True)
    lastUpdateUser = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="postsLastUpdatedBy", related_query_name="postLastUpdatedBy")
    newTo = models.ManyToManyField(User, blank=True, related_name="postsNotYetSeenBy", related_query_name="postNotYetSeenBy")

    def type(self):
        return "post"

    def __str__(self):
        return "ID("+str(self.id) + "), ORDER(" + str(self.order) + ")"

class Talk(Entry):
    lastUpdateUser = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="talksLastUpdatedBy", related_query_name="talkLastUpdatedBy")
    newTo = models.ManyToManyField(User, related_name="talksNotYetSeenBy", related_query_name="talkNotYetSeenBy")

    def getParticipants(self):
        utterances = self.utterance_set.order_by('id')
        roles = []
        for ut in utterances:
            if ut.role and not ut.role in roles:
                roles.append(ut.role)
            elif ut.roleName and not ut.roleName in roles:
                roles.append(ut.roleName)
        return roles

    def getNumberOfParticipants(self):
        return len(self.getParticipants())

    def type(self):
        return "talk"

@python_2_unicode_compatible
class Utterance(models.Model):
    talk = models.ForeignKey(Talk, on_delete=models.CASCADE)
    text = models.TextField()
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, blank=True, null=True)
    roleName = models.CharField(max_length=100, blank=True, null=True)
    picture = models.ForeignKey(Picture, on_delete=models.SET_NULL, blank=True, null=True)

    def __str__(self):
        return self.text

@python_2_unicode_compatible
class Comment(models.Model):
    user = models.ForeignKey(User, blank=True, null=True, on_delete=models.SET_NULL)
    comment = models.CharField(max_length=512)
    createDate = models.DateTimeField()
    post = models.ForeignKey(Post, on_delete=models.CASCADE, blank=True, null=True)
    talk = models.ForeignKey(Talk, on_delete=models.CASCADE, blank=True, null=True)

    def getCreateDate(self):
        return self.createDate.strftime('%d.%m.%Y %H:%M')

    def __str__(self):
        return self.comment

    class Meta:
        ordering = ['createDate']