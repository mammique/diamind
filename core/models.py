import re, os

from django.db import models
from django.utils.html import mark_safe
from django.template import Context as TemplateContext
from django.template import Template
from django.urls import reverse

from markdownx.models import MarkdownxField
from markdownx.utils import markdownify

from ordered_model.models import OrderedModel


class Entry(OrderedModel):

    name        = models.CharField(max_length=64, blank=True)
    name_parent = models.BooleanField(default=False, help_text="Use parent's name as prefix (if only one parent).")
    text        = MarkdownxField(blank=True)
    file        = models.FileField(upload_to='file', blank=True)
    image       = models.ImageField(upload_to='image', blank=True)
    root        = models.BooleanField(default=False)
    date        = models.DateTimeField(auto_now_add=True)
    updated_on  = models.DateTimeField(auto_now=True)
    parents     = models.ManyToManyField('self', related_name="children", symmetrical=False, blank=True)

    order_with_respect_to = 'pk'

    def file_ext(self):
        if self.file: return self.file.name.split('.')[-1].lower()

    def file_is_video(self):
        return self.file_ext() in ('mp4', 'ogg', 'webm',)

    def file_filename(self):
        return os.path.basename(self.file.name)

    def text_html(self): return mark_safe(markdownify(self.text))

    def badge(self):
        t = Template("""<a class="badge badge-secondary entry" href="%s">%s</a>""" % (self.url_path(), self.span()))
        return t.render(TemplateContext({'entry': self}))

    def span(self):

        if self.image:
            img = """{% load responsive_images %}<img src="{% src entry.image 32x24 nocrop %}" />&nbsp;"""
        else:
            img = ''

        t = Template("""<span>%s{{ entry }}</span>""" % img)
        return t.render(TemplateContext({'entry': self}))

    def url_path(self):
        return reverse('nav', args=('%s/'%self.pk,))
        
    def __str__(self): return self.name

    class Meta(OrderedModel.Meta):
        verbose_name_plural   = "Entries"