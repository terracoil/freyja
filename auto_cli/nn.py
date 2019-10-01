import importlib

import os
import numpy
import pathlib
import data_storage
import grapher as grapher
import torch
from torch.utils.data import DataLoader

import train_callbacks
from cli import CLI
import utils
DATA_DIR_DEFAULT = 'data/ag_news_csv'
MODEL_DIR_DEFAULT = 'ag_news_model'
MODEL_CLASS_DEFAULT = 'char_nn_conv'

# Maximum length. Longer gets chopped. Shorter gets padded.
MAX_CHAR_COUNT = 1044

STATUS_MSG = "{} Results - Epoch: {}  Avg accuracy: {:.2f} Avg loss: {:.2f}"

def train(
  data_dir:str=DATA_DIR_DEFAULT,
  model_class:str=MODEL_CLASS_DEFAULT,
  model_dir:str=MODEL_DIR_DEFAULT,
  initial_learning_rate:float=0.0001,
  seed:int=2112,
  batch_size:int=512,
  epochs:int = 20,
  max_samples:int = 0,
  checkpoint_suffix:str = "",
  device = 'cpu',
):
  _setup_pytorch(seed)
  store = data_storage.DataStorage(data_dir)
  categories = store.categories
  cat_count = len(categories)
  print("Model Dir", model_dir)

  model_cls = model_factory(model_class)

  dataset_train, dataset_test, dataset_holdout, categories = store.load_from_dir(max_samples=max_samples)
  if len(dataset_train) ==0 or len(dataset_test)==0:
    print("ERROR: Sample count(max_samples) must exceed batch_size.")
    return
  print(f"Categories:{categories}")
  class_weights = torch.tensor(store.class_weights(), dtype=torch.float32)

  model = setup_model_structure(categories, model_cls)
  loss_fn = torch.nn.CrossEntropyLoss(weight=class_weights)
  optimizer = torch.optim.Adam(model.parameters(), lr=0.001)

  start_epoch, best_acc=utils.load_train_checkpoint(model, optimizer, model_dir, checkpoint_suffix)

  pathlib.Path(model_dir).mkdir(parents=True, exist_ok=True)
  train_loader = DataLoader(dataset_train, batch_size=batch_size, num_workers=0, drop_last=True, shuffle=True)
  test_loader = DataLoader(dataset_test, batch_size=batch_size, num_workers=0, drop_last=True, shuffle=False)
  holdout_loader = DataLoader(dataset_holdout, batch_size=batch_size, num_workers=0, drop_last=True, shuffle=False)


  callbacks = train_callbacks.TrainCallbacks(model, model_dir, categories, loss_fn, optimizer, epochs, best_acc)
  print('Training model...', len(dataset_train))
  model.train()
  for epoch in range(start_epoch, epochs + 1):
    for b, batch in enumerate(train_loader):
      #with torch.set_grad_enabled(True):
      x, y_truth = batch
      optimizer.zero_grad()

      #x = x.to(device)
      y_truth = y_truth.to(device)

      #x.requires_grad_()
      y_pred = model(x)

      y_truth = y_truth
      #y_pred = y_pred.argmax(dim=1)
      # print("YYY", y_pred.size())
      #print("YYY", y_pred, y_truth)
      loss = loss_fn(y_pred, y_truth)
      loss.backward()
      optimizer.step()
      # print(f"{epoch}:{b} Loss:{loss}")
      #optimizer.zero_grad()
      callbacks.on_batch_end(epoch, batch, b, loss.data.item(), train_loader)
      torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)

    acc, loss, conf_matrix = utils.verify_model_on(model, holdout_loader, categories, losser=loss_fn, verbose=True)
    print("HOLDOIUT acc, loss, conf_matrix", acc, loss, conf_matrix)

    if callbacks.on_epoch_end(epoch, test_loader):
      print("Early stopping...")
      break

  utils.save_infer_model(model, model_dir)
  acc, loss, conf_matrix = utils.verify_model_on(model, test_loader, categories, losser=loss_fn, verbose=True)
  print("TEST acc, loss, conf_matrix", acc, loss, conf_matrix)

  acc, loss, conf_matrix = utils.verify_model_on(model, holdout_loader, categories, losser=loss_fn, verbose=True)
  print("HOLDOUT acc, loss, conf_matrix", acc, loss, conf_matrix)

def setup_model_structure(categories, model_cls, training:bool=True):
  print('Building model...')
  model = model_cls.NNConvolution(
    dense_neurons=1024,
    max_len=MAX_CHAR_COUNT,
    cat_output=len(categories),
    filter_size=256,
  )
  model.train(training)
  return model

def _setup_pytorch(seed=2112):
  torch.manual_seed(0)
  numpy.random.seed(0)

def lr(
  data_dir:str=DATA_DIR_DEFAULT,
  model_dir:str=MODEL_DIR_DEFAULT,
):
  print("lr")

def graph(
  data_dir:str=DATA_DIR_DEFAULT,
  model_class: str = MODEL_CLASS_DEFAULT,
  model_dir:str=MODEL_DIR_DEFAULT,
  batch_size:int=80,
  max_samples:int=0,
  seed:int=2112,
):
  model_cls = model_factory(model_class)
  _setup_pytorch(seed)
  store = data_storage.DataStorage(data_dir)
  cat_count = len(store.categories)
  model = torch.load(f'{model_dir}/model.pt')

  dataset_train, dataset_test, categories = store.load_from_dir(max_samples=max_samples)

  print("graph model ", model)
  grapher.save_model_graph(model)
  y_pred = model.predict(dataset_test)
  #grapher.save_confusion_matrix(model, x_test, y_test, y_pred)

def predict(
  model_dir:str=MODEL_DIR_DEFAULT,
  seed:int=2112,
):
  _setup_pytorch(seed)
  print("predict")

def verify(
  data_dir:str=DATA_DIR_DEFAULT,
  model_class:str=MODEL_CLASS_DEFAULT,
  model_dir:str=MODEL_DIR_DEFAULT,
  checkpoint_suffix:str = "",
  max_samples:int=0,
  seed:int=2112,
  batch_size:int=512,
):
  _setup_pytorch(seed)
  store = data_storage.DataStorage(data_dir)
  categories = store.categories
  cat_count = len(categories)

  dataset_train, dataset_test, _ = store.load_from_dir( max_samples=max_samples)

  model_cls = model_factory(model_class)
  training_model = setup_model_structure(categories, model_cls, False)
  model = utils.load_infer_model(training_model, checkpoint_suffix, model_dir)

  return _evaluate_model(model, dataset_test, categories, batch_size)

def model_factory(model_class):
  return importlib.import_module(model_class)

def setup_training_model(model):
  #sgd = SGD(lr=0.01, momentum=0.9)
  print("setup_training_model...")
  #loss = torch.nn.NLLLoss()
  loss = torch.nn.CrossEntropyLoss()
  optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
  return loss, optimizer

def _evaluate_model(model, dataset, categories, batch_size=32):
  data_loader = DataLoader(dataset, batch_size=batch_size, num_workers=0, shuffle=False)
  print(f"Verifying with model Training=={model.training}-{model}")
  acc, _, conf_matrix = utils.verify_model_on(model, data_loader, categories)
  print(f"Model accuracy: {100*acc:.2f}%")
  print(utils.format_confusion_matrix(conf_matrix))
  # data_loader = DataLoader(dataset, batch_size=batch_size, num_workers=0, shuffle=False)
  # for b, batch in enumerate(data_loader):
  #   x, y_truth = batch
  #   y_pred = model(x)
  #   acc, _ = utils.calc_accuracy(y_pred, y_truth, categories)
  #   print(f"Model accuracy: {acc:.2f}%", acc * 100.0)

if __name__ == '__main__':
  fn_opts = {
    'lr': dict(description='Find Learning Rate '),
    'graph': dict(description='Graph(s)'),
    'predict': dict(description='Predict'),
    'train': dict(description='Train'),
    'verify': dict(description='Verify'),
  }

  nn_mod = importlib.import_module('nn')
  cli = CLI(nn_mod, function_opts=fn_opts)
  cli.display()
