from django.db import models
from django.contrib.auth.models import User


class Location(models.Model):
    # 发文部门基本表
    code = models.CharField(max_length=10, db_index=True, unique=True)
    province = models.CharField(max_length=20, db_index=True)
    city = models.CharField(max_length=20, db_index=True, blank=True, null=True)
    file_count = models.PositiveIntegerField(default=0)


class Config(models.Model):
    # 配置文件表
    loc = models.ForeignKey("Location", on_delete=models.CASCADE, verbose_name="发文地区")
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    gov = models.CharField(max_length=10, db_index=True, default="人民政府")
    is_active = models.BooleanField(default=True)
    file_count = models.PositiveIntegerField(default=0)
    zupei_type = models.CharField(max_length=45, blank=True, null=True, default="")
    target_url = models.CharField(max_length=512)
    # 以下以pattern结尾的均为配置xpath表达式
    item_pattern = models.CharField(max_length=128, blank=True, null=True, default="")
    main_text_pattern = models.CharField(max_length=128, blank=True, null=True, default="")
    date_pattern = models.CharField(max_length=128, blank=True, null=True, default="")
    source_pattern = models.CharField(max_length=128, blank=True, null=True, default="")
    title_pattern = models.CharField(max_length=128, blank=True, null=True, default="")
    next_pattern = models.CharField(max_length=128, blank=True, null=True, default="")
    action_pattern = models.CharField(max_length=256, blank=True, null=True, default="")
    
    class Meta:
        unique_together = ('target_url', 'action_pattern')


class Status(models.Model):
    # 爬虫状态表
    config = models.OneToOneField("Config", on_delete=models.CASCADE)
    status = models.PositiveIntegerField(default=0)  # 0待定，1等待中, 2运行中, 3已完成, 4异常终止
    pages = models.PositiveIntegerField(default=0, verbose_name="翻页数")
    counts = models.PositiveIntegerField(default=0, verbose_name="文件总数")
    error_info = models.CharField(max_length=512, null=True, blank=True)


class Links(models.Model):
    # 子链接表
    loc = models.ForeignKey("Location", on_delete=models.CASCADE)
    config = models.ForeignKey("Config", null=True, blank=True, on_delete=models.SET_NULL)
    gov = models.CharField(max_length=10, db_index=True, default="人民政府")
    title = models.CharField(max_length=512, db_index=True)
    pub_date = models.DateTimeField(blank=True, null=True, db_index=True)
    rank = models.PositiveIntegerField(default=1, db_index=True)
    crawl_date = models.DateTimeField(auto_now_add=True)  # 创建时间
    sub_url = models.CharField(max_length=700, unique=True)  # 子链接
    zupei_type = models.CharField(max_length=128, null=True, blank=True, db_index=True, default="")
    source = models.CharField(max_length=128, null=True, blank=True, default="")
    
    class Meta:
        unique_together = ('loc', 'title')


class Details(models.Model):
    # 详细内容（正文部分）
    links = models.OneToOneField("Links", on_delete=models.CASCADE, related_name="details")
    main_text = models.TextField(null=True, blank=True)
    img = models.TextField(null=True, blank=True)
    attachment = models.TextField(null=True, blank=True)
    rank = models.PositiveIntegerField(default=1, db_index=True)
