from rest_framework import viewsets
from django.shortcuts import render
from django.http import HttpResponse
from runtime.apps.runtime.tasks import run
import logging


class PlaybookViewSet(viewsets.ModelViewSet):
  def run_playbook(self,request, *args, **kwargs):
    host=request.data.get("host")
    playbook=request.data.get("playbook")
    result = run.delay(playbook, host)
    return HttpResponse(result.id)
  def get_state(self,request,*args,**kwargs):
    taskid=request.data.get("taskid")
    result=run.AsyncResult(taskid)
    return HttpResponse(result.state)
