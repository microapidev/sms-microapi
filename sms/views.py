from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

# Create your views here.
@csrf_exempt
def index(request):
    if request.method == 'POST':
        pass
        return JsonResponse({"success":"We'd soon be ready"})
    return render(request, "index.html")


@csrf_exempt
def bulk(request):
    if request.method == 'POST':
        pass
        return JsonResponse({"success":"We'd soon be ready"})
    return render(request, "bulk.html")

def check_status(request):
    return 0

def translate_message(request):
    return 0