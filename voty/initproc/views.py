from django.shortcuts import render, get_object_or_404

from .models import Initiative
# Create your views here.

def index(request):
	return render(request, 'initproc/index.html')

def item(request, init_id):
	init = get_object_or_404(Initiative, pk=init_id)
	return render(request, 'initproc/item.html', context=dict(initiative=init))