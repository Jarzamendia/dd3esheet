from django.shortcuts import render, redirect


def home(request):
    if request.user.is_authenticated:
        return redirect('character:home')
    return render(request, 'home/landing.html')
