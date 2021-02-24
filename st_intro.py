import inspect
import textwrap
from collections import OrderedDict

import streamlit as st
import st_experiments as experiments

EXPERIMENTS = OrderedDict(
    [
        ("Welcome", (experiments.intro, None)),
        ("Examples", (experiments.cnn3d, None)),
    ]
)

def run():
    experiment_name = st.sidebar.selectbox("Choose an experiment", list(EXPERIMENTS.keys()),0)
    experiment = EXPERIMENTS[experiment_name][0]
    
    if experiment_name == 'Welcome':
        show_code = False
    else:
        pass
    
    experiment()


if __name__ == "__main__":
    run()