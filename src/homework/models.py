import os
from django.db import models
from django.conf import settings
from django.dispatch import receiver
from xpinyin import Pinyin


# 定义文件存储路径
def upload_to(instance, filename):
    return '/'.join([settings.MEDIA_ROOT, instance.submit.homework.name,
                     instance.submit.homework.name + "_" + instance.submit.student.student_id + "_" + instance.submit.student.name,
                     filename])


# OJ文件存储路径
def oj_upload(instance, filename):
    p = Pinyin()
    return '/'.join([settings.MEDIA_ROOT, "OJ",
                     p.get_pinyin(instance.name) + "/" + "sample.py"])


# 学生
class Student(models.Model):
    student_id = models.CharField(max_length=10, null=False, blank=False, verbose_name="学号")  # 学号
    school = models.CharField(max_length=128, null=False, blank=False, verbose_name="学院")  # 学院
    name = models.CharField(max_length=128, null=False, blank=False, verbose_name="姓名")  # 姓名
    password = models.CharField(max_length=256, null=False, blank=False, verbose_name="密码")  # 密码
    time = models.DateTimeField(auto_now=True, verbose_name="注册时间")  # 注册时间
    has_confirmed = models.BooleanField(default=False, verbose_name="已验证")  # 是否已邮箱验证
    elective = models.BooleanField(default=False, verbose_name="已选课")  # 是否选课

    class Meta:
        ordering = ["student_id"]
        verbose_name = "学生"
        verbose_name_plural = "学生"

    def __str__(self):
        return self.name


# 验证码
class ConfirmString(models.Model):
    code = models.CharField(max_length=256)  # 验证码字符串
    student = models.OneToOneField(Student, on_delete=models.CASCADE)  # 一对一关联学生，级联删除
    c_time = models.DateTimeField(auto_now_add=True)  # 生成时间

    class Meta:
        verbose_name = "验证码"
        verbose_name_plural = "验证码"

    def __str__(self):
        return self.code


# 作业
class Homework(models.Model):
    name = models.CharField(max_length=128, null=False, blank=False, verbose_name="作业名")  # 名称
    description = models.CharField(max_length=256, null=False, blank=False, default="-", verbose_name="描述")  # 描述
    cutoff = models.DateTimeField(verbose_name="截止日期")  # 截止日期
    can_submit = models.BooleanField(default=True, verbose_name="允许提交")  # 是否允许提交
    tip = models.TextField(max_length=256, null=True, blank=True, verbose_name="Tip")  # 提示
    iter = models.PositiveSmallIntegerField(null=False, blank=False, default=0, verbose_name="作业分配迭代器")  # 用于迭代分配助教
    file_type = models.CharField(max_length=128, null=False, blank=False, default="['py']",
                                 verbose_name="可提交文件类型")  # 可提交文件类型
    just_code = models.TextField(null=False, blank=True, default="", verbose_name="测试代码")  # 测试代码

    class Meta:
        verbose_name = "作业"
        verbose_name_plural = "作业"

    def __str__(self):
        return self.name


# 助教
class Assistant(models.Model):
    student_id = models.CharField(max_length=10, null=False, blank=False, verbose_name="学号")  # 学号
    name = models.CharField(max_length=128, null=False, blank=False, verbose_name="姓名")  # 姓名
    password = models.CharField(max_length=256, null=False, blank=False, verbose_name="密码")  # 密码
    working = models.BooleanField(default=True, verbose_name="为其分配作业")  # 是否分配作业

    class Meta:
        verbose_name = "助教"
        verbose_name_plural = "助教"

    def __str__(self):
        return self.name


# 评分
class Score(models.Model):
    score = models.PositiveSmallIntegerField(null=False, blank=False, default=0, verbose_name="分数")  # 分数
    tac = models.BooleanField(null=False, blank=False, default=False, verbose_name="优秀")  # 助教之选优秀作业
    comment = models.TextField(max_length=512, default="", blank=True, verbose_name="反馈")  # 反馈
    student = models.ForeignKey(Student, on_delete=models.CASCADE, default="", verbose_name="学生")  # 关联学生，级联删除
    homework = models.ForeignKey(Homework, on_delete=models.CASCADE, default="", verbose_name="作业")  # 关联作业，级联删除

    class Meta:
        verbose_name = "评分"
        verbose_name_plural = "评分"


# 作业提交
class Submit(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, default="", verbose_name="学生")  # 关联学生，级联删除
    homework = models.ForeignKey(Homework, on_delete=models.CASCADE, default="", verbose_name="作业")  # 关联作业，级联删除
    assistant = models.ForeignKey(Assistant, on_delete=models.CASCADE, default="", verbose_name="批改人")  # 分配助教，级联删除
    scored = models.BooleanField(default=False, verbose_name="已评分")  # 是否已评分
    late = models.BooleanField(default=False, verbose_name="补交")  # 是否为补交
    time = models.DateTimeField(null=True, verbose_name="提交时间")  # 提交时间
    times = models.PositiveSmallIntegerField(null=False, blank=False, default=0, verbose_name="提交次数") # 提交次数
    block = models.BooleanField(null=False, blank=False, default=False, verbose_name="锁定")  # 发现抄袭锁定提交不允许覆盖

    # path = models.CharField(null=True, verbose_name="文件路径")  # 文件路径

    class Meta:
        verbose_name = "作业提交"
        verbose_name_plural = "作业提交"


# 文件
class File(models.Model):
    submit = models.ForeignKey(Submit, on_delete=models.CASCADE, default="", related_name='files', verbose_name="提交")
    file = models.FileField(upload_to=upload_to, verbose_name="文件")  # 上传文件

    class Meta:
        verbose_name = "提交文件"
        verbose_name_plural = "提交文件"


# 慕课成绩
class Mooc(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, default="", verbose_name="学生")  # 关联学生，级联删除
    chapter_1 = models.FloatField(null=False, blank=False, default=0, verbose_name="分数")  # 分数
    chapter_2 = models.FloatField(null=False, blank=False, default=0, verbose_name="分数")  # 分数
    chapter_3 = models.FloatField(null=False, blank=False, default=0, verbose_name="分数")  # 分数
    chapter_4 = models.FloatField(null=False, blank=False, default=0, verbose_name="分数")  # 分数

    class Meta:
        verbose_name = "慕课成绩"
        verbose_name_plural = "慕课成绩"


# OJ题目
# class OJ(models.Model):
#     ojid = models.IntegerField(null=False, blank=False, default=0, verbose_name="编号")  # 编号
#     name = models.CharField(max_length=128, null=False, blank=False, verbose_name="名称")  # 名称
#     file = models.FileField(upload_to=oj_upload, verbose_name="文件")  # 样例文件
#     time = models.DateTimeField(null=True, verbose_name="提交时间")  # 提交时间
#     limit_time = models.IntegerField(null=False, blank=False, default=2, verbose_name="时间限制")  # 时间限制
#     submit = models.IntegerField(null=False, blank=False, default=0, verbose_name="提交次数")  # 提交次数
#     accept = models.IntegerField(null=False, blank=False, default=0, verbose_name="通过次数")  # 通过次数
#
#     class Meta:
#         verbose_name = "OJ题目"
#         verbose_name_plural = "OJ题目"
#
#     def __str__(self):
#         return self.name


# OJ提交
# class OJSubmit(models.Model):
#     student = models.ForeignKey(Student, on_delete=models.CASCADE, default="", verbose_name="学生")  # 关联学生，级联删除
#     oj = models.ForeignKey(OJ, on_delete=models.CASCADE, default="", verbose_name="题目")  # 关联题目，级联删除
#     submit = models.IntegerField(null=False, blank=False, default=0, verbose_name="提交次数")  # 提交次数
#     accept = models.IntegerField(null=False, blank=False, default=0, verbose_name="通过次数")  # 通过次数
#     code = models.TextField(null=False, default="", verbose_name="代码")  # 代码
#     score = models.IntegerField(null=False, blank=False, default=0, verbose_name="分数")  # 分数
#
#     class Meta:
#         verbose_name = "OJ提交"
#         verbose_name_plural = "OJ提交"
#
#     def __str__(self):
#         return self.name


# 文件随提交记录级联删除
@receiver(models.signals.post_delete, sender=Submit)
def auto_delete_file_on_delete(sender, instance, **kwargs):
    files = instance.files.all()
    for f in files:
        if os.path.isfile(f.file.name):
            os.remove(f.file.name)
    files.delete()

# 文件随提交记录级联删除
# @receiver(models.signals.post_delete, sender=OJ)
# def auto_delete_file_on_delete(sender, instance, **kwargs):
#     if instance.file:
#         if os.path.isfile(instance.file.name):
#             os.remove(instance.file.name)
#         instance_dir = "/".join(instance.file.name.split("/")[:-1])
#         if os.path.isdir(instance_dir):
#             os.rmdir(instance_dir)
