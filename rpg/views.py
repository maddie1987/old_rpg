from django.http import JsonResponse, HttpResponseRedirect, Http404, HttpResponseForbidden
from django.shortcuts import render
from django.contrib.auth import authenticate
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout
from django.urls import reverse
from django.core import serializers
from django.contrib import messages
from django.shortcuts import redirect
from django.db.models import Q
from django.conf import settings

import logging

from .models import *
from .utils import *
from uuid import uuid4
import os

logger = logging.getLogger(__name__)

def login(request):
    username = request.POST['username']
    password = request.POST['password']
    user = authenticate(username=username, password=password)
    if user is not None:
        auth_login(request, user)
    else:
        messages.add_message(request, messages.ERROR, 'Username oder Passwort falsch.')
    return HttpResponseRedirect(reverse('rpg:index'))

def logout(request):
    auth_logout(request)
    return HttpResponseRedirect(reverse('rpg:index'))

def index(request):
    if request.user.is_authenticated:
        chapters = Chapter.objects.all()
        sorted(chapters, key=lambda x: x.getEndYear())
        for chapter in chapters:
            updates = chapter.getUpdates(request.user)
            if len(updates) > 0:
                chapter.lastUpdates = chapter.getUpdates(request.user)
                for entry in chapter.lastUpdates:
                    entry.targetPage = determinePageForEntry(chapter.id, entry)
            chapter.lastEntry = chapter.getLastEntry()
            chapter.lastEntryTargetPage = determinePageForEntry(chapter.id, chapter.lastEntry)
        roles = Role.objects.filter(newTo=request.user).order_by('-lastUpdateDate')
        context = initializeContext()
        context["postUpdates"] = chapters
        context["roleEdits"] = roles
        return render(request, 'rpg/index.html', context)
    else:
        return render(request, "rpg/login.html")

def storyOverview(request):
    if request.user.is_authenticated:
        chapters = Chapter.objects.all()
        sorted(chapters, key=lambda x: x.getEndYear())
        for chapter in chapters:
            chapter.lastUpdates = chapter.getUpdates(request.user)
            for entry in chapter.lastUpdates:
                entry.targetPage = determinePageForEntry(chapter.id, entry)
            chapter.lastEntry = chapter.getLastEntry()
            chapter.lastEntryTargetPage = determinePageForEntry(chapter.id, chapter.getLastEntry())
        context = initializeContext("story")
        context["chapters"] = chapters
        return render(request, 'rpg/storyOverview.html', context)
    else:
        return render(request, 'rpg/login.html')

def newChapter(request):
    return redirect('rpg:editChapter', 0)

def editChapter(request, id):
    if request.user.is_authenticated:
        context = initializeContext("story")
        context['id'] = id
        if int(id) > 0:
            chapter = Chapter.objects.get(pk=id)
            context['chapter'] = chapter
        return render(request, 'rpg/editChapter.html', context)
    else:
        return render(request, 'rpg/login.html')


def saveChapter(request, id):
    if request.user.is_authenticated:
        if int(id)==0:
            chapter = Chapter()
        else:
            chapter = Chapter.objects.get(pk=id)
        chapter = populateChapterFromRequest(request, chapter)
        chapter.save()
        return redirect('rpg:storyOverview')
    else:
        return render(request, 'rpg/login.html')

def viewChapterFirst(request, id):
    return redirect('rpg:viewChapterPage', id, 1)

def viewChapter(request, id, page):
    if request.user.is_authenticated:
        context = initializeContext("story")
        chapter = None
        if id:
            chapter = Chapter.objects.get(pk=id)
        if not chapter:
            raise Http404("Chapter doesn't exist")
        context["chapter"] = chapter
        entries = getEntries(chapter, page)
        for entry in entries:
            if request.user in entry.newTo.all():
                entry.newTo.remove(request.user)
                entry.wasNew = True

        prettifyTalks(entries)
        context["entries"] = entries
        context["predecessor"] = determinePredecessor(chapter, page)
        visiblePages, totalPages = getEntryPages(chapter, page)
        context["visiblePages"] = visiblePages
        context["totalPages"] = totalPages
        context["currentPage"] = int(page)
        return render(request, 'rpg/chapterView.html', context)
    else:
        return render(request, 'rpg/login.html')

def addPost(request, id, precedent):
    if request.user.is_authenticated:
        context = initializeContext("story")
        chapter = None
        if id:
            chapter = Chapter.objects.get(pk=id)
        if not chapter:
            raise Http404("Chapter doesn't exist")
        context["chapter"] = chapter
        entries = chapter.getEntries()
        if entries:
            postEnv = settings.POST_ENVIRONMENT_SIZE
            precedentIndex = -1
            for x in range(0, len(entries)):
                print(entries[x].order)
                if entries[x].order == precedent:
                    precedentIndex = x
                    break
            if precedentIndex >= 0:
                context["mostRecentEntries"] = entries[max(0, precedentIndex-postEnv+1):precedentIndex+1]
                context["minyear"] = entries[precedentIndex].year
            if precedentIndex < len(entries)-1:
                context["nextEntries"] = entries[precedentIndex+1:min(len(entries), precedentIndex+postEnv+1)]
                context["maxyear"] = entries[precedentIndex+1].year
        context["precedent"] = precedent
        context["roles"] = Role.objects.all().order_by('shortName')
        return render(request, 'rpg/editPost.html', context)
    else:
        return render(request, 'rpg/login.html')

def editPost(request, chapter_id, post_id):
    if request.user.is_authenticated:
        context = initializeContext("story")
        post = Post.objects.get(pk=post_id)
        chapter = Chapter.objects.get(pk=chapter_id)
        context['post'] = post
        context['chapter'] = chapter
        entries = chapter.getEntries()
        if entries:
            postEnv = settings.POST_ENVIRONMENT_SIZE
            postIndex = -1
            for x in range(0, len(entries)):
                if (entries[x].id == int(post_id)):
                    postIndex = x
                    break
            if postIndex >= 0:
                context["mostRecentEntries"] = entries[max(0, postIndex-postEnv):postIndex]
                if postIndex > 0:
                    context["minyear"] = entries[postIndex-1].year
            if postIndex < len(entries)-1:
                context["nextEntries"] = entries[postIndex+1:min(len(entries), postIndex+postEnv+1)]
                context["maxyear"] = entries[postIndex+1].year
        context["roles"] = Role.objects.all().order_by('shortName')
        return render(request, 'rpg/editPost.html', context)
    else:
        return render(request, 'rpg/login.html')

def savePost(request, chapter_id, post_id):
    if request.user.is_authenticated:
        if int(post_id) == 0:
            post = Post()
        else:
            post = Post.objects.get(pk=post_id)
        post = populatePostFromRequest(request, post, chapter_id)
        post.save()
        uninformedUsers = User.objects.exclude(username=request.user.username).all()
        post.newTo.set(uninformedUsers)
        post.save()
        return redirect(('{}#' + str(post.id)).format(reverse('rpg:viewChapterPage', args=[chapter_id, determinePageForEntry(chapter_id, post)])))
    else:
        return render(request, 'rpg/login.html')

def deletePost(request, chapter_id, post_id):
    if request.user.is_authenticated:
        chapter = Chapter.objects.get(pk=chapter_id)
        entries = chapter.getEntries()
        post = None
        previous = None
        if entries:
            for x in range(0, len(entries)):
                if (entries[x].id == int(post_id)):
                    post = entries[x]
                    break
                else:
                    previous = entries[x]
        if post:
            post.delete(keep_parents=True)
        if previous:
            return redirect(('{}#'+str(previous.id)).format(reverse('rpg:viewChapterPage', args=[chapter_id, determinePageForEntry(chapter_id, previous)])))
        else:
            return viewChapterFirst(request, chapter_id)
    else:
        return render(request, 'rpg/login.html')

def createComment(request, chapter_id, entry_id):
    if request.user.is_authenticated:
        comment = Comment()
        comment, type= populateCommentFromRequest(request, comment, entry_id)
        comment.save()
        entry = comment.post
        if not entry:
            entry = comment.talk
        uninformedUsers = User.objects.exclude(username=request.user.username).all()
        entry.newTo.set(uninformedUsers)
        entry.save()
        return redirect(('{}#'+entry_id).format(reverse('rpg:viewChapterPage', args=[chapter_id, determinePageForEntry(chapter_id, entry)])))
    else:
        return render(request, 'rpg/login.html')

def addTalk(request, chapter, predecessor):
    pass

def addUtterance(request, chapter, talk):
    pass

def saveEntry(request, chapter, id):
    pass

def archiveChapter(request, id):
    pass


def rolesOverviewFirst(request):
    return redirect('rpg:rolesOverviewPage', 1)

def rolesOverview(request, page):
    if request.user.is_authenticated:
        roles = getRoles(page)
        context = initializeContext("roles")
        context["rpgRoles"] = roles
        for role in roles:
            if request.user in role.newTo.all():
                context["news"] = True
                break
        visiblePages, totalPages = getRolePages(page)
        context["visiblePages"] = visiblePages
        context["totalPages"] = totalPages
        context["currentPage"] = int(page)
        return render(request, 'rpg/rolesOverview.html', context)
    else:
        return render(request, 'rpg/login.html')

def newRole(request):
    return redirect('rpg:editRole', 0)

def editRole(request, id):
    if request.user.is_authenticated:
        context = initializeContext("roles")
        context['id'] = id
        if int(id) > 0:
            role = Role.objects.get(pk=id)
            if request.user in role.newTo.all():
                role.newTo.remove(request.user)
                role.save()
            context['role'] = role
            context['nextRelation'] = Relation.objects.filter(Q(source=role) | Q(target=role)).count() + 1
            context['possibleRelations'] = Role.objects.exclude(id=role.id)
        else:
            context['nextRelation'] = 1
            context['possibleRelations'] = Role.objects.all()
        return render(request, 'rpg/editRole.html', context)
    else:
        return render(request, 'rpg/login.html')

def saveRole(request, id):
    if request.user.is_authenticated:
        if int(id)==0:
            role = Role()
        else:
            role = Role.objects.get(pk=id)
        role = populateRoleFromRequest(request, role)
        role.save()
        uninformedUsers = User.objects.exclude(username=request.user.username).all()
        role.newTo.set(uninformedUsers)
        role.save()
        manageRelations(request, role)
        managePics(request, role)
        return redirect('rpg:rolesOverview')
    else:
        return render(request, 'rpg/login.html')





def initializeContext(context=""):
    if (context=="roles"):
        return {"roles":True, "story":False}
    elif (context=="story"):
        return {"roles":False, "story":True}
    else:
        return {"roles":False, "story":False}



################### AJAX ENDPOINTS ####################
def getPicsForRole(request):
    if request.user.is_authenticated:
        pics = Picture.objects.filter(role__id = request.GET['role_id'])
        return JsonResponse(
            {'pics': [{
                          'dest': p.destination,
                          'fav': p.favorite,
                          'id': p.id
                      } for p in pics]
             })
    else:
        return HttpResponseForbidden('No access')