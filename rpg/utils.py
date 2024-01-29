from .models import *
from django.conf import settings
from django.db.models import Q
from uuid import uuid4
from urllib.parse import parse_qs
import os
from .modelComparators import *
from functools import cmp_to_key

def managePics(request, role):
    avatarDir = settings.AVATAR_FOLDER
    newFavorite = request.POST.get('favorite')
    if (role.id is not None):
        pics = list(Picture.objects.filter(role=role))
        for pic in pics:
            picStillThere = False
            for i in range(1,101):
                if request.POST.get('existing_picture_'+str(i))==pic.destination:
                    picStillThere = True
                    break
            if not picStillThere:
                os.remove(avatarDir+pic.destination)
                pic.delete()
            elif pic.destination!=newFavorite and pic.isFavorite():
                pic.favorite = False
                pic.save()
            elif pic.destination==newFavorite and not pic.isFavorite():
                pic.favorite = True
                pic.save()

    for i in range(1,101):
        try:
            file = request.FILES['picture_'+str(i)]
            filename = str(uuid4())+'.'+file.name.split('.')[-1]
            with open(avatarDir + filename, 'wb+') as dest:
                for chunk in file.chunks():
                    dest.write(chunk)
                pic = Picture()
                pic.destination = filename
                pic.role = role
                if newFavorite == 'picture_'+str(i):
                    pic.favorite = True
                pic.save()
        except KeyError:
            continue

def manageRelations(request, role):
    if (role.id is not None):
        rels = Relation.objects.filter(Q(source=role) | Q(target=role))
        for rel in rels:
            relStillThere = False
            for i in range(1, 101):
                if request.POST.get('relation_type_'+str(i))==rel.getType(role) \
                    and request.POST.get('relation_target_'+str(i))==rel.getTarget(role).id:
                    relStillThere = True
                    break
            if not relStillThere:
                rel.delete()
    for i in range(1, 101):
        relType = request.POST.get('relation_type_'+str(i))
        relTarget = request.POST.get('relation_target_'+str(i))
        if not relType or not relTarget:
            continue
        try:
            existingRel = Relation.objects.get(Q(source=role, target__id=relTarget) | Q(source__id=relTarget, target=role))
        except Relation.DoesNotExist:
            existingRel = None
        if not existingRel:
            newRel = Relation()
            newRel.setType(relType)
            newRel.source = role
            newRel.target = Role.objects.get(pk=relTarget)
            newRel.save()
        elif existingRel.getType(role) != relType:
            existingRel.setTypeFromDirection(role, relType)
            existingRel.save()


def populateChapterFromRequest(request, chapter):
    try:
        chapter.name = request.POST['name']
    except KeyError:
        pass
    return chapter

def populatePostFromRequest(request, post, chapter_id):
    post.chapter = Chapter.objects.get(pk = chapter_id)
    if request.POST['role']:
        post.role = Role.objects.get(pk = request.POST['role'])
        post.roleName = None
        if (request.POST['picture']):
            post.picture = Picture.objects.get(pk=int(request.POST['picture']))
    elif request.POST['name']:
        post.roleName = request.POST['name']
        post.role = None
        post.picture = None
    else:
        post.roleName = None
        post.role = None
        post.picture = None

    post.year = request.POST['year']

    try:
        post.order = determinePostOrder(request.POST['precedent'], post.chapter.getEntries())
    except Exception as e:
        if not post.id:
            raise e

    post.text = request.POST['text']

    if (request.POST['youtube']):
        print(request.POST['youtube'])
        post.youtube = determineVideoCode(request.POST['youtube'])
    post.lastUpdateUser = request.user
    post.lastUpdateDate = datetime.datetime.now().isoformat()
    return post

def populateRoleFromRequest(request, role):
    try:
        role.fullName = request.POST['fullName']
    except KeyError:
        return

def populateCommentFromRequest(request, comment, entry_id):
    try:
        if request.POST['type'] == 'talk':
            entry = Talk.objects.get(pk=entry_id)
            comment.talk=entry
        elif request.POST['type'] == 'post':
            entry = Post.objects.get(pk=entry_id)
            comment.post=entry
        else:
            return
        comment.comment = request.POST['comment']
        comment.user = request.user
        comment.createDate = datetime.datetime.now().isoformat()
        return comment, request.POST['type']
    except KeyError:
        return

def populateRoleFromRequest(request, role):
    try:
        role.fullName = request.POST['fullName']
        role.shortName = request.POST['shortName']
        if request.POST['born']:
            role.born = datetime.datetime.strptime(request.POST['born'], '%d.%m.%Y').isoformat().split('T')[0]
        else:
            role.born = None
        if request.POST['died']:
            role.died = datetime.datetime.strptime(request.POST['died'], '%d.%m.%Y').isoformat().split('T')[0]
        else:
            role.died = None
        role.sex = request.POST['sex']
    except KeyError:
        pass
    role.lastUpdateUser = request.user
    role.lastUpdateDate = datetime.datetime.now().isoformat()
    return role

def getRoles(page):
    pageSize = settings.OVERVIEW_PAGE_SIZE
    start = (int(page) - 1) * pageSize
    roles = Role.objects.order_by('-lastUpdateDate')[start:start+pageSize]
    return roles

def getEntries(chapter, page):
    pageSize = settings.STORY_PAGE_SIZE
    start = (int(page) - 1) * pageSize
    posts = [a for a in list(Post.objects.filter(chapter__id=chapter.id))]
    talks = [b for b in list(Talk.objects.filter(chapter__id=chapter.id))]
    entries = sorted(posts+talks, key=cmp_to_key(compareEntry))[start:start+pageSize]
    print(entries)
    return entries

def determinePredecessor(chapter, page):
    if (int(page) == 1):
        return 0
    pageSize = settings.STORY_PAGE_SIZE
    ind = (int(page) -1) * pageSize - 1
    return chapter.getEntries()[ind].id

def prettifyTalks(entries):
    for entry in entries:
        if entry.type() == "talk":
            participants = entry.getParticipants()
            sidemap = {}
            for i in range(len(participants)):
                if isinstance(participants[i], unicode):
                    sidemap[participants[i]] = i % 2
                else:
                    sidemap[participants[i].shortName] = i % 2
            sidedUtterances = []
            for utterance in entry.utterance_set.all():
                if (utterance.roleName and sidemap[utterance.roleName] == 1) or \
                    (utterance.role and sidemap[unicode(utterance.role.shortName)] == 1):
                    utterance.side = "left"
                elif (utterance.roleName and sidemap[utterance.roleName] == 0) or \
                    (utterance.role and sidemap[unicode(utterance.role.shortName)] == 0):
                    utterance.side = "right"
                sidedUtterances.append(utterance)
            entry.sidedUtterances = sidedUtterances


def getRolePages(page):
    pageSize = settings.OVERVIEW_PAGE_SIZE
    roleNumber = Role.objects.all().count()
    additionalPage = 0 if roleNumber % pageSize == 0 else 1
    totalPages = Role.objects.all().count() // pageSize + additionalPage
    visiblePages = [p for p in range(1, totalPages+1) if p > int(page)-4 and p < int(page) + 4]
    return visiblePages, totalPages

def getEntryPages(chapter, page):
    pageSize = settings.STORY_PAGE_SIZE
    entryNumber = chapter.getLength()
    additionalPage = 0 if entryNumber % pageSize == 0 else 1
    totalPages = chapter.getLength() // pageSize + additionalPage
    visiblePages = [p for p in range(1, totalPages+1) if p > int(page)-4 and p < int(page) + 4]
    return visiblePages, totalPages

def determinePageForEntry(chapter_id, entry):
    if not entry:
        return 1
    pageSize = settings.STORY_PAGE_SIZE
    chapter = Chapter.objects.get(pk = chapter_id)
    entries = chapter.getEntries()
    for x in range(0, len(entries)):
        if entries[x].id == entry.id:
            return x//pageSize + 1

def determinePostOrder(order, chapter):
    if len(chapter) == 0:
        return 1
    else:
        lowerbound = order

    if chapter[-1].order == order:
        return str(int(lowerbound.split('.')[0]) + 1)
    elif order == '0':
        upperbound = chapter[0].order
    else:
        for x in range(0, len(chapter)):
            if chapter[x].order == lowerbound:
                upperbound = chapter[x + 1].order

    temp = ".".join(lowerbound.split('.')[:-1]) + "." + str(int(lowerbound.split('.')[-1]) + 1)
    if temp[0] == '.':
        temp = temp[1]
    print("temp = " + temp)
    if compareOrder(temp, upperbound) < 0:
        print("use temp")
        return temp
    temp = lowerbound + ".1"
    print("count temp up to " + temp)
    while compareOrder(temp, upperbound) >= 0:
        temp = ".".join(temp.split('.')[:-1]) + '.0.1'
        print("not enough")
        print("count temp up to " + temp)
    return temp

def determineVideoCode(url):
    queries = parse_qs(url)
    for q in queries:
        if q[-1] == 'v':
            return queries[q][0]