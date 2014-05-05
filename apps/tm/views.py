from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect, Http404

from wordrobot.sitetools.usertools import group_required


@group_required('text_metrics_viewer')
def homepage(request):
    """
    Home page
    """
    from .lib.documentlistmanager import DocumentListManager
    dm = DocumentListManager()
    params = {'randomdocs': dm.random_list(6), }
    return render(request, 'tm/home.html', params)


def display_canned(request, **kwargs):
    """
    Display results for a canned document
    """
    from .models import Document
    from .lib.scatterbuttons import scatter_buttons
    author = kwargs.get('author')
    title = kwargs.get('title')
    try:
        record = Document.objects.get(authorsort=author, titlesort=title)
    except Document.DoesNotExist:
        raise Http404()
    else:
        params = {'text': record.text, 'author': record.author,
                  'title': record.title, 'document_year': record.year,
                  'scatter_buttons': scatter_buttons(record.year),
                  'jsonlemmas': record.lemmas,
                  'jsontokens': record.tokens,
                  'include_save': False}
    return render(request, 'tm/viewresults.html', params)


def display_stored(request, **kwargs):
    """
    Display results for a stored user-submitted document
    """
    from .lib.textmanager import TextManager
    from .models import UserSubmission
    from .lib.scatterbuttons import scatter_buttons
    identifier = kwargs.get('identifier')
    try:
        record = UserSubmission.objects.get(identifier=identifier)
    except UserSubmission.DoesNotExist:
        raise Http404()
    else:
        tc = TextManager(record.text, record.year)
        json_lemmas = tc.lemmas_datastruct(formalism='json')
        json_tokens = tc.tokens_datastruct(formalism='json')
        params = {'text': record.text, 'author': record.author,
                  'title': record.title, 'document_year': record.year,
                  'scatter_buttons': scatter_buttons(record.year),
                  'jsonlemmas': json_lemmas,
                  'jsontokens': json_tokens,
                  'include_save': False}
    return render(request, 'tm/viewresults.html', params)


@group_required('text_metrics_viewer')
def list_canned(request):
    """
    Display sortable list of canned documents
    """
    from .lib.documentlistmanager import DocumentListManager
    dm = DocumentListManager()
    documents = dm.datastruct(formalism='json')
    params = {'documents': documents}
    return render(request, 'tm/listcanned.html', params)


def random_document(request):
    """
    Redirect to a random document from the canned library
    """
    from .lib.documentlistmanager import DocumentListManager
    dm = DocumentListManager()
    document = dm.random_document()
    return HttpResponseRedirect(document.get_absolute_url())


@group_required('text_metrics_viewer')
def submission_form(request):
    """
    Display the submission form in its own page
    """
    params = {}
    return render(request, 'tm/experiment.html', params)


def submit(request):
    """
    Process a text submitted by the user; return a page of results
    """
    from .lib.submissioncleaner import submission_cleaner
    from .lib.textmanager import TextManager
    from .lib.scatterbuttons import scatter_buttons
    if request.method == 'POST':
        post = submission_cleaner(request.POST.copy())
        tc = TextManager(post['text'], post['year'])
        json_lemmas = tc.lemmas_datastruct(formalism='json')
        json_tokens = tc.tokens_datastruct(formalism='json')
        params = {'text': tc.text, 'author': post['author'],
                  'title': post['title'], 'document_year': post['year'],
                  'scatter_buttons': scatter_buttons(post['year']),
                  'jsonlemmas': json_lemmas,
                  'jsontokens': json_tokens,
                  'include_save': True}
        return render(request, 'tm/viewresults.html', params)
    else:
        return redirect(homepage)


def save_text(request):
    """
    Save user-submitted text, and return permalink
    """
    from .lib.submissioncleaner import submission_cleaner
    from .lib.storeusersubmission import store_user_submission
    if request.method == 'POST':
        post = submission_cleaner(request.POST.copy())
        record = store_user_submission(post)
        return redirect(record.get_absolute_url() + '?notify')
    else:
        return redirect(homepage)


def fetch_definition(request, **kwargs):
    """
    Return the definition text from a given row in the Definition table
    (in response to AJAX requests)
    """
    import json
    from .models import Definition
    definition_id = int(kwargs.get('id'))
    try:
        definition = Definition.objects.get(id=definition_id).text
    except Definition.DoesNotExist:
        definition = '[definition not found]'
    response = json.dumps([definition, ])
    return HttpResponse(response, content_type='text/plain')


def fetch_thesaurus_alternatives(request, **kwargs):
    """
    Return the set of thesaurus instances corresponding to a given class ID
    (in response to AJAX requests)
    """
    import json
    from .htmodels import ThesaurusClass
    class_ids = [int(z) for z in kwargs.get('idstring').split(',')]
    records = []
    for class_id in class_ids:
        try:
            record = ThesaurusClass.objects.get(id=class_id)
        except ThesaurusClass.DoesNotExist:
            pass
        else:
            records.append(record.to_dict())
    response = json.dumps(records)
    return HttpResponse(response, content_type='text/plain')


def info(request, **kwargs):
    """
    Return a static info page (e.g. the help page)
    """
    page = kwargs.get('page', 'help')
    params = {}
    return render(request, 'tm/info/%s.html' % page, params)
