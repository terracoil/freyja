#!/usr/bin/env python
"""
  Simple Examples of CLI creation.
"""
import sys
from auto_cli import CLI



def foo():
  print("FOO!")

def train(
  data_dir:str='./data/',
  initial_learning_rate:float=0.0001,
  seed:int=2112,
  batch_size:int=512,
  epochs:int = 20):
  print("Training with initial_learning_rate:{initial_learning_rate}, seed:{seed}, batch_size:{batch_size}, epochs:{epochs} into data_dir:{data_dir}")

if __name__ == '__main__':
  fn_opts = {
    'foo': dict(description='FOO CLI TEST'),
    'graph': dict(description='Graph(s)'),
  }

  cli = CLI(sys.modules[__name__], function_opts=fn_opts)
  cli.display()


