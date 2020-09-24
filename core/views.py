from django.shortcuts import render, redirect, get_object_or_404
from django.db import models
from django.forms import ModelForm
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.contrib import messages
from django.utils.html import mark_safe

from core.models import Entry


def home(request):

    return render(request, 'core/home.html', {'entries': Entry.objects.filter(root=True).order_by('name')})


def nav(request, path):

    # print(request.PATH)

    path_entries = []
    entry        = None
    entry_pk     = int(request.GET.get('e', -1))
    child        = None
    child_pk     = int(request.GET.get('c', -1))

    path_current = '/nav/'
    path_e       = None

    for pk in path.split('/'):

        if pk != '':

            path_current = '%s%s/' % (path_current, pk)
            path_entry   = Entry.objects.filter(pk=pk).last()

            if not path_entry: continue

            path_entries.append({'entry': path_entry, 'path': path_current})

            if path_entry.pk == entry_pk:

                entry  = path_entry
                path_e = path_current

            elif path_entry.pk == child_pk: child = path_entry

    path_clean = path_current

    if not entry:  entry  = path_entries[-1]['entry']
    if not path_e: path_e = path_entries[-1]['path']
    if not child:  child  = entry

    parent          = None
    previous_parent = None
    for e in path_entries:
        if e['entry'] == child: parent = previous_parent
        e['path'] = '%s?e=%s' % (path_clean, e['entry'].pk,)
        previous_parent = e['entry']

    children = Entry.objects.filter(root=True).order_by('name')

    return render(request, 'core/nav.html', {'path_entries': path_entries,
                                             'path_clean':   path_clean,
                                             'path_entry':   path_e,
                                             'entry':        entry,
                                             'child':        child,
                                             'parent':       parent,
                                            })


class EntryForm(ModelForm):

    class Meta:
        model  = Entry
        fields = ('name', 'name_parent', 'text' ,'file', 'image', 'parents', 'root',)


@login_required
def entry_create(request):

    nxt = request.GET.get('next', None)
    if not nxt: nxt = request.POST.get('next', None)

    if 'parent' in request.GET: initial = {'parents': [get_object_or_404(Entry, pk=request.GET.get('parent'))]}
    else: initial = {}

    form = EntryForm(initial=initial)

    if request.method == 'POST':

        form = EntryForm(request.POST, request.FILES)

        if form.is_valid():

            entry = form.save()
            if entry.parents.all().count(): return redirect('%s&c=%s' % (nxt, entry.pk,))

    return render(request, 'core/entry_create.html', {'form': form, 'form_action': 'Create', 'next': nxt})


@login_required
def entry_update(request, pk):

    nxt = request.GET.get('next', None)
    if not nxt: nxt = request.POST.get('next', None)

    entry = get_object_or_404(Entry, pk=pk)

    form = EntryForm(instance=entry)

    if request.method == 'POST':

        form = EntryForm(request.POST, request.FILES, instance=entry)

        if form.is_valid():

            entry = form.save()

            if nxt: return redirect(nxt)

    return render(request, 'core/entry_create.html', {'form': form, 'form_action': 'Update'})


@login_required
def entry_delete(request, pk): # FIXME: CSRF

    nxt   = request.GET.get('next', None)
    entry = get_object_or_404(Entry, pk=pk)

    entry.delete()

    messages.success(request, mark_safe('"%s" successfully deleted.' % entry))

    if nxt: return redirect(nxt)
    else:   return redirect(reverse('home'))

    return render(request, 'core/entry_create.html', {'form': form, 'form_action': 'Update'})