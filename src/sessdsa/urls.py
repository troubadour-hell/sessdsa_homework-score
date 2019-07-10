"""sessdsa URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path("", views.home, name="home")
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path("", Home.as_view(), name="home")
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path("blog/", include("blog.urls"))
"""
from django.contrib import admin
from django.urls import path
from django.conf.urls import url
from django.conf import settings
from homework import views as hview
from django.views.static import serve
from . import settings

urlpatterns = [
    url(r"^/", hview.login, name="login"),
    url(r"^/", hview.register, name="register"),
    url(r"^/(?P<confirm_string_code>.+)/$", hview.confirm, name="confirm"),
    url(r"^/(?P<confirm_string_code>.+)/(?P<student_id>.+)/$", hview.resend_email, name="resend_email"),
    url(r"^/", hview.profile, name="profile"),
    url(r"^/(?P<homework_name>.+)/$", hview.test, name="test"),
    url(r"^/", hview.logout, name="logout"),
    url(r"^/", hview.upload, name="upload"),
    url(r"^/(?P<homework_id>.+)/$", hview.download, name="download"),
    url(r"^/(?P<file_id>.+)/$", hview.run_submit, name="run_submit"),
    url(r"^/", hview.a_register, name="a_register"),
    url(r"^/", hview.a_login, name="a_login"),
    url(r"^/", hview.a_index, name="a_index"),
    url(r"^/(?P<tac>.+)/(?P<all_a>.+)/(?P<all_m>.+)/(?P<to_score>.+)/(?P<homework_id>.+)/(?P<assistant_id>.+)/$",
        hview.a_homeworks, name="a_homeworks"),
    url(r"^/", hview.a_score, name="a_score"),
    url(r"^/", hview.a_logout, name="a_logout"),
    url(r"^/", hview.a_students, name="a_students"),
    url(r"^/(?P<student_id>.+)/$", hview.a_student, name="a_student"),
    url(r"^/(?P<tac>.+)/(?P<all_a>.+)/(?P<all_m>.+)/(?P<to_score>.+)/(?P<homework_id>.+)/(?P<assistant_id>.+)/$",
        hview.a_zip, name="a_zip"),
    url(r"^/(?P<file_id>.+)/$", hview.a_download, name="a_download"),
    url(r"^/", hview.get_excel, name="a_xls"),
    url(r"^/(?P<homework_id>.+)/$", hview.duplicate_check, name="duplicate_check"),
    url(r"^/(?P<file_id>.+)/$", hview.code_preview, name="code"),
    url(r'^/(?P<path>.*)$', serve, {"document_root": settings.MEDIA_ROOT}, name="media"),
    # url(r"^oj/", hview.oj),
    # url(r"^my_code/(?P<question_id>.+)/$", hview.my_code),
    # url(r"^question/(?P<question_id>.+)/$", hview.question),
    path("/", admin.site.urls, name="manage"),
    url(r"^", hview.login, name="index"),
]
