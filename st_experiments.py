import streamlit as st
import os
import sys
import inspect

#uncomment if cloned from github!
user = os.getenv("USER")
sys.path.append("/home/%s/Sapsan/"%user)

from sapsan.lib.backends.fake import FakeBackend
from sapsan.lib.backends.mlflow import MLflowBackend
from sapsan.lib.data.hdf5_dataset import HDF5Dataset
from sapsan.lib.data import EquidistanceSampling
from sapsan.lib.estimator import CNN3d, CNN3dConfig
from sapsan.lib.estimator.cnn.spacial_3d_encoder import CNN3dModel
from sapsan.lib.experiments.evaluate_3d import Evaluate3d
from sapsan.lib.experiments.train import Train

import pandas as pd
import hiddenlayer as hl
import torch
import matplotlib.pyplot as plt
import configparser
import webbrowser
import time
import numpy as np
from threading import Thread
from streamlit.ReportThread import add_report_ctx
import json
from collections import OrderedDict
import plotly.express as px

cf = configparser.RawConfigParser()
widget_values = {}

def intro():
    st.sidebar.success("Select an experiment above.")

    st.markdown(
        """
        Sapsan is a pipeline for easy Machine Learning implementation in scientific projects.
        That being said, its primary goal and featured models are geared towards dynamic MHD 
        turbulence subgrid modeling. Sapsan will soon feature Physics-Informed Machine Learning
        models in its set of tools to accurately capture the turbulent nature appicable to 
        Core-Collapse Supernovae.

        Note: currently Sapsan is in alpha, but we are actively working on it and introduce new 
        feature on a daily basis.        

        **👈 Select an experiment from the dropdown on the left** to see what Sapsan can do!
        ### Want to learn more?
        - Check out Sapsan on [Github](https://github.com/pikarpov-LANL/Sapsan)
    """
    )
    
    show_license = st.checkbox('License Information', value=False)
    if show_license:
        st.markdown(
            """
© (or copyright) 2019. Triad National Security, LLC. All rights reserved. This program was produced under U.S. Government contract 89233218CNA000001 for Los Alamos National Laboratory (LANL), which is operated by Triad National Security, LLC for the U.S. Department of Energy/National Nuclear Security Administration. All rights in the program are reserved by Triad National Security, LLC, and the U.S. Department of Energy/National Nuclear Security Administration. The Government is granted for itself and others acting on its behalf a nonexclusive, paid-up, irrevocable worldwide license in this material to reproduce, prepare derivative works, distribute copies to the public, perform publicly and display publicly, and to permit others to do so.
        """
        )



def test(): 
    st.write('----Before----')
    try:
        cf.read('temp.txt')
        temp = dict(cf.items('config'))
        st.write(temp)
    except: st.write('no temp 8(')

    def make_recording_widget(f):
        """Return a function that wraps a streamlit widget and records the
        widget's values to a global dictionary.
        """
        def wrapper(label, *args, **kwargs):
            widget_value = f(label, *args, **kwargs)
            widget_values[label] = widget_value
            return widget_value

        return wrapper

    
    button = make_recording_widget(st.button)
    number = make_recording_widget(st.number_input)
    checkbox = make_recording_widget(st.checkbox)
    #button("recorded button")
    name = 'recorded number'
    default = 10
    if st.button("reset"):
        widget_values[name+'_default'] = default
        widget_values['flag'] = False
    
    
    def widget_history(name, default):
        if checkbox(name+'_checkbox'):
            try:
                if widget_values['flag'] == True:
                    widget_values['flag'] = False
                    try:
                        widget_values[name+'_default'] = int(temp[name])
                        number("recorded number", value = int(temp[name]))
                    except: number(name, value = widget_values[name+'_default'])
                else:
                    number(name, value = widget_values[name+'_default'])
                st.write('I tried and succeded')
            except: 
                widget_values['flag'] = False
                number(name, value = default)  
        else:
            widget_values['flag'] = True        
            widget_values[name+'_default'] = default
            
    name = 'recorded number'
    widget_history(name, default)
    

        
    st.write('----After----')
    st.write("recorded values: ", widget_values)
    
    with open('temp.txt', 'w') as file:
        file.write('[config]\n')
        for key, value in widget_values.items():
            file.write('%s = %s\n'%(key, value))


            
def cnn3d():
    st.title('Sapsan Configuration')
    st.write('This demo is meant to present capabilities of Sapsan. You can configure each part of the experiment at the sidebar. Once you are done, you can see the summary of your runtime parameters under _Show configuration_. In addition you can review the model that is being used (in the custom setup, you will also be able to edit it). Lastly click the _Run experiment_ button to train the test the ML model.')

    st.sidebar.markdown("General Configuration")
    
    try:
        cf.read('temp.txt')
        temp = dict(cf.items('config'))
    except: pass
    
    def make_recording_widget(f):
        """Return a function that wraps a streamlit widget and records the
        widget's values to a global dictionary.
        """
        def wrapper(label, *args, **kwargs):
            widget_value = f(label, *args, **kwargs)
            widget_values[label] = widget_value
            return widget_value

        return wrapper
           
    def widget_history_checkbox(title, params):
        if st.sidebar.checkbox(title):
            widget_history_checked(params)
        else:
            widget_history_unchecked(params)
    
    def widget_history_checked(params):
        widget_type = {number:int, text:str, checkbox:bool}
        for i in range(len(params)):
            label = params[i]['label']
            default = params[i]['default']
            widget = params[i]['widget']

            not_widget_params = ['default', 'widget', 'widget_type']
            additional_params = {key:value for key, value in params[i].items() if key not in not_widget_params}
            try:
                if widget_values[label+'_flag'] == True:
                    widget_values[label+'_flag'] = False
                    try:
                        widget_values[label+'_default'] = widget_type[widget](temp[label])
                        widget(value = widget_type[widget](temp[label]), **additional_params)
                    except: widget(value = widget_values[label+'_default'], **additional_params)
                else:
                    widget(value = widget_values[label+'_default'], **additional_params)
            except: 
                widget_values[label+'_flag'] = False
                widget(value = widget_type[widget](default), **additional_params)
    

    def widget_history_unchecked(params):
        widget_type = {number:int, text:str, checkbox:bool, selectbox:str}
        for i in range(len(params)):
            label = params[i]['label']
            default = params[i]['default']
            widget = params[i]['widget']
            
            widget_values[label+'_flag'] = True        
            widget_values[label+'_default'] = widget_type[widget](default)

    def load_config(config_file):
        cf.read(config_file)
        config = dict(cf.items('sapsan_config'))
        return config
    
    def selectbox_params():
        widget_values['backend_list'] = ['Fake', 'MLflow']
        widget_values['backend_selection_index'] = widget_values['backend_list'].index(widget_values['backend_selection'])

        
    def show_log(progress_slot, epoch_slot):
        from datetime import datetime
        
        #log_path = 'logs/checkpoints/_metrics.json'
        log_path = 'logs/log.txt'
        log_exists = False
        while log_exists == False:
            if os.path.exists(log_path):
                log_exists = True
            time.sleep(0.1)
            
        plot_data = {'epoch':[], 'train_loss':[]}
        last_epoch = 0
        running = True
        
        start_time= datetime.now()
        while running:
            with open(log_path) as file:
                #get the date of the latest event
                lines = list(file)
                latest_time = lines[-4].replace(",",".")
                latest_time = datetime.strptime(latest_time, '[%Y-%m-%d %H:%M:%S.%f] ')

                #check for the newest entry
                if start_time > latest_time:
                    continue
                else:
                    current_epoch = int(lines[-2].split('/')[0])
                    train_loss = float(lines[-2].split('loss=')[-1])
                    valid_loss = float(lines[-1].split('loss=')[-1])

            if current_epoch == last_epoch or current_epoch == -1:
                pass
            else:     
                #metrics = data['epoch_%d'%(current_epoch-1)][-1]
                metrics = {'train_loss':train_loss, 'valid_loss':valid_loss}
                epoch_slot.markdown('Epoch:$~$**%d** $~~~~~$ Train Loss:$~$**%.4e**'%(current_epoch, metrics['train_loss']))
                plot_data['epoch'] = np.append(plot_data['epoch'], current_epoch)
                plot_data['train_loss'] = np.append(plot_data['train_loss'], metrics['train_loss'])                
                df = pd.DataFrame(plot_data)
                
                if len(plot_data['epoch']) == 1:
                    plotting_routine = px.scatter
                else:
                    plotting_routine = px.line
                
                fig = plotting_routine(df, x="epoch", y="train_loss", log_y=True,
                              title='Training Progress', width=700, height=400)
                fig.layout.hovermode = 'x'
                progress_slot.plotly_chart(fig)
                
                last_epoch = current_epoch

            if current_epoch == widget_values['n_epochs']: 
                return
            
            time.sleep(0.1)  
            
    def run_experiment():
        
        #os.system("mlflow ui --port=%s &"%widget_values['mlflow_port'])
        
        if widget_values['backend_selection'] == 'Fake':
            tracking_backend = FakeBackend(widget_values['experiment name'])
            
        elif widget_values['backend_selection'] == 'MLflow':
            tracking_backend = MLflowBackend(widget_values['experiment name'], 
            widget_values['mlflow_host'],widget_values['mlflow_port'])
        
        #Load the data
        x, y = HDF5Dataset(path=widget_values['path'],
                           features=widget_values['features'],
                           target=widget_values['target'],
                           checkpoints=[0],
                           grid_size=int(widget_values['grid_size']),
                           checkpoint_data_size=int(widget_values['checkpoint_data_size']),
                           sampler=sampler).load()
        st.write("Dataset loaded...")
        
        #Set the experiment
        training_experiment = Train(name=widget_values["experiment name"],
                                     backend=tracking_backend,
                                     model=estimator,
                                     inputs=x, targets=y)
        
        #Plot progress
        progress_slot = st.empty()
        epoch_slot = st.empty()
        
        thread = Thread(target=show_log, args=(progress_slot, epoch_slot))
        add_report_ctx(thread)
        thread.start()

        start = time.time()
        #Train the model
        training_experiment.run()
        st.write('Trained in %.2f sec'%((time.time()-start)))
        st.success('Done! Plotting...')

        #def evaluate_experiment():
        #--- Test the model ---
        #Load the test data
        x, y = HDF5Dataset(path=widget_values['path'],
                           features=widget_values['features'],
                           target=widget_values['target'],
                           checkpoints=[0],
                           grid_size=int(widget_values['grid_size']),
                           checkpoint_data_size=int(widget_values['checkpoint_data_size']),
                           sampler=sampler).load()

        #Set the test experiment
        evaluation_experiment = Evaluate3d(name=widget_values["experiment name"],
                                           backend=tracking_backend,
                                           model=training_experiment.model,
                                           inputs=x, targets=y,
                                           grid_size=int(widget_values['grid_size']),
                                           checkpoint_data_size=int(widget_values['sample_to']))

        #Test the model
        evaluation_experiment.run()


        data = y
        #'data', data
        st.pyplot()
        
    #--- Load Default ---
    #button = make_recording_widget(st.sidebar.button)
    number = make_recording_widget(st.sidebar.number_input)
    number_main = make_recording_widget(st.number_input)
    text = make_recording_widget(st.sidebar.text_input)
    text_main = make_recording_widget(st.text_input)
    checkbox = make_recording_widget(st.sidebar.checkbox)
    selectbox = make_recording_widget(st.sidebar.selectbox)
    
    config_file = st.sidebar.text_input('Configuration file', "st_config.txt", type='default')
    
    if st.sidebar.button('reload config'):
        #st.caching.clear_cache()
        config = load_config(config_file)
        
        for key, value in config.items():
            widget_values[key+'_default'] = value
            widget_values[key] = value
            widget_values[key+'flag'] = None
        
        selectbox_params()                
        st.sidebar.text('... loaded config %s'%config_file)
        
    else:
        config = load_config(config_file)
        for key, value in config.items():
            if key in widget_values: pass
            else: widget_values[key] = value
        selectbox_params()
    
    st.sidebar.text('> Collapse all sidebar pars to reset <')
    
    widget_history_checked([{'label':'experiment name', 'default':config['experiment name'], 'widget':text}])

    if st.sidebar.checkbox('Backend', value=False):        
        widget_values['backend_selection'] = selectbox(
            'What backend to use?',
            widget_values['backend_list'], index=widget_values['backend_selection_index'])
        
        widget_values['backend_selection_index'] = widget_values['backend_list'].index(widget_values['backend_selection'])
        
        
        if widget_values['backend_selection'] == 'MLflow':
            widget_history_checked([{'label':'mlflow_host', 'default':config['mlflow_host'], 'widget':text}])
            widget_history_checked([{'label':'mlflow_port', 'default':config['mlflow_port'], 'widget':number,
                                                                        'min_value':1024, 'max_value':65535}])
    else:
        widget_history_unchecked([{'label':'mlflow_host', 'default':config['mlflow_host'], 'widget':text}])
        widget_history_unchecked([{'label':'mlflow_port', 'default':config['mlflow_port'], 'widget':number,
                                                                        'min_value':1024, 'max_value':65535}]) 

    
    widget_history_checkbox('Data',[{'label':'path', 'default':config['path'], 'widget':text},
                                    {'label':'features', 'default':config['features'], 'widget':text},
                                    {'label':'target', 'default':config['target'], 'widget':text},
                                    {'label':'checkpoint_data_size', 'default':config['checkpoint_data_size'], 
                                                                     'widget':number, 'min_value':1},
                                    {'label':'sample_to', 'default':config['sample_to'], 
                                                                     'widget':number, 'min_value':1},
                                    {'label':'grid_size', 'default':config['grid_size'], 
                                                                     'widget':number, 'min_value':1}])
    

        
    widget_history_checkbox('Model',[{'label':'n_epochs', 'default':config['n_epochs'], 'widget':number, 'min_value':1},
                                     {'label':'patience', 'default':config['patience'], 'widget':number, 'min_value':0},
                                     {'label':'min_delta', 'default':config['min_delta'], 'widget':text}])  

    #sampler_selection = st.sidebar.selectbox('What sampler to use?', ('Equidistant3D', ''), )
    if widget_values['sampler_selection'] == "Equidistant3D":
        sampler = EquidistanceSampling(int(widget_values['checkpoint_data_size']), 
                                       int(widget_values['sample_to']), int(widget_values['axis']))
    
    estimator = CNN3d(config=CNN3dConfig(n_epochs=int(widget_values['n_epochs']), 
                                         grid_dim=int(widget_values['grid_size']), 
                                         patience=int(widget_values['patience']), 
                                         min_delta=float(widget_values['min_delta'])))


    show_config = [
        ['experiment name', widget_values['experiment name']],
        ['data path', widget_values['path']],
        ['features', widget_values['features']],
        ['target', widget_values['target']],
        ['Dimensionality of the data', widget_values['axis']],
        ['Size of the data per axis', widget_values['checkpoint_data_size']],
        ['Reduce each dimension to', widget_values['sample_to']],
        ['Batch size per dimension', widget_values['grid_size']],
        ['number of epochs', widget_values['n_epochs']],
        ['patience', widget_values['patience']],
        ['min_delta', widget_values['min_delta']],
        ['backend_selection', widget_values['backend_selection']]
        ]
        
    if widget_values['backend_selection']=='MLflow': 
        show_config.append(['mlflow_host', widget_values['mlflow_host']])
        show_config.append(['mlflow_port', widget_values['mlflow_port']])
    
    if st.checkbox("Show configuration"):
        st.table(pd.DataFrame(show_config, columns=["key", "value"]))

    if st.checkbox("Show model graph"):
        res = hl.build_graph(estimator.model, torch.zeros([72, 1, 2, 2, 2]))
        st.graphviz_chart(res.build_dot())

    if st.checkbox("Show code of model"):
        st.code(inspect.getsource(CNN3dModel), language='python')
        st.write('***Code editing is available in the local GUI version***')

    if st.button("Run experiment"):
        #st.write("Experiment is running. Please hold on...")
        st.caching.clear_cache()
        start = time.time()
        try: os.remove('logs/logs.txt')
        except: pass
        
        run_experiment()
        
        st.write('Finished in %.2f mins'%((time.time()-start)/60))
        st.write('***MLflow interface is available in the local GUI version***')

    #if st.button("Evaluate experiment"):
    #    #st.write("Experiment is running. Please hold on...")
    #    evaluate_experiment()
    
    with open('temp.txt', 'w') as file:
        file.write('[config]\n')
        for key, value in widget_values.items():
            file.write('%s = %s\n'%(key, value))

        
def custom():
    st.markdown("# Available in the local GUI version!")
    
def ccsn():
    import os
    
    st.markdown("# ** Temporarily unavailable - please check back on 6/19 **")    
    st.markdown("# 1D Core-Collapse Supernovae Experiment")
    st.write('Below is an example on our ML implementation within 1D CCSN code developed by Chris Fryer (Los Alamos National Laboratory)')
    
    def run_ccsn():
        os.system("./ChCode/run15f1/st_test")
        st.error("At line 4617 of file 1dburn.f (unit = 60, file = 'tst1')")
    
    if st.button("Run experiment"):
        run_ccsn()
        
        
def config_write(var, file):
    cf.read(config_file)
    cf['sapsan_config'][''] = '1123'
    with open(config_file, 'w') as file:
        cf.write(file)
    
    
   


'''
@st.cache(allow_output_mutation=True, suppress_st_warning=True)
def write_config(config_file, config):
    with open(config_file, 'w') as file:
        st.write('writing to file! ', config['n_epochs'])
        file.write('[sapsan_config]\n')
        for key, value in config.items():
            file.write('%s = %s \n'%(key, value))
'''
