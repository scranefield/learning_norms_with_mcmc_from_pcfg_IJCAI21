# -*- coding: utf-8 -*-
"""
Created on Mon Jun 10 13:38:10 2019

@author: dhias426
"""
from rules_3 import *
from copy import deepcopy
import matplotlib.pyplot as plt
import numpy as np

def to_tuple(expression):
    """ Convert nested list to nested tuple """
    my_tup=tuple()
    for elem in expression:
        if type(elem)!=list:
            my_tup=my_tup+tuple([elem])
        else:
            my_tup=my_tup+tuple([to_tuple(elem)])
    return (my_tup)


def random_task_func(env,num_actionable,c1,s1):
    """ Genearte random task on environment """
    #num_actionable deifnes the number of objects in the target_area
    from robot_task_new import task,robot
    from environment import position
    from random import uniform
    while(True):
        (a,b)=(uniform(-1,1),uniform(-1,1))
        (c,d)=(uniform(a,1),uniform(b,1))
        target_area=[position(a,b),position(c,d)]
        task1=task(colour_specific=c1,shape_specific=s1,target_area=target_area)
        actionable=len(robot(task1,deepcopy(env)).all_actionable())
        if actionable>0:
            if np.isnan(num_actionable):
                break
            elif num_actionable==actionable:
                break
    return (task1)

def create_data(expression,env,name,task1=np.nan,random_task=False,limit_task_scope=False,
	num_actionable=np.nan,num_repeat=500,verbose=True):
    """ Function to create data from either given task or randomised tasks """
    print ("Generating action-profile data for case {}".format(name))
    from robot_task_new import robot,plot_task
    from algorithm_1_v4 import random_task_func
    from tqdm import tnrange, tqdm_notebook
    from time import sleep
    import os,glob,random
    import numpy as np
    action_profile={}
    #Empty the required directories
    for folder in ["action_profiles","env_states"]:
        for f in glob.glob("./{}/{}/*".format(name,folder)):
            os.chmod(f, 0o777)
            os.remove(f)
    for itr in tnrange(num_repeat,desc="Repetition of Task"):
        sleep(0.01)
        env_copy=deepcopy(env)
        fig,ax=plt.subplots(1, 2, sharex=True, sharey=True,figsize=(14,10))
        #Generate random task with actionable objects specified (random if specidied np.nan)
        if random_task==True:
        	if limit_task_scope==True:
        		c=random.choice(env[1])
        		s=random.choice(env[2])
        	else:
        		c=np.nan
        		s=np.nan
        	task1=random_task_func(env,num_actionable,c,s)
        plot_task(env_copy,ax[0],"Before clearing ({})".format(name),task1,True)
        if verbose==True:
            print ("For repetition={} of task".format(itr+1))
        action_profile[itr+1]=robot(task1,env_copy).perform_task(expression,"./{}/action_profiles/itr_{}".format(name,itr+1),verbose);
        plot_task(env_copy,ax[1],"After clearing ({})".format(name),task1,True)
        plt.savefig("./{}/env_states/itr_{}.jpeg".format(name,itr+1))
        plt.close()
    return (action_profile)

def algorithm_1(data,env,task1,expression,q_dict,rule_dict,filename="mcmc_reort",sim_threshold=0,similarity_penalty=1,relevance_factor=0.5,time_threshold=1000,max_iterations=1000000,w_normative=1,verbose=False):  
    """ For testing algorithm v_2 also similarity factor included """
    from algorithm_2_utilities import Likelihood
    from algorithm_2_v2 import generate_new_expression
    from relevance import is_relevant
    from rules_3 import expand,print_expression
    import sys
    import os.path
    import time
    from numpy import nan,exp,random,isnan
    from tqdm import tnrange, tqdm_notebook
    #Generate E0
    E_0=expand("NORMS")
    s=time.time()
    time_flag=0
    log_lik_null=Likelihood([],data,env,w_normative)
    while((time.time()-s)<time_threshold):
        time_flag=1
        if (Likelihood(E_0,data,env,w_normative)>log_lik_null):
            """ Compared to lok(Lik(no_norm) because for large sequences exp(log_Lik) gets to zero"""
            """ >= be cause we do rejection sampling for relevant norms below """
            if isnan(relevance_factor):
                break
            else:
                if (is_relevant(expression,task1,env)==False):
                    if (random.uniform()>relevance_factor):
                        break
                else:
                    if (random.uniform()<=relevance_factor):
                        break
        else:
            #print(Likelihood(E_0,data,env))
            E_0=expand("NORMS")
            time_flag=0
    print("Time to initialise E_0={:.4f}s".format(time.time()-s))
    if time_flag==0:
        print ("Stopping Algorithm, Not able to initialise E_0 in given time_threshold")
        return (nan,nan)
    print ("E0 chosen is:")
    print_expression(E_0)
    sequence=[E_0]
    lik_list=[]
    lik_list.append(exp(Likelihood(sequence[-1],data,env,w_normative)))
    original = sys.stdout
    exists = os.path.isfile('./{}.txt'.format(filename))
    if exists==True:
        os.remove('./{}.txt'.format(filename))
    for i in tnrange(1,max_iterations+1,desc="Length of Sequence"):
        if verbose==True:
            print ("\n--------------Iteration={}--------------".format(i))
        sys.stdout = open('./{}.txt'.format(filename), 'a+')
        if i==1:
            print ("\n-----------E0 chosen is:---------------")
            print_expression(E_0)
            print ("----------------------------------------")
        print ("\n\n===========================Iteration={}===========================".format(i))
        sequence.append(generate_new_expression(sequence[-1],data,task1,q_dict,rule_dict,env,relevance_factor,sim_threshold,similarity_penalty,w_normative))
        print_expression(sequence[-1])
        lik_list.append(exp(Likelihood(sequence[-1],data,env,w_normative)))
        print ("===================================================================")
        sys.stdout=original
    return (sequence,lik_list)
    

# =============================================================================
# env=create_env(N=30)
# sns.set_style("white")
# fig,ax=plt.subplots(figsize=(8,6))
# plot_env(env,ax,legend=True)
# 
# data=[]
# for i in range(100):
#     z=random.choice([1,2,3],p=[0.45,0.5,0.05])
#     o=random.choice([2,5,12,18,15])
#     data.append((("pickup",o),("putdown",o,z)))
#     
# 
# 
# from algorithm_2_utilities import violation
# 
# E_0=expand("NORMS")
# print_expression(E_0)
# v=violation(E_0,env)
# 
# 
# 
# exp_seq,lik_list=algorithm_1(data,env,q_dict,rule_dict,filename="mcmc_report4",max_iterations=50000)
# print ("Order of Improvement in Likelihood={:.2E}".format(max(lik_list)/min(lik_list)))
# 
# learned_norms=Counter(map(to_tuple,exp_seq))
# t=sum(learned_norms.values())
# 
# top=learned_norms.most_common()[:50]
# exists = os.path.isfile('./top_norms.txt')
# if exists==True:
#     os.remove('./top_norms.txt')
# original = sys.stdout
# for i in range(len(top)):
#     exp=top[i]
#     print("Rank:{} Norm has relative frequency={:.3f}%".format(i+1,exp[1]*100/t))
#     sys.stdout = open('./top_norms.txt', 'a+')
#     print("\n\n\n************Rank:{}, %-Frequency={:.3f}%**********".format(i+1,exp[1]*100/t))
#     print_expression(exp[0])
#     print("*************************************************")
#     sys.stdout=original
# 
# 
# import seaborn as sns
# sns.set_style("darkgrid")
# #sns.relplot(x="Different Norms", y="Frequency", kind="line", data=learned_norms)
# fig,ax=plt.subplots(figsize=(8,6))
# plt.plot(sorted(learned_norms.values()),"o-",c=(250/255,93/255,130/255,0.7),markerfacecolor=(250/255,18/255,72/255,0.77))
# plt.ylabel("Frequency in sample of size={}".format(t))
# plt.xlabel("Index of Norms from a total of {} Norms".format(len(learned_norms)))
# plt.title("Frequency of Norms")
# 
# =============================================================================
