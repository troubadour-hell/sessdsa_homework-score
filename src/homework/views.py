from . import forms
from . import models
from urllib import parse
from django.urls import reverse
from django.conf import settings
from django.shortcuts import render, redirect
from django.shortcuts import get_object_or_404
from django.core.mail import EmailMultiAlternatives
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse, StreamingHttpResponse, Http404, HttpResponseForbidden
import hashlib, datetime, json, os, zipfile, io, xlwt, filetype, codecs, mosspy, re


# import sys
# import markdown
# import signal
# import resource
# import traceback
# import random
# import time
# import urllib.request
# from itertools import chain
# from django.db.models import Q


# 学生登录
def login(request):
    if request == "GET":
        if request.session.get("is_login", None):  # 若session保持登录，跳转至个人页面
            return redirect(reverse("profile"))
        else:
            login_form = forms.StudentForm()  # 否则返回登录页面
            return render(request, 'homework/login.html', locals())
    if request.method == "POST":
        login_form = forms.StudentForm(request.POST)
        message = "请检查填写的内容！"
        if login_form.is_valid():
            student_id = login_form.cleaned_data['student_id']
            password = login_form.cleaned_data['password']
            try:
                student = models.Student.objects.get(student_id=student_id)
                if not student.has_confirmed:  # 邮箱是否验证
                    message = "该用户还未通过邮件确认！"
                    return render(request, 'homework/login.html', locals())
                if student.password == hash_code(password):  # 密码验证
                    request.session['is_login'] = True  # 写入session
                    request.session['student_id'] = student_id
                    request.session['student_name'] = student.name
                    return redirect(reverse("profile"))  # 跳转至个人页面
                else:
                    message = "密码不正确！"
            except ObjectDoesNotExist:
                message = "用户不存在！"  # 账号错误返回登录页面
                return render(request, 'homework/login.html', locals())
    login_form = forms.StudentForm()  # 如果是GET，返回登录页面
    return render(request, 'homework/login.html', locals())


# 哈希加密密码
def hash_code(s, salt='dsa'):
    h = hashlib.sha256()
    s = s + salt
    h.update(s.encode())
    return h.hexdigest()


# 生成验证码
def make_confirm_string(student):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    hashcode = hash_code(student.name, now)
    models.ConfirmString.objects.filter(student=student).delete()
    confirm_string = models.ConfirmString.objects.create(student=student, code=hashcode)
    confirm_string.save()
    return hashcode


# 发送邮件
def send_email(email, confirm_string_code):
    subject = '数算作业提交系统注册确认邮件'
    text_content = '''感谢注册数据结构与算法作业提交系统，这是注册确认邮件！
                    如果你看到这条消息，说明你正在纯文本模式浏览，请切换为HTML模式！'''
    html_content = '''
                    <p>感谢注册<a href="http://{}/confirm/{}/" target=blank>数据结构与算法作业提交系统</a>，
                    这是注册确认邮件！</p>
                    <p>请点击上方链接完成注册确认！</p>
                    <p>此链接有效期为{}天！</p>
                    '''.format(settings.SEVER_ADDRESS, confirm_string_code, settings.CONFIRM_DAYS)
    mail = EmailMultiAlternatives(subject, text_content, settings.EMAIL_HOST_USER, [email])
    mail.attach_alternative(html_content, "text/html")
    mail.send()


# 重发邮件
def resend_email(request, confirm_string_code, student_id):
    confirm_string = get_object_or_404(models.ConfirmString, code=confirm_string_code)
    student = get_object_or_404(models.Student, student_id=student_id)
    if confirm_string.student == student:
        send_email(str(student_id) + settings.EMAIL_POSTFIX, confirm_string.code)
        status = "重发"
        return render(request, 'homework/resend.html', locals())
    else:
        return Http404


# 学生注册
def register(request):
    if request.session.get('is_login', None):  # 若session保持登录，跳转至个人页面
        return redirect(reverse("profile"))
    if request.method == "POST":
        register_form = forms.RegisterForm(request.POST)
        message = "请检查填写的内容！"
        if register_form.is_valid():
            student_id = register_form.cleaned_data['student_id']
            name = register_form.cleaned_data['name']
            school = register_form.cleaned_data['school']
            password1 = register_form.cleaned_data['password1']
            password2 = register_form.cleaned_data['password2']
            if password1 != password2:  # 判断两次密码是否相同
                message = "两次输入的密码不同！"
                return render(request, 'homework/register.html', locals())
            else:
                try:
                    same_id_student = models.Student.objects.get(student_id=student_id)
                    if same_id_student.has_confirmed:
                        message = '用户已存在！'
                        return render(request, 'homework/register.html', locals())
                    else:
                        same_id_student.name = name
                        same_id_student.school = school
                        same_id_student.password = hash_code(password1)
                        same_id_student.save()
                        student = same_id_student
                        hashcode = make_confirm_string(same_id_student)  # 生成并保存验证码
                        send_email(str(student_id) + settings.EMAIL_POSTFIX, hashcode)  # 发送验证邮件
                        status = "更改密码"
                        return render(request, 'homework/resend.html', locals())
                except ObjectDoesNotExist:
                    new_student = models.Student.objects.create(name=name, school=school, student_id=student_id)
                    new_student.password = hash_code(password1)
                    new_student.save()
                    student = new_student
                    hashcode = make_confirm_string(student)  # 生成并保存验证码
                    send_email(str(student_id) + settings.EMAIL_POSTFIX, hashcode)  # 发送验证邮件
                    status = "注册"
                    return render(request, 'homework/resend.html', locals())
                finally:
                    pass
    register_form = forms.RegisterForm()  # 如果是GET，返回注册页面
    return render(request, 'homework/register.html', locals())


# 邮箱验证
def confirm(request, confirm_string_code):
    try:
        confirm_string = models.ConfirmString.objects.get(code=confirm_string_code)
    except ObjectDoesNotExist:
        message = '无效的确认请求!'
        return HttpResponse(message)
    confirm_string_c_time = confirm_string.c_time
    now = datetime.datetime.now()
    if now > confirm_string_c_time + datetime.timedelta(settings.CONFIRM_DAYS):
        confirm_string.student.delete()
        message = '您的邮件已经过期！请重新注册!'
        return HttpResponse(message)
    else:
        confirm_string.student.has_confirmed = True
        confirm_string.student.save()
        confirm_string.delete()
        message = '感谢确认，请使用账户登录！'
        return HttpResponse(message)


# 学生个人页面
def profile(request):
    if request.session.get('is_login', None):
        student_name = request.session.get("student_name", None)
        student_id = request.session.get("student_id", None)
        try:
            student = models.Student.objects.get(student_id=student_id)
        except ObjectDoesNotExist:
            request.session.flush()
            return redirect(reverse("login"))
        homeworks = models.Homework.objects.all().order_by("id").values()
        submits = models.Submit.objects.filter(student=student)
        scores = models.Score.objects.filter(student=student)
        try:
            moocScore = models.Mooc.objects.get(student=student)
            moocScore = round(moocScore.final+0.5)
        except:
            pass
        for h in homeworks:
            for s in submits:
                if h["id"] == s.homework_id:  # 作业与提交对应
                    h["last_submit"] = s.time
                    h["scored"] = s.scored
                    h["file_num"] = len(s.files.all())
                    files = s.files.all()
                    h["code"] = []
                    for f in files:
                        if ".py" in f.file.name:
                            h["code"].append(f.id)
                    if s.late:
                        h["late"] = True
                    s.save()
            for score in scores:
                if score.homework.id == h["id"]:
                    h["score"] = score.score
                    h["comment"] = score.comment
                    h["tac"] = score.tac
            if h["cutoff"] < datetime.datetime.now():
                h["late_submit"] = True
        # location = random.randint(1, 2120)
        # url = "https://xkcd.com/{}/info.0.json".format(location)
        # xkcd = json.loads(urllib.request.urlopen(url).read())
        return render(request, 'homework/profile.html', locals())
    return redirect(reverse("login"))  # 若未登录重定向到登录页面


# 学生登出
def logout(request):
    request.session.flush()  # 销毁session
    return redirect(reverse("login"))


# 学生上传作业
def upload(request):
    if request.session.get('is_login', None):
        student_id = request.session.get("student_id", None)
        files = request.FILES.getlist("file_data", None)  # 获取http传输的文件及附加信息
        homework_id = request.POST.get("homework_id", None)
        if student_id and files and homework_id:
            student = models.Student.objects.get(student_id=student_id)
            homework = models.Homework.objects.get(id=homework_id)
            score = models.Score.objects.filter(homework=homework, student=student)
            if datetime.datetime.now() > homework.cutoff and score:
                data = {"success": False, "message": "已评分，不能提交！"}
                return HttpResponse(json.dumps(data))
            if not student.elective:
                data = {"success": False, "message": "为非选课用户，不能提交！"}
            elif student and homework:
                older = models.Submit.objects.filter(student=student, homework=homework)  # 删除已有提交
                if older:
                    if older[0].block:
                        data = {"success": False, "message": "怀疑抄袭，当前提交已锁定"}
                        return HttpResponse(json.dumps(data))
                    for f in older[0].files.all():
                        try:
                            os.remove(f.file.name)
                        except:
                            pass
                        finally:
                            f.delete()
                    older[0].times = older[0].times + 1
                    for f in files:
                        models.File.objects.create(submit=older[0], file=f)
                    models.Score.objects.filter(student=student, homework=homework).delete()  # 删除已有分数
                    new_submit = older[0]
                else:
                    assistants = models.Assistant.objects.filter(working=True).order_by('id')
                    homework.iter += 1
                    if homework.iter >= assistants.count():
                        homework.iter = 0
                    homework.save()
                    new_submit = models.Submit.objects.create(student=student, homework=homework,
                                                              assistant=assistants[homework.iter], times=0)
                    for f in files:
                        models.File.objects.create(submit=new_submit, file=f)
                if datetime.datetime.now() > homework.cutoff:  # 若已过截止时间标记为补交
                    new_submit.late = True
                else:
                    new_submit.late = False
                new_submit.scored = False
                new_submit.time = datetime.datetime.now()
                new_submit.save()
                data = {"success": True, "number": str(len(files))}
            else:
                data = {"success": False}
        else:
            data = {"success": False}
    else:
        data = {"success": False, "message": "请登录后提交"}
    return HttpResponse(json.dumps(data))


# 文件迭代器
def file_iterator(file_name, chunk_size=512):
    with open(file_name, 'rb') as f:
        while True:
            c = f.read(chunk_size)
            if c:
                yield c
            else:
                break


# 学生下载已提交作业
def download(request, homework_id):
    if request.session.get('is_login', None):
        student_id = request.session.get("student_id", None)
        homework = models.Homework.objects.get(id=homework_id)
        student = models.Student.objects.get(student_id=student_id)
        submit = models.Submit.objects.get(homework=homework, student=student)
        files = submit.files.all()
        the_file_names = [f.file.name for f in files]
        now = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
        z_name = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                              homework.name + "_" + now + ".zip")
        z_file = zipfile.ZipFile(z_name, 'w')
        for f in the_file_names:
            z_file.write(f, f.split('/')[-1])
        z_file.close()
        with open(z_name, "rb") as z_file:
            data = z_file.read()
        os.remove(z_file.name)
        response = HttpResponse(data, content_type="application/zip")
        response["Content-Disposition"] = "attachment;filename=" + parse.quote(
            homework.name + "_" + student_id + ".zip")
        return response


# 学生运行提交的代码
def run_submit(request, file_id):
    if request.session.get('is_login', None):
        student_id = request.session.get("student_id", None)
        file = get_object_or_404(models.File, id=file_id)
        if file.submit.student.student_id == student_id:
            the_file_name = file.file.name
            title = the_file_name.split('/')[-1]
            with open(the_file_name, 'r', encoding="utf8") as f:
                code = f.read().replace(r"\n", "\\\\n")
                if code[0] == codecs.BOM_UTF8.decode("utf8"):  # 去除UFT8-BOM隐藏字符
                    code = code[1:]
            return render(request, "homework/submit_run.html", locals())
        else:
            return HttpResponseForbidden()


# 作业测试页面
def test(request, homework_name):
    return render(request, "homework/test/{}.html".format(homework_name), locals())


# 助教登录
def a_login(request):
    if request.session.get("a_login", None):  # 若已登录，重定向至个人页面
        return redirect(reverse("a_index"))
    if request.method == "POST":
        login_form = forms.AssistantForm(request.POST)
        message = "请检查填写的内容！"
        if login_form.is_valid():
            student_id = login_form.cleaned_data["student_id"]
            password = login_form.cleaned_data["password"]
            try:
                assistant = models.Assistant.objects.get(student_id=student_id)
                if assistant.password == hash_code(password):
                    request.session["a_login"] = True
                    request.session["student_id"] = student_id
                    request.session["student_name"] = assistant.name
                    return redirect(reverse("a_index"))
                else:
                    message = "密码不正确！"
            except ObjectDoesNotExist:
                message = "用户不存在！"
                return render(request, "homework/alogin.html", locals())
    login_form = forms.AssistantForm()
    return render(request, "homework/alogin.html", locals())


# 助教登出
def a_logout(request):
    request.session.flush()
    return redirect(reverse("a_login"))


# 助教注册
def a_register(request):
    if request.session.get("a_login", None):
        return redirect(reverse("a_index"))
    if request.method == "POST":
        register_form = forms.AssistantRegisterForm(request.POST)
        message = "请检查填写的内容！"
        if register_form.is_valid():
            student_id = register_form.cleaned_data["student_id"]
            name = register_form.cleaned_data["name"]
            secretcode = register_form.cleaned_data["secretCode"]
            password1 = register_form.cleaned_data["password1"]
            password2 = register_form.cleaned_data["password2"]
            if secretcode != settings.SECRET_WORD:  # 验证暗号
                message = "有空猜这个孩子都能打酱油了"
                return render(request, "homework/aregister.html", locals())
            if password1 != password2:  # 判断两次密码是否相同
                message = "两次输入的密码不同！"
                return render(request, "homework/aregister.html", locals())
            else:
                same_id_assistant = models.Assistant.objects.filter(student_id=student_id)
                if same_id_assistant:  # 判断学号是否已注册
                    message = "用户已存在！"
                    return render(request, "homework/aregister.html", locals())
                else:
                    new_assistant = models.Assistant.objects.create()
                    new_assistant.student_id = student_id
                    new_assistant.name = name
                    new_assistant.password = hash_code(password1)
                    new_assistant.save()
                    message = "注册成功，请登录！"
                    login_form = forms.AssistantForm()
                    return render(request, "homework/alogin.html", locals())  # 返回助教登录页面
    register_form = forms.AssistantRegisterForm()  # 若未GET，返回助教注册页面
    return render(request, "homework/aregister.html", locals())


# 助教个人页面
def a_index(request):
    if request.session.get("a_login", None):
        student_name = request.session.get("student_name", None)
        student_id = request.session.get("student_id", None)
        assistant = models.Assistant.objects.get(student_id=student_id)
        homeworks = models.Homework.objects.all().order_by("id")
        homeworklist = homeworks.values()
        for h in homeworklist:
            h["mine"] = models.Submit.objects.filter(assistant=assistant, homework=h["id"]).count()  # 分配给助教的作业数
            h["to_score"] = models.Submit.objects.filter(assistant=assistant, scored=False,
                                                         homework=h["id"]).count()  # 分配给助教待批的改作业数
            h["scored"] = h["mine"] - h["to_score"]
            h["all"] = models.Submit.objects.filter(homework=h["id"]).count()  # 全部作业数
            h["all_to_score"] = models.Submit.objects.filter(homework=h["id"], scored=False).count()  # 全部待批改的作业数
            h["tac_num"] = models.Score.objects.filter(homework=h["id"], tac=True).count()  # 助教之选作业数
            if h["cutoff"] < datetime.datetime.now():
                h["late"] = True
            now = datetime.datetime.now()
        assistantlist = models.Assistant.objects.filter(working=True).values()
        for a in assistantlist:
            assistant = models.Assistant.objects.get(id=a["id"])
            a["work"] = []
            for h in homeworks:
                all_homework = models.Submit.objects.filter(assistant=assistant, homework=h).count()  # 分配给助教的作业数
                to_score_homework = models.Submit.objects.filter(assistant=assistant, scored=False,
                                                                 homework=h).count()  # 分配给助教待批的改作业数
                scored_homework = all_homework - to_score_homework
                a["work"].append(
                    {"all_homework": all_homework, "scored_homework": scored_homework,
                     "to_score_homework": to_score_homework, "homework_id": h.id})
        return render(request, "homework/aindex.html", locals())
    return redirect(reverse("a_login"))


def get_media_url(file_name):
    return file_name[file_name.index("media") + 6:]


# 作业批量显示页面
def a_homeworks(request, tac, all_a, all_m, to_score, homework_id, assistant_id):
    if request.session.get("a_login", None):
        tac = json.loads(tac.lower())
        all_a = json.loads(all_a.lower())
        all_m = json.loads(all_m.lower())
        to_score = json.loads(to_score.lower())
        homework_id = json.loads(homework_id.lower())
        homework = models.Homework.objects.get(id=homework_id)
        # 根据参数决定显示哪些提交
        if tac:
            scores = models.Score.objects.filter(homework=homework, tac=True).order_by("student__student_id")
            submits = models.Submit.objects.filter(homework="-1").values()
            for sc in scores:
                submits = submits | models.Submit.objects.filter(homework=sc.homework, student=sc.student).values()
        else:
            if all_a:
                if to_score:
                    submits = models.Submit.objects.filter(homework=homework, scored=False).order_by(
                        "student__student_id").values()
                else:
                    submits = models.Submit.objects.filter(homework=homework).order_by("student__student_id").values()
            else:
                if assistant_id == "-1":
                    assistant = models.Assistant.objects.get(student_id=request.session.get("student_id", None))
                else:
                    assistant = models.Assistant.objects.get(id=json.loads(assistant_id))
                if all_m:
                    submits = models.Submit.objects.filter(homework=homework, assistant=assistant).order_by(
                        "student__student_id").values()
                else:
                    if to_score:
                        submits = models.Submit.objects.filter(homework=homework, scored=False,
                                                               assistant=assistant).order_by(
                            "student__student_id").values()
                    else:
                        submits = models.Submit.objects.filter(homework=homework, scored=True,
                                                               assistant=assistant).order_by(
                            "student__student_id").values()
        for s in submits:
            assistant = models.Assistant.objects.get(id=s["assistant_id"])
            student = models.Student.objects.get(id=s["student_id"])
            submit = models.Submit.objects.get(id=s["id"])
            try:
                score = models.Score.objects.get(student=student, homework=homework)
                s["score"] = score.score
                s["comment"] = score.comment
                s["tac"] = int(score.tac)
            except:
                pass
                s["tac"] = 0
            s["time_stamp"] = str(submit.time)
            s["assistant_name"] = assistant.name
            s["student_name"] = student.name
            s["student_id"] = student.student_id
            s["student_school"] = student.school
            s["previews"] = []
            s["downloads"] = []
            for f in submit.files.all():
                if ".py" in f.file.name:
                    s["previews"].append(reverse("code", args=(f.id,)))
                elif filetype.guess(f.file.name):
                    s["previews"].append(reverse("media", args=(get_media_url(f.file.name),)))
                else:
                    s["downloads"].append(reverse("media", args=(get_media_url(f.file.name),)))
        return render(request, "homework/ahomeworks.html", locals())


# 作业评分
def a_score(request):
    message = {"success": False}
    if request.session.get("a_login", None):
        student_id = request.session.get("student_id", None)
        submit_id = request.POST.get("submit_id", None)
        submit_time = request.POST.get("submit_time", None)
        score = int(request.POST.get("score", None))
        tac = json.loads(request.POST.get("tac", None))
        comment = request.POST.get("comment", None)
        if submit_id and score is not None:
            submit = models.Submit.objects.get(id=submit_id)
            if str(submit.time) != submit_time:  # 防止评分时上传新版本
                message["message"] = "学生提交了新版本，将刷新页面"
                return HttpResponse(json.dumps(message), content_type="application/json")
        models.Score.objects.filter(student=submit.student, homework=submit.homework).delete()
        new_score = models.Score.objects.create(student=submit.student, homework=submit.homework,
                                                score=score, tac=tac)
        if comment != "":
            new_score.comment = comment
        new_score.save()
        submit.scored = True
        assistant = models.Assistant.objects.get(student_id=student_id)
        submit.assistant = assistant
        submit.save()
        message = {"success": True, "score": str(new_score.score), "assistant": assistant.name, "comment": comment,
                   "tac": tac}
        return HttpResponse(json.dumps(message), content_type="application/json")


# 查看所有学生
def a_students(request):
    if request.session.get("a_login", None):
        students = models.Student.objects.all().order_by("student_id")
        studentlist = students.values()
        homeworks = models.Homework.objects.all().order_by("id")
        homeworklist = homeworks.values()
        scorelist = []
        for s in students:
            scores = []
            for h in homeworks:
                try:
                    score = models.Score.objects.get(student=s, homework=h)
                    scores.append(str(score.score))
                except:
                    scores.append('-')
            scorelist.append(scores)
        i = 0
        for s in studentlist:
            s["scores"] = scorelist[i]
            i = i + 1
        return render(request, "homework/astudents.html", locals())


# 查看单个学生作业信息
def a_student(request, student_id):
    if request.session.get("a_login", None):
        student = models.Student.objects.get(student_id=student_id)
        submits = models.Submit.objects.filter(student=student)
        homeworks = models.Homework.objects.all().order_by("id").values()
        scores = models.Score.objects.filter(student=student)
        for h in homeworks:
            for s in submits:
                if s.homework.id == h["id"]:
                    h["submit"] = True
                    h["submit_time"] = s.time
                    h["time_stamp"] = str(s.time)
                    h["scored"] = s.scored
                    h["submit_id"] = s.id
                    h["late"] = s.late
                    h["student_id"] = s.student.student_id
                    h["assistant_name"] = s.assistant.name
                    h["previews"] = []
                    h["downloads"] = []
                    for f in s.files.all():
                        if ".py" in f.file.name:
                            h["previews"].append(reverse("code", args=(f.id,)))
                        elif filetype.guess(f.file.name):
                            h["previews"].append(reverse("media", args=(get_media_url(f.file.name),)))
                        else:
                            h["downloads"].append(reverse("media", args=(get_media_url(f.file.name),)))
            for s in scores:
                if s.homework.id == h["id"]:
                    h["score"] = s.score
                    h["comment"] = s.comment
                    h["tac"] = s.tac
        return render(request, "homework/astudent.html", locals())


# 助教下载学生作业
def a_download(request, file_id):
    if request.session.get("a_login", None):
        file = models.File.objects.get(id=file_id)
        the_file_name = file.file.name
        response = StreamingHttpResponse(file_iterator(the_file_name))
        response["Content-Type"] = "application/octet-stream"
        response["Content-Disposition"] = "attachment;filename=" + parse.quote(the_file_name.split('/')[-1])
        return response


# 在线预览代码
def code_preview(request, file_id):
    if request.session.get("a_login", None):
        file = models.File.objects.get(id=file_id)
        the_file_name = file.file.name
        file_name = the_file_name.split('/')[-1]
        homework_name = file.submit.homework.name
        student_name = file.submit.student.name
        run = file.submit.homework.run
        just_code = file.submit.homework.just_code.replace(r"\n", "\\\\n")
        with open(the_file_name, 'r', encoding="utf8") as f:
            code = f.read().replace(r"\n", "\\\\n")
            if code[0] == codecs.BOM_UTF8.decode("utf8"):  # 去除UFT8-BOM隐藏字符
                code = code[1:]
        return render(request, "homework/code.html", locals())


# 助教批量下载学生作业
def a_zip(request, tac, all_a, all_m, to_score, homework_id, assistant_id):
    if request.session.get("a_login", None):
        tac = json.loads(tac.lower())
        all_a = json.loads(all_a.lower())
        all_m = json.loads(all_m.lower())
        to_score = json.loads(to_score.lower())
        homework_id = json.loads(homework_id.lower())
        homework = models.Homework.objects.get(id=homework_id)
        # 根据参数决定显示哪些提交
        if tac:
            scores = models.Score.objects.filter(homework=homework, tac=True).order_by("student__student_id")
            submits = models.Submit.objects.filter(homework="-1")
            for sc in scores:
                submits = submits | models.Submit.objects.filter(homework=sc.homework, student=sc.student)
        else:
            if all_a:
                if to_score:
                    submits = models.Submit.objects.filter(homework=homework, scored=False)
                else:
                    submits = models.Submit.objects.filter(homework=homework)
            else:
                if assistant_id == "-1":
                    assistant = models.Assistant.objects.get(student_id=request.session.get("student_id", None))
                else:
                    assistant = models.Assistant.objects.get(id=json.loads(assistant_id))
                if all_m:
                    submits = models.Submit.objects.filter(homework=homework, assistant=assistant)
                else:
                    if to_score:
                        submits = models.Submit.objects.filter(homework=homework, scored=False, assistant=assistant)
                    else:
                        submits = models.Submit.objects.filter(homework=homework, scored=True, assistant=assistant)
        the_file_paths = ['/'.join(s.files.all()[0].file.name.split('/')[:-1]) for s in submits]
        now = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
        z_name = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                              homework.name + "_" + now + ".zip")
        z_file = zipfile.ZipFile(z_name, 'w')
        for p in the_file_paths:
            for root, dirs, files in os.walk(p):
                for file in files:
                    fpath = '/'.join(p.split('/')[-2:])
                    z_file.write(os.path.join(root, file), fpath + '/' + file)
        z_file.close()
        with open(z_name, "rb") as z_file:
            data = z_file.read()
        os.remove(z_file.name)
        response = HttpResponse(data, content_type="application/zip")
        response["Content-Disposition"] = "attachment;filename=" + parse.quote(z_name.split('/')[-1])
        return response


def get_excel_stream(file):
    # StringIO操作的只能是str，如果要操作二进制数据，就需要使用BytesIO。
    excel_stream = io.BytesIO()
    # 这点很重要，传给save函数的不是保存文件名，而是一个BytesIO流（在内存中读写）
    file.save(excel_stream)
    # getvalue方法用于获得写入后的byte将结果返回给re
    res = excel_stream.getvalue()
    excel_stream.close()
    return res


# 下载所有学生名单及作业成绩excel表单
def get_excel(request):
    students = models.Student.objects.filter(elective=True).order_by("student_id")
    homeworks = models.Homework.objects.all().order_by("id")
    lines = []
    for s in students:
        line = []
        line.append(s.student_id)
        line.append(s.name)
        line.append(s.school)
        for h in homeworks:
            try:
                score = models.Score.objects.get(student=s, homework=h)
                line.append(str(score.score))
            except:
                line.append('-')
        try:
            mooc = models.Mooc.objects.get(student=s)
            line.append(mooc.final)
        except:
            line.append('-')
        lines.append(line)
    file = xlwt.Workbook()
    table = file.add_sheet("this", cell_overwrite_ok=True)
    title = ["学号", "姓名", "学院"] + [h.name for h in homeworks] + ['MOOC']
    for col, t in enumerate(title):
        table.write(0, col, t)
    for row, line in enumerate(lines):
        for col, item in enumerate(line):
            table.write(row + 1, col, item)
    now = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
    file_name = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), now + ".xls")
    file.save(file_name)
    res = get_excel_stream(file)
    response = HttpResponse(content_type="application/vnd.ms-excel")
    response["Content-Disposition"] = "attachment;filename=" + parse.quote(file_name.split('/')[-1])
    # 将文件流写入到response返回
    response.write(res)
    os.remove(file_name)
    return response


def duplicate_check(request, homework_id):
    if request.session.get("a_login", None):
        if homework_id == "!":
            homeworks = models.Homework.objects.all()
            return render(request, "homework/duplicate.html", locals())
        else:
            homework_id = int(homework_id)
            homework = get_object_or_404(models.Homework, id=homework_id)
            duplicate = models.DuplicateCheck.objects.filter(homework=homework)
            now = datetime.datetime.now()
            if len(duplicate) == 0:
                duplicate = models.DuplicateCheck.objects.create(homework=homework, time=now)
            else:
                duplicate = duplicate[0]
            submits_number = len(homework.submits.all())
            effective = now < duplicate.time + datetime.timedelta(settings.MOSS_DAYS)
            if submits_number == duplicate.submit_number and effective:
                if re.match(r'^http?:/{2}\w.+$', duplicate.result):
                    return redirect(duplicate.result)
                else:
                    return HttpResponse(u"此次作业没有py文件可以查重")
            else:
                userid = settings.MOSS_ID
                m = mosspy.Moss(userid, "python")
                media_path = settings.MEDIA_ROOT
                homework_path = os.path.join(media_path, homework.name)
                submit_dirs = [p for p in os.listdir(homework_path) if os.path.isdir(os.path.join(homework_path, p))]
                if os.path.exists(os.path.join(media_path, "{}.py".format(homework.name))):
                    m.addBaseFile(os.path.join(media_path, "{}.py".format(homework.name)))
                for s in submit_dirs:
                    m.addFilesByWildcard(os.path.join(homework_path, s, "*.py"))
                url = m.send()
                duplicate.result = url
                duplicate.time = datetime.datetime.now()
                duplicate.submit_number = submits_number
                duplicate.save()
                if re.match(r'^http?:/{2}\w.+$', url):
                    return redirect(url)
                else:
                    return HttpResponse(u"此次作业没有py文件可以查重")
# OJ页面
# def oj(request):
#     if request.session.get("is_login", None):  # 若session保持登录，跳转至OJ页面
#         student_id = request.session.get("student_id", None)
#         student = models.Student.objects.get(student_id=student_id)
#         questions = models.OJ.objects.all().order_by("id")
#         for q in questions:
#             try:
#                 oj_submit = models.OJSubmit.objects.get(student=student, oj=q)
#             except:
#                 oj_submit = models.OJSubmit.objects.create(student=student, oj=q)
#                 oj_submit.save()
#             q.index = "{0:04d}".format(q.ojid)
#             if q.submit == 0:
#                 q.submit = 1
#             q.acceptance = "{:.1%}".format(q.accept / q.submit)
#         return render(request, "homework/oj.html", locals())
#     else:
#         login_form = forms.StudentForm()  # 否则返回登录页面
#         return render(request, "homework/login.html", locals())


# def my_code(request, question_id):
#     if request.session.get("is_login", None):  # 若session保持登录，跳转至code页面
#         student_id = request.session.get("student_id", None)
#         student = get_object_or_404(models.Student, student_id=student_id)
#         question = get_object_or_404(models.OJ, id=question_id)
#         submit = get_object_or_404(models.OJSubmit, student=student, oj=question)
#         return render(request, "homework/my_code.html", locals())


# 限制运行时间
# def signal_handler(signum, frame):
#     raise RuntimeError


# 限制运行内存
# def memory_limit():
#     rsrc = resource.RLIMIT_DATA
#     soft, hard = resource.getrlimit(rsrc)
#     soft /= 100
#     resource.setrlimit(rsrc, (soft, hard))


# 显示问题详情、提交代码评判
# def question(request, question_id):
#     if request.session.get("is_login", None):
#         if request.method == "POST":
#             form = forms.CodeForm(request.POST)
#             if form.is_valid():
#                 student_id = request.session.get("student_id", None)
#                 student = models.Student.objects.get(student_id=student_id)
#                 user_code = form.cleaned_data["code"]
#                 question_id = form.cleaned_data["question_id"]
#                 q = get_object_or_404(models.OJ, id=question_id)
#                 q.submit = q.submit + 1
#                 try:
#                     oj_submit = models.OJSubmit.objects.get(student=student, oj=q)
#                 except:
#                     oj_submit = models.OJSubmit.objects.create(student=student, oj=q)
#                 oj_submit.submit = oj_submit.submit + 1
#                 oj_submit.code = user_code
#                 with open(q.file.name, 'r', encoding="UTF-8") as oj_file:
#                     oj = {}
#                     exec (oj_file.read(), oj)
#                     case = 0
#                     total = 0
#                     result = []
#                     evaluate = "Wrong Answer!"
#                     for test_case in oj["_oj_cases"]:
#                         message = {}
#                         memory_limit()
#                         signal.signal(signal.SIGALRM, signal_handler)
#                         signal.alarm(q.limit_time)
#                         try:
#                             exec (user_code, test_case["data_in"])
#                         except RuntimeError:
#                             message["error"] = "Time Out! Over " + str(q.limit_time) + "s."
#                         except MemoryError:
#                             message["error"] = "Memory Overflow!"
#                         except Exception as e:
#                             error = traceback.format_exc()
#                             message["error"] = error[error.find("File \"<string>\""):]
#                         finally:
#                             if "error" not in message:
#                                 if "result" in test_case["data_in"]:
#                                     if test_case["data_in"]["result"] == test_case["result"]:
#                                         total += test_case["points"]
#                                     else:
#                                         message["error"] = "Wrong Answer!"
#                                     message["input"] = test_case["data_in"]
#                                     message["std_out"] = test_case["result"]
#                                     message["user_out"] = test_case["data_in"]["result"]
#                                     message["input"].pop("__builtins__")
#                                     message["input"].pop("result")
#                                 else:
#                                     message["error"] = "Absent Answer!"
#                             message["id"] = case
#                             case = case + 1
#                             result.append(message)
#                     if total == 100:
#                         evaluate = "Accepted!"
#                         q.accept = q.accept + 1
#                         oj_submit.accept = oj_submit.accept + 1
#                     q.save()
#                     oj_submit.save()
#                 return render(request, "homework/oj_result.html", locals())
#         else:
#             q = get_object_or_404(models.OJ, id=question_id)
#             with open(q.file.name, 'r', encoding="UTF-8") as oj_file:
#                 oj = {}
#                 exec (oj_file.read(), oj)
#                 doc = list(oj["__doc__"])
#                 doc.insert(0, "# [{0:04d}] ".format(q.ojid))
#                 doc = "".join(doc)
#                 doc = markdown.markdown(doc)
#                 codeform = forms.CodeForm()
#                 return render(request, "homework/question.html", locals())
