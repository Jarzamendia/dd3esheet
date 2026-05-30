from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.views.decorators.http import require_GET


def home(request):
    if request.user.is_authenticated:
        return redirect('character:home')
    return render(request, 'home/landing.html')


@require_GET
def health(request):
    return JsonResponse({'ok': True})
