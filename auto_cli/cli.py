import argparse
from collections import OrderedDict
import enum
import functools
import inspect
import sys
import traceback
from typing import Dict

TOP_LEVEL_ARGS=['func', 'help', 'verbose']

class CLI:
  class ArgFormatter(argparse.HelpFormatter):
    """Help message formatter which adds default values to argument help.
    Only the name of this class is considered a public API. All the methods
    provided by the class are considered an implementation detail.
    """

    def _get_help_string(self, action):
      help = action.help
      print("HERE, orig helop", dir(action))
      print(action)
      if '%(default)' not in action.help:
        if action.default is not argparse.SUPPRESS:
          defaulting_nargs = [argparse.OPTIONAL, argparse.ZERO_OR_MORE]
          if action.option_strings or action.nargs in defaulting_nargs:
            help += ' (default: %(default)s)'
            pass
      #help+=":%(type)s"  if hasattr(action,'type') else '' # in action else '' #Default=[%(default)s]') if 'default' in parm_opts else ''
      # help+="=%(default)s" if 'default' in action else ''
      # help+="  -> [%(choices)s]" if 'choices' in action else ''

      return help

  def __init__(self, target_module, title, function_opts:Dict[str, Dict]):
    self.target_module = target_module
    self.title = title
    self.function_opts = function_opts

  def fn_callback(self, fn_name, args):
    res = self.execute_model_fn(fn_name, args)
    print(f"[{self.title}] Results for {fn_name}", res)

  def execute_model_fn(self, fn_name:str, fn_args:Dict):
    fn = getattr(self.target_module, fn_name)
    return fn(**fn_args)

  def sig_parms(self, fn_name:str):
    fn = getattr(self.target_module, fn_name)
    sigs = inspect.signature(fn)
    return sigs.parameters

  @staticmethod
  def add_sig_parm_args(sig_parms:OrderedDict, subparser):

    for parm_name, parm in sig_parms.items():
      parm_opts = {}

      has_default = parm.default is not parm.empty

      annotation = parm.annotation
      if annotation is not parm.empty:
        if annotation == str:
          parm_opts['type'] = str
          if has_default:
            parm_opts['default'] = parm.default# f'"{str(parm.default)}"'
        elif annotation == int:
          parm_opts['type'] = int
          if has_default:
            parm_opts['default'] =  parm.default
        elif annotation == bool:
          parm_opts['type'] = bool
          if has_default:
            parm_opts['default'] =  parm.default
        elif annotation == float:
          parm_opts['type'] = float
          if has_default:
            parm_opts['default'] =  parm.default
        elif issubclass(annotation, enum.Enum):

          # Easy lookup for enumeration types:
          def choice_type_fn(enum_type:enum.Enum, arg:str):
            return enum_type[arg.split(".")[-1]]

          # Convert enumeration to choices:
          parm_opts['choices'] = [e for e in annotation]
          parm_opts['type'] = functools.partial(choice_type_fn, annotation)

          if has_default and hasattr(parm.default, 'name'):
            # Set default to friendly enum value:
            parm_opts['default'] = f"{parm.default}"
        else:
          pass
          #parm_opts['type'] = "unknown" #f"**{'xox'}(**)" #str(annotation)
          #print("UNRECOG ANNOT", annotation)

      if parm_opts:
        help = []
        if 'choices' in parm_opts:
          help.append("Choices: [%(choices)s]")
        elif 'type' in parm_opts:
          help.append("Type:%(type)s")

        if 'default' in parm_opts:
          help.append("=%(default)s(default)")

        #help += f'keys={str(parm_opts.keys())}'
        parm_opts['help'] = "".join(help)
      parm_opts['metavar'] = parm_name.upper()
      subparser.add_argument(f"--{parm_name}", **parm_opts)

  @staticmethod
  def _add_enh_signature(enh_name, enh, str_builder):
    """ Utility function to add signature of method """
    parms = []
    signature = inspect.signature(enh)
    if signature != signature.empty:
      for p in signature.parameters.values():
        parm = f'{p.name}'
        # Sig annotation, if any:
        if p.annotation != p.empty:
          if p.annotation == str:
            parm += ':str'
          if p.annotation == int:
            parm += ':int'
          else:
            parm += f':{p.annotation}'
        if p.default != p.empty:
          parm += f'={p.default}'
        parms.append(parm)

      # Add all parms as string to sig:
      parm_str = ', '.join(parms)
      sig = f"{enh_name}({parm_str})"
      if signature.return_annotation != signature.empty:
        if p.annotation == str:
          sig += ' => str'
        else:
          sig += f" => {signature.return_annotation}"
      # str_builder.append(textwrap.indent("Signature:", CHAR_TAB))
      # str_builder.append(textwrap.indent(sig, CHAR_TAB2))
    return str_builder

  def create_arg_parser(self):
    #HELP_FORMATTER = functools.partial(argparse.HelpFormatter, prog=None, max_help_position=120)
    parser = argparse.ArgumentParser(
      description=self.title,
      prog=self.title,
      add_help=True,
      formatter_class=functools.partial(argparse.HelpFormatter, prog=None, max_help_position=120)
    )

    subparser = parser.add_subparsers(
      title='Commands',
      description='Valid Commands',
      help='Additional Help:',
    )

    # Custom help arg:
    # parser.add_argument(
    #   '-h',
    #   '--help',
    #   action="store_true",
    #   help='Show help with increasing level of verbosity using --verbose flag'
    # )

    parser.add_argument(
      "-v",
      "--verbose",
      help="increase output verbosity",
      action="store_true"
    )

    # Subparsers automatically setup based on function signatures:
    for fn_name, fn_opt in self.function_opts.items():
      callback_fn = functools.partial(self.fn_callback, fn_name)
      self.setup_subparser(parser, subparser, fn_name, callback_fn, fn_opt["description"])

    return parser

  def setup_subparser(self, parser, subparser, fn_name, func_callback, help):
    sub_parser = subparser.add_parser(fn_name, help=help)

    # Get signature parms and add corresponding arguments:
    parms = self.sig_parms(fn_name)
    CLI.add_sig_parm_args(parms, sub_parser)

    help_formatter = functools.partial(argparse.HelpFormatter,prog=parser.prog,max_help_position=80)
    sub_parser.set_defaults(func=func_callback)
    sub_parser.formatter_class = help_formatter#argparse.HelpFormatter(prog=parser.prog, max_help_position=100)#   CLI.ArgFormatter#argparse.ArgumentDefaultsHelpFormatter
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
            #helps.append(textwrap.indent(subparser.format_help(), '  '))
            helps.append(subparser.format_help())

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
          #print(textwrap.indent(command_help, prefix='  '))
          print(command_help)

          args.func(fn_args)
        # elif 'help' in args and args.help:
        #   print("HELP:")
        #   print(parser.format_help())
        #   if 'verbose' in args:
        #     print("Help for commands:")
        #     command_help = CLI.__get_commands_help__(parser)
        #     print(command_help)

    except Exception as x:
      print(f"Unexpected Error: {type(x)}: '{x}'")
      traceback.print_exc()
      x.__traceback__.print_stack()
    finally:
      parser.exit()

