import re, os

from django.db import models
from django.utils.html import mark_safe
from django.template import Context as TemplateContext
from django.template import Template
from django.urls import reverse

from markdownx.models import MarkdownxField
from markdownx.utils import markdownify

from ordered_model.models import OrderedModel


class EntryParentThroughModel(OrderedModel):

    parent = models.ForeignKey('Entry', on_delete=models.CASCADE, related_name="children_through")
    child  = models.ForeignKey('Entry', on_delete=models.CASCADE, related_name="parents_through")

    order_with_respect_to = 'parent'

    def __str__(self):
        return 'Parent: %s (%s) - Child: %s (%s)' % \
            (self.parent.name_get_no_name_parent(), self.parent.pk, self.child.name_get_no_name_parent(), self.child.pk)


class Entry(models.Model):

    name        = models.CharField(max_length=64, blank=True)
    name_parent = models.ForeignKey('self', verbose_name="Parent name prefix",
                                    help_text="Use this parent's name as prefix when displayed out of context.",
                                    null=True, blank=True, on_delete=models.SET_NULL, related_name="children_using_name")
    text        = MarkdownxField(blank=True)
    file        = models.FileField(upload_to='file', blank=True)
    image       = models.ImageField(upload_to='image', blank=True)
    home        = models.BooleanField(default=False, help_text="Display entry in home page.")
    date        = models.DateTimeField(auto_now_add=True)
    updated_on  = models.DateTimeField(auto_now=True)
    parents     = models.ManyToManyField('self', related_name="children", symmetrical=False, blank=True, through='EntryParentThroughModel', through_fields=('child', 'parent'),)

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

    def span(self, name_parent=True):

        if self.image:
            img = """{% load responsive_images %}<img src="{% src entry.image 32x24 nocrop %}" />&nbsp;"""
        else:
            img = ''

        t = Template("""<span>%s{{ name }}</span>""" % img)

        return t.render(TemplateContext({'entry': self, 'name': self.name_get(name_parent=name_parent)}))

    def span_no_name_parent(self): return self.span(name_parent=False)

    def url_path(self): return reverse('nav', args=('%s/'%self.pk,))

    def name_get(self, name_parent=True):

        name_strip = self.name.strip()
        text_strip = self.text.strip()

        if name_strip != '': name = name_strip
        elif text_strip != '':
            name = text_strip[0:16]
            if len(name) != len(text_strip): name = '%s…' % name
        else: name = '∅'

        if name_parent and self.name_parent:
            name = '%s: %s' % (self.name_parent.name_get(), name,)

        return name

    def name_get_no_name_parent(self): return self.name_get(name_parent=False)

    def __str__(self): return self.name_get()

    class Meta:
        verbose_name_plural = "Entries"
        # ordering = ('parents_through__order', 'children_through__order',)