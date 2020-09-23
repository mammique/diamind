from django.shortcuts import render, redirect, get_object_or_404
from django.db import models
from django.forms import ModelForm
from django.contrib.auth.decorators import login_required

from core.models import Entry


def home(request):

    return render(request, 'core/home.html', {'entries': Entry.objects.filter(root=True).order_by('name')})


def nav(request, path):

    # print(path)

    path_entries = []
    entry        = None
    entry_pk     = int(request.GET.get('e', -1))

    path_current = '/nav/'
    for pk in path.split('/'):
        if pk != '':
            path_current = '%s%s/' % (path_current, pk)
            path_entry = get_object_or_404(Entry, pk=pk)
            path_entries.append({'entry': path_entry})
            if path_entry.pk == entry_pk: entry = path_entry

    for e in path_entries: e['path'] = '%s?e=%s' % (path_current, e['entry'].pk,)

    if not entry: entry = path_entries['entry'][-1]

    # entry = 
    # child =
    # children = 
    # child_children = 

    children = Entry.objects.filter(root=True).order_by('name')

    return render(request, 'core/nav.html', {'path_entries': path_entries, 'entry': entry,})


class EntryForm(ModelForm):

    name       = models.CharField(max_length=64)
    text       = models.TextField()
    file       = models.ImageField(upload_to='file', blank=True)
    url        = models.URLField(max_length=1024)
    root       = models.BooleanField(default=False)
    date       = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    children   = models.ManyToManyField('self', related_name="parents")
    tags       = models.ManyToManyField('self', related_name="tagged_from")

    class Meta:
        model  = Entry
        fields = ('name', 'text' ,'file', 'image', 'children', 'root',)


@login_required
def entry_create(request):

    form = EntryForm()

    if request.method == 'POST':

        form = EntryForm(request.POST, request.FILES)

        if form.is_valid():

            entry = form.save()

            # entry = form.save(commit=False)
            # entry.save()
            # entry.save_m2m()

    return render(request, 'core/entry_create.html', {'form': form, 'form_action': 'Create'})


@login_required
def entry_update(request, pk):

    entry = get_object_or_404(Entry, pk=pk)

    form = EntryForm(instance=entry)

    if request.method == 'POST':

        form = EntryForm(request.POST, request.FILES, instance=entry)

        if form.is_valid():

            entry = form.save()

            # entry = form.save(commit=False)
            # entry.save()
            # entry.save_m2m()

    return render(request, 'core/entry_create.html', {'form': form, 'form_action': 'Update'})