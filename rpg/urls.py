from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^login/$', views.login, name='login'),
    url(r'^logout/$', views.logout, name='logout'),

    url(r'^story/$', views.storyOverview, name='storyOverview'),
    url(r'^story/new/$', views.newChapter, name='newChapter'),
    url(r'^story/([0-9]+)/$', views.viewChapterFirst, name='viewChapter'),
    url(r'^story/([0-9]+)/page/([0-9]+)/$', views.viewChapter, name='viewChapterPage'),
    url(r'^story/([0-9]+)/edit/$', views.editChapter, name='editChapter'),
    url(r'^story/([0-9]+)/archive/$', views.archiveChapter, name='archiveChapter'),
    url(r'^story/([0-9]+)/save/$', views.saveChapter, name='saveChapter'),

    url(r'^story/([0-9]+)/after/([0-9.]+)/post/$', views.addPost, name='addPost'),
    url(r'^story/([0-9]+)/post/([0-9]+)/edit/$', views.editPost, name='editPost'),
    url(r'^story/([0-9]+)/post/([0-9]+)/save/$', views.savePost, name='savePost'),
    url(r'^story/([0-9]+)/post/([0-9]+)/delete/$', views.deletePost, name='deletePost'),
    url(r'^story/([0-9]+)/post/([0-9]+)/comment/$', views.createComment, name='createComment'),

    url(r'^story/([0-9]+)/after/([0-9.]+)/talk/$', views.addTalk, name='addTalk'),
    url(r'^story/([0-9]+)/talk/([0-9]+)/utterance/$', views.addUtterance, name='addUtterance'),


    url(r'^roles/$', views.rolesOverviewFirst, name='rolesOverview'),
    url(r'^roles/page/([0-9]+)/$', views.rolesOverview, name='rolesOverviewPage'),
    url(r'^roles/new/$', views.newRole, name='newRole'),
    url(r'^roles/([0-9]+)/edit/$', views.editRole, name='editRole'),
    url(r'^roles/([0-9]+)/save/$', views.saveRole, name='saveRole'),

    url(r'^roles/getPicsForRole/$', views.getPicsForRole, name='getPicsForRole')
]