from django.shortcuts import render, get_object_or_404

from .models import Initiative
# Create your views here.

def index(request):
	inits = Initiative.objects.all()
	return render(request, 'initproc/index.html', context=dict(initiatives=inits))

def item(request, init_id):
	init = get_object_or_404(Initiative, pk=init_id)
	return render(request, 'initproc/item.html', context=dict(initiative=init))