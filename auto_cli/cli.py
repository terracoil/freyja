import argparse
from collections import OrderedDict
import functools
import importlib
import textwrap
import inspect
from typing import (Dict, List)
import pprint
import traceback
import sys


TOP_LEVEL_ARGS=['func', 'help', 'verbose']

class CLI:
  def __init__(self, target_module, function_opts:Dict[str, Dict]):
    self.target_module = target_module
    self.function_opts = function_opts

  def fn_callback(self, fn_name, args):
    res = self.execute_model_fn(fn_name, args)
    print(f"Results for {fn_name}", res)

  def execute_model_fn(self, fn_name:str, fn_args:Dict):
    #mod = importlib.import_module(module_name)
    fn = getattr(self.target_module, fn_name)
    return fn(**fn_args)

  def sig_parms(self, fn_name:str):
    #mod = importlib.import_module(module_name)
    fn = getattr(self.target_module, fn_name)
    sigs = inspect.signature(fn)
    return sigs.parameters

  @staticmethod
  def add_sig_parm_args(sig_parms:OrderedDict, subparser):
    for parm_name in sig_parms:
      parm = sig_parms[parm_name]
      parm_opts = {}
      if parm.default is not parm.empty:
        parm_opts['default'] = str(parm.default)

      if parm.annotation is not parm.empty:
        parm_opts['type'] = parm.annotation

      #print(f"parm: --{parm_name}", parm_opts)
      subparser.add_argument(f"--{parm_name}", **parm_opts)

  def create_arg_parser(self):
    # create_arg_parser.train_parms = sig_parms('nn', 'train')
    # create_arg_parser.lr_parms = sig_parms('nn', 'lr')
    # create_arg_parser.graph_parms = sig_parms('nn', 'graph')
    # create_arg_parser.predict_parms = sig_parms('nn', 'predict')
    # create_arg_parser.verify_parms = sig_parms('nn', 'verify')

    parser = argparse.ArgumentParser(
      description='Char CNN Model',
      prog='char_cnn',
      add_help=False,
      formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    subparser = parser.add_subparsers(
      title='Commands',
      description='Valid Commands',
      help='Additional Help:',
    )

    # Custom help arg:
    parser.add_argument(
      '-h',
      '--help',
      action="store_true",
      help='Show help with increasing level of verbosity using --verbose flag'
    )

    parser.add_argument(
      "-v",
      "--verbose",
      help="increase output verbosity",
      action="store_true"
    )

    # Subparsers automatically setup based on function signatures:
    for fn_name, fn_opt in self.function_opts.items():
      callback_fn = functools.partial(self.fn_callback, fn_name)
      self.setup_subparser(subparser, fn_name, callback_fn, fn_opt["description"])

    # lr_callback = functools.partial(self.fn_callback, "lr")
    # graph_callback = functools.partial(self.fn_callback, "graph")
    # predict_callback = functools.partial(self.fn_callback, "predict")
    # train_callback = functools.partial(self.fn_callback, "train")
    # verify_callback = functools.partial(self.fn_callback, "verify")
    #
    # self.setup_subparser(subparser, 'lr', lr_callback, 'Find Learning Rate for %(prog)s')
    # self.setup_subparser(subparser, 'graph', graph_callback, 'Graph(s) for %(prog)s')
    # self.setup_subparser(subparser, 'predict', predict_callback, 'Predict using %(prog)s')
    # self.setup_subparser(subparser, 'train', train_callback, 'Train using %(prog)s')
    # self.setup_subparser(subparser, 'verify', verify_callback, 'Verify using %(prog)s')

    return parser

  def setup_subparser(self, subparser, fn_name, func_callback, help):
    sub_parser = subparser.add_parser(fn_name, help=help)

    # Get signature parms and add corresponding arguments:
    parms = self.sig_parms(fn_name)
    CLI.add_sig_parm_args(parms, sub_parser)

    sub_parser.formatter_class = argparse.ArgumentDefaultsHelpFormatter
    sub_parser.set_defaults(func=func_callback)
    return sub_parser

  @staticmethod
  def __get_commands_help__(parser, command_name:str=None, usage=False):
    helps = []

    subparsers_actions = [
      action for action in parser._actions
      if isinstance(action, argparse._SubParsersAction)
    ]

    for subparsers_action in subparsers_actions:
      for choice, subparser in subparsers_action.choices.items():
        if command_name is None or command_name == choice:
          if usage:
            helps.append(subparser.format_usage())
          else:
            helps.append(f"Command '{choice}'")
            helps.append(textwrap.indent(subparser.format_help(), '  '))

    return "\n".join(helps)

  def display(self):
    parser = self.create_arg_parser()
    try:
      if len(sys.argv[1:])==0:
        print(parser.format_help())
        #parser.print_usage() # for just the usage line
      else:
        args = parser.parse_args()
        if 'func' in args:
          vargs = vars(args)
          fn_args = {k: vargs[k] for k in vargs if k not in TOP_LEVEL_ARGS}

          # Show Usage no matter what:
          cmd_name = args.func.args[0]# __name__.replace('_callback', '')
          print(f"Command Name: {cmd_name}")
          command_help = CLI.__get_commands_help__(parser, cmd_name, True)
          print(textwrap.indent(command_help, prefix='  '))

          args.func(fn_args)
        elif 'help' in args and args.help:
          print("HELP:")
          print(parser.format_help())
          if 'verbose' in args:
            print("Help for commands:")
            command_help = CLI.__get_commands_help__(parser)
            print(textwrap.indent(command_help, prefix='  '))

    except Exception as x:
      print(f"Unexpected Error: {type(x)}: '{x}'")
      traceback.print_exc()
      x.__traceback__.print_stack()
    finally:
      parser.exit()

