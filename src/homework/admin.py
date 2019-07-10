from django.contrib import admin
from .models import *
from django.forms import TextInput, Textarea
from django.db import models


# Register your models here.

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    search_fields = ['name', 'student_id']
    list_filter = ['school']
    list_display = ('name', 'student_id', 'school', 'elective')


@admin.register(Submit)
class SubmitAdmin(admin.ModelAdmin):
    search_fields = ['student__name', 'student__student_id']
    list_filter = ["homework__name"]
    list_display = ('homework_name', 'student_id', 'student_name', 'assistant_name')
    ordering = ["-time"]

    def homework_name(self, obj):
        return obj.homework.name

    def student_id(self, obj):
        return obj.student.student_id

    def student_name(self, obj):
        return obj.student.name

    def assistant_name(self, obj):
        return obj.assistant.name


@admin.register(File)
class FileAdmin(admin.ModelAdmin):
    list_display = ('id', 'student_name', 'student_name', 'homework_name')
    search_fields = ['id', 'submit__student__id', 'submit__student__name']
    list_filter = ["submit__homework"]

    def student_id(self, obj):
        return obj.submit.student.student_id

    def student_name(self, obj):
        return obj.submit.student.name

    def homework_name(self, obj):
        return obj.submit.homework.name


@admin.register(Homework)
class HomeWorkAdmin(admin.ModelAdmin):
    list_display = ('name', 'cutoff')
    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size': '20'})},
        models.TextField: {'widget': Textarea(attrs={'rows': 20, 'cols': 80, 'style': 'resize:none'})},
    }


@admin.register(Assistant)
class AssistantAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'student_id')


@admin.register(Score)
class ScoreAdmin(admin.ModelAdmin):
    search_fields = ['student__name']
    list_filter = ['homework__name']
    list_display = ('student_id', 'student_name', 'homework_name', 'score')

    def student_id(self, obj):
        return obj.student.student_id

    def student_name(self, obj):
        return obj.student.name

    def homework_name(self, obj):
        return obj.homework.name


@admin.register(Mooc)
class MoocAdmin(admin.ModelAdmin):
    search_fields = ['student__name']
    list_display = ['student_name', 'student_id', 'test', 'homework', 'exam', 'discuss', 'final']

    def student_id(self, obj):
        return obj.student.student_id

    def student_name(self, obj):
        return obj.student.name


@admin.register(DuplicateCheck)
class DuplicateAdmin(admin.ModelAdmin):
    list_display = ["homework_name", "time", "result"]

    def homework_name(self, obj):
        return obj.homework.name


# @admin.register(OJ)
# class OJAdmin(admin.ModelAdmin):
#     search_fields = ['OJ__name']
#     list_display = ('id', 'name', 'ojid', 'file')
#
#
# @admin.register(OJSubmit)
# class OJSubmitAdmin(admin.ModelAdmin):
#     list_display = ["id", "student_name", "oj_name", "code"]
#
#     def student_name(self, obj):
#         return obj.student.name
#
#     def oj_name(self, obj):
#         return obj.oj.name


@admin.register(ConfirmString)
class ConfirmStringAdmin(admin.ModelAdmin):
    list_display = ['id', 'student_name', 'student_id']

    def student_id(self, obj):
        return obj.student.student_id

    def student_name(self, obj):
        return obj.student.name


admin.site.site_header = "数据结构与算法作业提交评分系统"
admin.site.site_title = "数据结构与算法作业提交评分系统"
