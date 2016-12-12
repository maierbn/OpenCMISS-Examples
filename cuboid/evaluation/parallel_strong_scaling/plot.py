#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import numpy as np
import matplotlib.pyplot as plt
import csv
import collections
import copy
from sets import Set

# load format package
SCENARIO='cuboid'
#sys.path.insert(0, src_path+"/evaluation")
import format as fo

# determine if plots are shown
show_plots = True
if len(sys.argv) >= 2:
  show_plots = False
  
remove_outlier = False
outlier_top = 1
outlier_bottom = 1
  
# read csv file
report_filename = "duration.00000.csv"
report_filename = "duration_strong_scaling.csv"
report_filename = "duration_strong_scaling2.csv"
print "report file: {}".format(report_filename)
data = []
with open(report_filename) as csvfile:
  reader = csv.reader(csvfile, delimiter=';')
  for row in reader:
    if len(row) > 0:
      if '#' not in row[0]:
        data.append(row)

n = len(data)

def getCol(colno):
  cols = []
  for i in range(len(data)):
    cols.append(data[i][colno])
  return cols  
  
def isfloat(value):
  try:
    float(value)
    return True
  except ValueError:
    return False
    
def isint(value):
  try:
    int(value)
    return True
  except ValueError:
    return False
    
# 0  Stamp
# 1  Host
# 2  NProc
# 3  X
# 4  Y
# 5  Z
# 6  F
# 7  Total FE
# 8  Total M
# 9  End Time
# 10 Dur. Init
# 11 Stretch Sim
# 12 Int. Init
# 13 Main Sim
# 14 Total
# 15 Total (User)
# 16 Total (System)
# 17 ODE
# 18 Parabolic
# 19 FE
# 20 FE before Main Sim
# 21 memory consumption after simulation
# 22 memory consumption at shutdown

max_index = 22
int_indices = [2, 3, 4, 5, 6, 7, 8, 9, 21, 22]
float_indices = [10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]

def extract_data(data):

  datasets = dict()
  
  # extract lines
  n = 0
  for dataset in data:
    
    if len(dataset) < 17:
      print "Warning: invalid data set"
      continue
    
    # copy dataset to new_data
    new_data = dataset
    
    # fill dataset to size of max_index
    if len(dataset) < max_index+1:
      new_data += (max_index+1-len(dataset)) * [0]
      
    # extract some values
    for index in int_indices:
      new_data[index] = int(new_data[index])     if isint(new_data[index])    else 0
    for index in float_indices:
      new_data[index] = float(new_data[index])     if isfloat(new_data[index])    else 0.0
      
    # define sorting key
    key = "{:03d}".format(new_data[2])
      
      
    # store extracted values
    if key not in datasets:
      datasets[key] = dict()
      datasets[key]["value"] = []
    
    datasets[key]['value'].append(new_data)
    n += 1
    
  # compute mean value
  for key in datasets:
    
    result = copy.copy(datasets[key]['value'][0])
    variances = copy.copy(datasets[key]['value'][0])
    result += [0]
    
    for i in int_indices + float_indices:
      
      # reduce values
      result[i] = 0
      value_list = []
      for j in range(len(datasets[key]['value'])):
        value = datasets[key]['value'][j][i]
        
        if value != 0:
          value_list.append(value)
      
      # remove outlier
      value_list = sorted(value_list)
      n = len(value_list)
      
      #print "i={}, value_list for {}: {}".format(i, key, value_list)
      
      if n > outlier_bottom+outlier_top and remove_outlier:
        value_list = value_list[outlier_bottom:-outlier_top]
        
      # compute mean and standard deviation
      result[i] = np.mean(value_list)
      variances[i] = np.std(value_list)
      #print "mean: {}, std: {}".format(result[i], variances[i])
        
    result[max_index+1] = len(datasets[key]["value"])
        
    datasets[key]['value'] = result
    datasets[key]['variance'] = variances
    
  datasets = collections.OrderedDict(sorted(datasets.items()))
    
  return datasets
  
datasets = extract_data(data)

###############################################################
# output to console
print ""
print "------------- duration -------------------------------------------"
print "{:10}, {:6},  {:6}, {:10}, {:10}, {:10}, {:10}".\
format("key", "F", "#M", "init", "stretch", "init", "main")
for key in datasets:
  
  print "{:10}, {:6}, {:6}, {:10}, {:10}, {:10}, {:10}".\
  format(key, datasets[key]["value"][6], datasets[key]["value"][8], 
  fo.str_format_seconds(datasets[key]["value"][10]), 
  fo.str_format_seconds(datasets[key]["value"][11]), 
  fo.str_format_seconds(datasets[key]["value"][12]), 
  fo.str_format_seconds(datasets[key]["value"][13]))
print ""
print ""
  
print "{:10}, {:6}, {:6}, {:10}, {:10}, {:10}, {:10}".\
format("key", "F", "#M", "ODE", "Parabolic", "FE", "pre FE")
for key in datasets:
  
  print "{:10}, {:6}, {:6}, {:10}, {:10}, {:10}, {:10}".\
  format(key, datasets[key]["value"][6], datasets[key]["value"][8], 
  fo.str_format_seconds(datasets[key]["value"][17]), 
  fo.str_format_seconds(datasets[key]["value"][18]), 
  fo.str_format_seconds(datasets[key]["value"][19]), 
  fo.str_format_seconds(datasets[key]["value"][20]))

print ""
print "------------- memory consumption -------------------------------------------"
print "{:10}, {:6}, {:6}, {:10}, {:10}".\
format("key", "F", "#M", "mem", "mem end")
for key in datasets:
  
  print "{:10}, {:6}, {:6}, {:10}, {:10}".\
  format(key, datasets[key]["value"][6], datasets[key]["value"][8], 
  fo.str_format_memory(datasets[key]["value"][21]),
  fo.str_format_memory(datasets[key]["value"][22]))
###############################################################
#######################################################
# plot
# x-axis: nproc
# y-axis: total time

plt.rcParams.update({'font.size': 16})
plt.rcParams['lines.linewidth'] = 2
output_path = ""
plotdata = dict()
xdata = Set()
plotkeys = Set()

for key in datasets:
  
  dataset = datasets[key]['value']
  variances = datasets[key]['variance']
  nproc = dataset[2]
  main_sim = dataset[13]
  
  plotkey = 0
  if plotkey not in plotdata:
    plotdata[plotkey] = dict()
    plotdata[plotkey]['value'] = collections.OrderedDict()
    plotdata[plotkey]['variance'] = collections.OrderedDict()
    
  xvalue = nproc
  yvalue = main_sim
  yvalue_variance = variances[13]
    
  plotdata[plotkey]['value'][xvalue] = yvalue
  plotdata[plotkey]['variance'][xvalue] = yvalue_variance
  xdata.add(xvalue)
  plotkeys.add(plotkey)
  
xlist = list(xdata)

######################
# plot strong scaling
plt.figure(2, figsize=(10,8))

colors = {
  0 : "ko-",
  1 : "go-",
  2 : "bo-",
}
labels = {
  0 : "Duration main simulation",
  1 : "Speedup",
  2 : "Parallel Efficiency"
}

for plotkey in plotkeys:
  
  xlist = list(plotdata[plotkey]["value"])
  ylist = [y for y in plotdata[plotkey]["value"].values()]
  yerr = [y for y in plotdata[plotkey]['variance'].values()]
  
  p0 = plt.errorbar(xlist, ylist, fmt=colors[plotkey], yerr=yerr, label=labels[plotkey])
  
ylist2 = [(plotdata[plotkey]["value"].values()[0]/y) for y in plotdata[plotkey]["value"].values()]
ylist3 = [(y/x)*100.0 for (x,y) in zip(xlist,ylist2)]


plt.xscale('log', basex=2)
plt.xlabel('number of processes')

ax = plt.gca()
#ax.set_yscale('log', basey=10) 
ax.set_xticks([1,2,4,8,16,32,64])
ax.set_xticklabels([1,2,4,8,16,32,64])
plt.ylabel('duration (s)')



# parallel efficiency
ax1 = ax.twinx()
color = (0.0, 0.5, 0.0)
ax1.set_ylabel(u'Parallele Effizienz (%)', color=color)
ax1.set_ylim([0,103.0])
for tl in ax1.get_yticklabels():
    tl.set_color(color)

p1, = plt.plot(xlist, ylist3, color=color, marker='o', label="\n\nParallel Efficiency")


# speedup
ax2 = ax.twinx()
color = (0.6, 0.6, 0.0)
ax2.set_ylabel(u'Speedup', color=color)
#ax2.set_ylim([0,3.5])
for tl in ax2.get_yticklabels():
    tl.set_color(color)
    
p2, = plt.plot(xlist, ylist2, color=color, marker='o', label="Speedup")
  
  
plt.title(u'Strong scaling, cuboid muscle, $8^3$ FE, neon')
plt.xlabel('Number of processes')
plt.legend([p0, p2, p1], [labels[0], labels[1], labels[2]], loc='center right')
plt.grid(which='both')
plt.tight_layout()
plt.savefig(output_path+SCENARIO+'_strong_scaling.png')

######################
# plot memory scaling
plt.figure(3, figsize=(10,8))

plotdata = dict()
xdata = Set()
plotkeys = Set()

for key in datasets:
  
  dataset = datasets[key]['value']
  variances = datasets[key]['variance']
  nproc = dataset[2]
  main_sim = dataset[13]
  
  plotkey = 0
  if plotkey not in plotdata:
    plotdata[plotkey] = dict()
    plotdata[plotkey]['value'] = collections.OrderedDict()
    plotdata[plotkey]['variance'] = collections.OrderedDict()
    
  xvalue = nproc
  yvalue = dataset[21]
  yvalue_variance = variances[21]
    
  plotdata[plotkey]['value'][xvalue] = yvalue
  plotdata[plotkey]['variance'][xvalue] = yvalue_variance
  xdata.add(xvalue)
  plotkeys.add(plotkey)

colors = {
  0 : "ko-",
  1 : "go-"
}
labels = {
  0 : "Memory per process",
  1 : "total memory / serial memory"
}

for plotkey in plotkeys:
  
  xlist = list(plotdata[plotkey]["value"])
  ylist = [y/1024./1024./1024. for y in plotdata[plotkey]["value"].values()]
  yerr = [y/1024./1024./1024. for y in plotdata[plotkey]['variance'].values()]

  p0 = plt.errorbar(xlist, ylist, fmt=colors[plotkey], yerr=yerr, label=labels[plotkey])
  
serial_value = plotdata[plotkey]["value"].values()[0]
ylist2 = [(x*y/serial_value) for (x,y) in zip(xlist,plotdata[plotkey]["value"].values())]

plt.xscale('log', basex=2)
plt.xlabel('number of processes')

ax = plt.gca()
#ax.set_yscale('log', basey=10) 
ax.set_xticks([1,2,4,8,16,32,64])
ax.set_xticklabels([1,2,4,8,16,32,64])
plt.ylabel('memory consumption (GiB)')



# total memory / serial memory
ax1 = ax.twinx()
color = (0.0, 0.5, 0.0)
ax1.set_ylabel(u'Relative total memory (factor)', color=color)
#ax1.set_ylim([0,110.0])
for tl in ax1.get_yticklabels():
    tl.set_color(color)

p1, = plt.plot(xlist, ylist2, color=color, marker='o')

  
plt.title(u'Memory consumption, cuboid muscle, $8^3$ FE, neon')
plt.xlabel('Number of processes')
plt.legend([p0, p1], [labels[0], labels[1]], loc='center right')
plt.grid(which='both')
plt.tight_layout()
plt.savefig(output_path+SCENARIO+'_strong_scaling.png')

if show_plots:
  plt.show()
#quit()
