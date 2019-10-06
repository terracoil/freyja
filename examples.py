#!/usr/bin/env python
"""
  Simple Examples of CLI creation.
"""
import sys
from auto_cli.cli import CLI
import enum

def foo():
  print("FOO!")

def train(
  data_dir:str='./data/',
  initial_learning_rate:float=0.0001,
  seed:int=2112,
  batch_size:int=512,
  epochs:int = 20):
  print("Training with initial_learning_rate:{initial_learning_rate}, seed:{seed}, batch_size:{batch_size}, epochs:{epochs} into data_dir:{data_dir}")

#AnimalEnum = enum.Enum('Animal', 'ANT BEE CAT DOG')
class AnimalEnum(enum.Enum):
  ANT = 1
  BEE = 2
  CAT = 3
  DOG = 4

def count_animals(count:int=20, animal:AnimalEnum=AnimalEnum.BEE):
  return count

if __name__ == '__main__':
  fn_opts = {
    'foo':   {'description':'Foobar'},
    'train': {'description':'Train'},
    'count_animals': {'description':'Count Animals'},
  }

  cli = CLI(sys.modules[__name__], function_opts=fn_opts, title="Foobar Example CLI")
  cli.display()


