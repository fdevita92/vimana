from django.shortcuts import render,get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse,HttpResponseRedirect,Http404

from .test_api import api_call
import numpy as np
import requests
from PIL import Image
import struct
import json
import time
import csv

from keras.preprocessing import image
from keras.applications.vgg16 import preprocess_input

from shutil import move, copyfile
import os

from .models import MLModel
from .forms import MLModelForm


def encode(input_value, output):
    return struct.pack('l%sf' %input_value.size,output, *input_value.flatten('F'))

def main(request,id=None):
    mlmodel = MLModel.objects.all()
    active = MLModel.objects.filter(active=True)
    print(active)
    context={
        "model": mlmodel,
        "active": active,
    }
    return render(request,"main.html",context)

def model_create(request):
	form = MLModelForm(request.POST or None , request.FILES)
	if form.is_valid():
		instance=form.save(commit=False)
		instance.save()
		return HttpResponseRedirect("/")
	context={
    "form":form,
    }
	return render(request,"form.html",context)

def update_active(request, id=None):
    
    active = MLModel.objects.filter(active=True)
    for node in active:
        node.active = False
        node.save(update_fields=["active"])

    instance = get_object_or_404(MLModel,id=id)
    instance.active = True
    instance.save(update_fields=["active"])

    
    path = os.path.relpath(instance.file.path)
    copyfile(path, 'tendermint/model.h5')
    return HttpResponseRedirect("/")

def write_to_csv(time_list):
    with open("mnist_with_tendermint.csv", 'w') as myfile:
        wr = csv.writer(myfile, quoting=csv.QUOTE_ALL)
        wr.writerow(time_list)

def test(request):
    input_file  = request.POST.get('file')
    print("--- INPUT FILE ----")
    print(input_file)
    time_taken = []
    for i in range(1,2):
        start_time = time.time()
        result = api_call(input_file)
        end_time = time.time()
        print(end_time-start_time)
        time_taken.append(end_time-start_time)
    
    
    print("--------RESULT-------------")
    print(result)

    print("Average time taken")
    print(sum(time_taken)/float(len(time_taken)))
    
    print("Writing to CSV")
    write_to_csv(time_taken)
    
    return HttpResponse(result)

def commit(request):
    input_file = request.POST.get('file')

    file_name = input_file

    # time_taken = []
    # for i in range(1,2):
    # start_time = time.time()
        
    img_path = "data/"+file_name

    img = image.load_img(img_path, target_size=(224, 224))
    x = image.img_to_array(img)
    x = np.expand_dims(x, axis=0)
    x = preprocess_input(x)

    output = api_call(file_name)

    raw = encode(x,output)
    raw_hex = raw.hex()

    print("WORKS UPTO HERE")
    json_response = requests.get('http://localhost:26657/broadcast_tx_commit?tx=0x'+raw_hex, stream= True)
    # end_time = time.time()
    # print(end_time-start_time)
    # time_taken.append(end_time-start_time)

    # print("Average time taken")
    # print(sum(time_taken)/float(len(time_taken)))
    
    # print("Writing to CSV")
    # write_to_csv(time_taken)
    
    print(json_response)
    return HttpResponse()
