from django.shortcuts import render, redirect, get_object_or_404
from django.db import models
from django.forms import ModelForm, ModelChoiceField, BooleanField
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.contrib import messages
from django.utils.html import mark_safe

from dal import autocomplete

from core.models import EntryParentThroughModel, Entry


def home(request):

    return render(request, 'core/home.html', {'home_entries':   Entry.objects.filter(home=True).order_by('name'),
                                              'latest_entries': Entry.objects.all().distinct().order_by('-updated_on')[0:12]})


def nav(request, path):

    path_entries = []
    entries_raw  = []
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

            if path_entry.name_parent and path_entry.name_parent in entries_raw:
                span = path_entry.span_no_name_parent()
            else: span = path_entry.span()

            path_entries.append({'entry': path_entry, 'path': path_current, 'span': span})
            entries_raw.append(path_entry)

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

    if 'children_position' in request.GET:

        instance_1 = entry.children.get(pk=request.GET['children_position'].split('_')[0])
        instance_1_through = EntryParentThroughModel.objects.get(parent=entry, child=instance_1)

        if request.GET['children_position'].endswith('top'):
            instance_1_through.top()

        else:
            instance_2 = entry.children.get(pk=request.GET['children_position'].split('_')[2])
            instance_2_through = EntryParentThroughModel.objects.get(parent=entry, child=instance_2)
            instance_1_through.below(instance_2_through)

    if 'children' in request.GET: template = 'core/nav_children.html'
    else: template = 'core/nav.html'

    entry_children = []
    for e in entry.children.all().order_by('parents_through__order', 'children_through__order',): # Quick fix for OrderedModel .distinct() fail.
        if not e in entry_children: entry_children.append(e)

    child_children = []
    for e in child.children.all().order_by('parents_through__order', 'children_through__order',): # Quick fix for OrderedModel .distinct() fail.
        if not e in child_children: child_children.append(e)

    return render(request, template, {'path_entries':   path_entries,
                                      'path_clean':     path_clean,
                                      'path_entry':     path_e,
                                      'entry':          entry,
                                      'entry_children': entry_children,
                                      'child':          child,
                                      'child_children': child_children,
                                      'parent':         parent,
                                     })


class EntryForm(ModelForm):

    def __init__(self,*args,**kwargs):

        super().__init__(*args,**kwargs)

        instance = getattr(self, 'instance', None)

        if instance and instance.pk: name_parent_qs = instance.parents
        else: name_parent_qs = Entry.objects.none()

        self.fields['name_parent'].queryset = name_parent_qs

    class Meta:

        model   = Entry
        fields  = ('name', 'name_parent', 'text' ,'file', 'image', 'parents', 'home',)
        widgets = {
            'parents': autocomplete.ModelSelect2Multiple(
                'entry_autocomplete', attrs={'data-html': True},
            )
        }


class EntryParentForm(ModelForm):

    name_parent_bool = BooleanField(required=False, label="Parent name prefix",
                                    help_text="Use parent's name as prefix when displayed out of context.")

    class Meta:

        model  = Entry
        fields = ('name', 'name_parent_bool', 'text' ,'file', 'image', 'home',)


class EntryAutocomplete(autocomplete.Select2QuerySetView):

    def get_result_label(self, entry):
        return entry.span()

    def get_queryset(self):

        qs = Entry.objects.all().order_by('name')

        if self.q:

            qs_kw = None

            for kw in self.q.split(' '):

                if kw == '': continue            

                qs_parents_name = qs.filter(parents__name__icontains=kw)
                qs_name         = qs.filter(name__icontains=kw)
                qs_text         = qs.filter(text__icontains=kw)
                qs_file         = qs.filter(file__icontains=kw)
                qs_image        = qs.filter(image__icontains=kw)

                if qs_kw == None: qs_kw = qs_parents_name | qs_name | qs_text | qs_file | qs_image
                else: qs_kw = qs_kw & (qs_name | qs_text | qs_file | qs_image)

            if qs_kw: qs = qs_kw

        return qs.distinct()


@login_required
def entry_create(request):

    nxt = request.GET.get('next', None)
    if not nxt: nxt = request.POST.get('next', None)

    initial = {}

    parent = Entry.objects.filter(pk=request.GET.get('parent')).last()
    if parent == None: parent = Entry.objects.filter(pk=request.POST.get('parent')).last()

    if 'home' in request.GET: initial['home'] = True

    if parent: form = EntryParentForm(initial=initial)
    else:      form = EntryForm(initial=initial)

    if request.method == 'POST':

        if parent: form = EntryParentForm(request.POST, request.FILES)
        else:      form = EntryForm(request.POST, request.FILES)

        if form.is_valid():

            entry = form.save()

            if parent: entry.parents.add(parent)

            if 'name_parent_bool' in request.POST:

                entry.name_parent = parent
                entry.save()

            if parent and nxt != None:
                return redirect('%s%s/?e=%s&c=%s' % (nxt, entry.pk, parent.pk, entry.pk,))
            else:
                return redirect(reverse('nav', kwargs={'path': entry.pk}))

    return render(request, 'core/entry_create.html', {'form': form, 'form_action': 'Create', 'next': nxt, 'parent': parent})


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

    return render(request, 'core/entry_create.html', {'form': form, 'form_action': 'Update', 'next': nxt})


@login_required
def entry_delete(request, pk): # FIXME: CSRF

    nxt   = request.GET.get('next', None)
    entry = get_object_or_404(Entry, pk=pk)

    entry.delete()

    messages.success(request, mark_safe('"%s" successfully deleted.' % entry))

    if nxt: return redirect(nxt)

    return redirect(reverse('home'))
