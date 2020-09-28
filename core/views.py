from django.shortcuts import render, redirect, get_object_or_404
from django.db import models
from django.forms import ModelForm, ModelChoiceField, BooleanField, ModelMultipleChoiceField
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.contrib import messages
from django.utils.html import mark_safe

from dal import autocomplete

from core.models import EntryParentThroughModel, Entry


def home(request):

    q = request.GET.get('q')
    search_results = None

    if q:

        ea = EntryAutocomplete()
        ea.q = q
        search_results = ea.get_queryset()

    return render(request, 'core/home.html', {'home_entries':   Entry.objects.filter(home=True).order_by('name'),
                                              'latest_entries': Entry.objects.all().distinct().order_by('-updated_on')[0:12],
                                              'search_results': search_results})


def nav(request, path):

    path_entries = []
    entries_raw  = []
    entry        = None
    entry_pk     = int(request.GET.get('e', -1))
    child        = None
    child_pk     = int(request.GET.get('c', -1))

    path_current = ''
    path_e       = None

    for pk in path.split('/'):

        if pk != '':

            path_prev_len = len(path_current)

            path_current = '%s%s/' % (path_current, pk)
            path_entry   = Entry.objects.filter(pk=pk).last()

            if not path_entry: continue

            if path_entry.name_prefix and path_entry.name_prefix in entries_raw:
                span = path_entry.span_no_name_prefix()
            else: span = path_entry.span()

            path_entries.append({'entry': path_entry, 'span': span, 'path': path_current, 'path_prev_len': path_prev_len})
            entries_raw.append(path_entry)

            if path_entry.pk == entry_pk:

                entry  = path_entry
                path_e = path_current

            elif path_entry.pk == child_pk: child = path_entry

    if not entry:  entry  = path_entries[-1]['entry']
    if not path_e: path_e = path_entries[-1]['path']
    if not child:  child  = entry

    path_e     = reverse('nav', kwargs={'path': path_e})
    path_clean = reverse('nav', kwargs={'path': path_current})

    child_parent    = None
    entry_parent    = None
    previous_parent = None
    entry_root_path = None
    child_root_path = None

    for e in path_entries:

        if e['entry'] == entry:
            entry_parent = previous_parent
            entry_root_path = path_current[e['path_prev_len']:]

        elif e['entry'] == child:
            child_parent = previous_parent
            child_root_path = path_current[e['path_prev_len']:]

        if e['entry'] not in (entry, child,) and previous_parent:
            e['path'] = '%s?e=%s&c=%s' % (path_clean, previous_parent.pk, e['entry'].pk,)
        else:
            e['path'] = '%s?e=%s' % (path_clean, e['entry'].pk,)

        previous_parent = e['entry']


    entry_parents = []
    if entry_parent: entry_parents_exclude = {'pk': entry_parent.pk}
    else: entry_parents_exclude = {}
    # entry_parents_exclude = {}

    for p in entry.parents.exclude(**entry_parents_exclude).order_by('name'):
        entry_parents.append({'entry': p, 'path': reverse('nav', kwargs={'path': '%s/%s' % (p.pk, entry_root_path,)}) + '?e=%s&c=%s' % (p.pk, entry.pk,)})

    child_parents = []
    if child_parent: child_parents_exclude = {'pk': child_parent.pk}
    else: child_parents_exclude = {}
    # child_parents_exclude = {}

    for p in child.parents.exclude(**child_parents_exclude).order_by('name'):
        child_parents.append({'entry': p, 'path': reverse('nav', kwargs={'path': '%s/%s' % (p.pk, child_root_path,)}) + '?e=%s&c=%s' % (p.pk, entry.pk,)})

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

    return render(request, template, {'path_entries':      path_entries,
                                      'path_clean':        path_clean,
                                      'path_entry':        path_e,
                                      'entry':             entry,
                                      'entry_children':    entry_children,
                                      'child':             child,
                                      'child_children':    child_children,
                                      'entry_parent':      entry_parent,
                                      'child_parent':      child_parent,
                                      'entry_parents':     entry_parents,
                                      'entry_tags':        entry.tags.all().order_by('name'),
                                      'entry_tagged_from': entry.tagged_from.all().order_by('name'),
                                      'child_parents':     child_parents,
                                      'child_tags':        child.tags.all().order_by('name'),
                                      'child_tagged_from': child.tagged_from.all().order_by('name'),
                                     })


class EntryForm(ModelForm):

    children = ModelMultipleChoiceField(
                queryset=Entry.objects.all(),
                required=False,
                widget=autocomplete.ModelSelect2Multiple(
                    'entry_autocomplete', attrs={'data-html': True},
            ))

    def __init__(self,*args,**kwargs):

        super().__init__(*args,**kwargs)

        instance = getattr(self, 'instance', None)

        if instance and instance.pk:
            name_prefix_qs = instance.parents.all() | instance.tags.all()
            self.fields['children'].initial = instance.children.all()
        else: name_prefix_qs = Entry.objects.none()

        self.fields['name_prefix'].queryset = name_prefix_qs.distinct()

    class Meta:

        model   = Entry
        fields  = ('name', 'name_prefix', 'aka', 'text' ,'file', 'image', 'parents', 'children', 'tags', 'home',)
        widgets = {
            'parents': autocomplete.ModelSelect2Multiple('entry_autocomplete', attrs={'data-html': True}),
            'tags':    autocomplete.ModelSelect2Multiple('entry_autocomplete', attrs={'data-html': True}),
        }


class EntryParentForm(ModelForm):

    name_prefix_bool = BooleanField(required=False, label="Entry name prefix",
                                    help_text="Use parent/tag entry's name as prefix when displayed out of context.")

    class Meta:

        model  = Entry
        fields = ('name', 'name_prefix_bool', 'aka', 'text' ,'file', 'image', 'home',)


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
                qs_parents_aka  = qs.filter(parents__aka__icontains=kw)
                qs_name         = qs.filter(name__icontains=kw)
                qs_aka          = qs.filter(aka__icontains=kw)
                qs_text         = qs.filter(text__icontains=kw)
                qs_file         = qs.filter(file__icontains=kw)
                qs_image        = qs.filter(image__icontains=kw)

                if qs_kw == None: qs_kw = qs_parents_name | qs_parents_aka | qs_name | qs_aka | qs_text | qs_file | qs_image
                else: qs_kw = qs_kw & (qs_parents_name | qs_parents_aka | qs_name | qs_aka | qs_text | qs_file | qs_image)

            if qs_kw != None: qs = qs_kw

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

            if 'name_prefix_bool' in request.POST:

                entry.name_prefix = parent
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

            diff_add = form.cleaned_data['children'].difference(entry.children.all())
            diff_rm   = entry.children.all().difference(form.cleaned_data['children'])

            if diff_add.count(): entry.children.add(*diff_add)
            if diff_rm.count():  entry.children.remove(*diff_rm)

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
