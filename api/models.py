from django.db import models
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.contrib.auth.models import User
# class Myuser(models.Model):
#     user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='extension')


class Location(models.Model):
    # 发文部门基本表
    code = models.CharField(max_length=10, db_index=True, unique=True)
    province = models.CharField(max_length=10, db_index=True)
    city = models.CharField(max_length=10, db_index=True, blank=True, null=True)
    file_count = models.PositiveIntegerField(default=0)

    
class Config(models.Model):
    # 配置文件表
    loc = models.ForeignKey("Location",on_delete=models.CASCADE, verbose_name="发文地区")
    gov = models.CharField(max_length=10, db_index=True)
    # auth = models.CharField(max_length=10, db_index=True)  这里应该是一个指向user的foreignkey
    file_count = models.PositiveIntegerField(default=0)
    target_url = models.URLField()
    # 以下以pattern结尾的均为配置xpath表达式
    item_pattern = models.CharField(max_length=128, blank=True, null=True)
    main_text_pattern = models.CharField(max_length=128, blank=True, null=True)
    date_pattern = models.CharField(max_length=128, blank=True, null=True)
    zupei_pattern = models.CharField(max_length=128, blank=True, null=True)
    source_pattern = models.CharField(max_length=128, blank=True, null=True)
    title_pattern = models.CharField(max_length=128, blank=True, null=True)
    next_pattern = models.CharField(max_length=128, blank=True, null=True)
    action_pattern = models.CharField(max_length=512, blank=True, null=True)
    

class Links(models.Model):
    # 子链接表
    loc = models.ForeignKey("Location", on_delete=models.CASCADE)
    config = models.ForeignKey("Config", null=True, blank=True, on_delete=models.SET_NULL)
    gov = models.CharField(max_length=10, db_index=True)
    title = models.CharField(max_length=512, db_index=True)
    pub_date = models.DateTimeField(blank=True, null=True, db_index=True)
    crawl_date = models.DateTimeField(auto_now_add=True)  # 创建时间
    sub_url = models.URLField()  # 子链接
    zupei_type = models.CharField(max_length=128, null=True, blank=True, db_index=True)
    source = models.CharField(max_length=128, null=True, blank=True)
    
    class Meta:
        unique_together = ('loc','title')


class Details(models.Model):
    # 详细内容（正文部分）
    links = models.OneToOneField("Links", on_delete=models.CASCADE, related_name="details")
    main_text = models.TextField(null=True, blank=True)
    img = models.TextField(null=True, blank=True)
    attachment = models.TextField(null=True, blank=True)