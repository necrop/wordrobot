from django.shortcuts import render


def homepage(request):
    """
    Home page
    """
    params = {}
    return render(request, 'root/home.html', params)
