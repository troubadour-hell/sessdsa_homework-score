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

urlpatterns = [
    url(r"^pass", hview.login, name="index"),
    url(r"^pass/", hview.login, name="login"),
    url(r"^pass/", hview.register, name="register"),
    url(r"^pass/(?P<confirm_string_code>.+)/$", hview.confirm, name="confirm"),
    url(r"^pass/(?P<confirm_string_code>.+)/(?P<student_id>.+)/$", hview.resend_email, name="resend_email"),
    url(r"^pass/", hview.profile, name="profile"),
    url(r"^pass/", hview.logout, name="logout"),
    url(r"^pass/", hview.upload, name="upload"),
    url(r"^pass/(?P<homework_id>.+)/$", hview.download, name="download"),
    url(r"^pass/", hview.a_register, name="a_register"),
    url(r"^pass/", hview.a_login, name="a_login"),
    url(r"^pass/", hview.a_index, name="a_index"),
    url(r"^pass/(?P<tac>.+)/(?P<all_a>.+)/(?P<all_m>.+)/(?P<to_score>.+)/(?P<homework_id>.+)/(?P<assistant_id>.+)/$",
        hview.a_homeworks, name="a_homeworks"),
    url(r"^pass/", hview.a_score, name="a_score"),
    url(r"^pass/", hview.a_logout, name="a_logout"),
    url(r"^pass/", hview.a_students, name="a_students"),
    url(r"^pass/(?P<student_id>.+)/$", hview.a_student, name="a_student"),
    url(r"^pass/(?P<tac>.+)/(?P<all_a>.+)/(?P<all_m>.+)/(?P<to_score>.+)/(?P<homework_id>.+)/(?P<assistant_id>.+)/$", hview.a_zip, name="a_zip"),
    url(r"^pass/(?P<file_id>.+)/$", hview.a_download, name="a_download"),
    url(r"^pass/", hview.get_excel, name="a_xls"),
    url(r"^pass/(?P<file_id>.+)/$", hview.code, name="code"),
    url(r"^pass/(?P<file_id>.+)/$", hview.pdf, name="pdf"),
    url(r"^pass/(?P<file_id>.+)/$", hview.image, name="image"),
    url(r"^pass/(?P<file_id>.+)/$", hview.pdf_stream, name="pdf_stream"),
    # url(r"^oj/", hview.oj),
    # url(r"^my_code/(?P<question_id>.+)/$", hview.my_code),
    # url(r"^question/(?P<question_id>.+)/$", hview.question),
    path("nothing/", admin.site.urls, name="manage"),
    url(r'^', hview.login),
]
