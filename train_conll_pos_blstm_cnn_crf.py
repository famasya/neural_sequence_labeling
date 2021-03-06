import tensorflow as tf
import os
from utils.conll2003_prepro import process_data
from models.blstm_cnn_crf_model import SequenceLabelModel
from utils import batchnize_dataset

# dataset parameters
tf.compat.v1.flags.DEFINE_string("task_name", "pos", "task name")
tf.compat.v1.flags.DEFINE_string("language", "english", "language")  # used for inference, indicated the source language
tf.compat.v1.flags.DEFINE_string("raw_path", "data/raw/conll2003/raw", "path to raw dataset")
tf.compat.v1.flags.DEFINE_string("save_path", "data/dataset/conll2003/pos", "path to save dataset")
tf.compat.v1.flags.DEFINE_string("glove_name", "6B", "glove embedding name")
tf.compat.v1.flags.DEFINE_boolean("char_lowercase", True, "char lowercase")
# glove embedding path
glove_path = os.path.join(os.path.expanduser('~'), "utilities", "embeddings", "glove.{}.{}d.txt")
tf.compat.v1.flags.DEFINE_string("glove_path", glove_path, "glove embedding path")

# dataset for train, validate and test
tf.compat.v1.flags.DEFINE_string("vocab", "data/dataset/conll2003/pos/vocab.json", "path to the word and tag vocabularies")
tf.compat.v1.flags.DEFINE_string("train_set", "data/dataset/conll2003/pos/train.json", "path to the training datasets")
tf.compat.v1.flags.DEFINE_string("dev_set", "data/dataset/conll2003/pos/dev.json", "path to the development datasets")
tf.compat.v1.flags.DEFINE_string("test_set", "data/dataset/conll2003/pos/test.json", "path to the test datasets")
tf.compat.v1.flags.DEFINE_string("pretrained_emb", "data/dataset/conll2003/pos/glove_emb.npz", "pretrained embeddings")

# network parameters
tf.compat.v1.flags.DEFINE_string("cell_type", "lstm", "RNN cell for encoder and decoder: [lstm | gru], default: lstm")
tf.compat.v1.flags.DEFINE_integer("num_units", 300, "number of hidden units for rnn cell")
tf.compat.v1.flags.DEFINE_integer("num_layers", None, "number of rnn layers")
tf.compat.v1.flags.DEFINE_boolean("use_stack_rnn", False, "True: use stacked rnn, False: use normal rnn (used for layers > 1)")
tf.compat.v1.flags.DEFINE_boolean("use_pretrained", True, "use pretrained word embedding")
tf.compat.v1.flags.DEFINE_boolean("tuning_emb", False, "tune pretrained word embedding while training")
tf.compat.v1.flags.DEFINE_integer("emb_dim", 300, "embedding dimension for encoder and decoder input words/tokens")
tf.compat.v1.flags.DEFINE_boolean("use_chars", True, "use char embeddings")
tf.compat.v1.flags.DEFINE_boolean("use_residual", False, "use residual connection")
tf.compat.v1.flags.DEFINE_boolean("use_layer_norm", False, "use layer normalization")
tf.compat.v1.flags.DEFINE_integer("char_emb_dim", 100, "character embedding dimension")
tf.compat.v1.flags.DEFINE_boolean("use_highway", True, "use highway network")
tf.compat.v1.flags.DEFINE_integer("highway_layers", 2, "number of layers for highway network")
tf.compat.v1.flags.DEFINE_multi_integer("filter_sizes", [100, 100], "filter size")
tf.compat.v1.flags.DEFINE_multi_integer("channel_sizes", [5, 5], "channel size")
tf.compat.v1.flags.DEFINE_boolean("use_crf", True, "use CRF decoder")
# attention mechanism (normal attention is Lurong/Bahdanau liked attention mechanism)
tf.compat.v1.flags.DEFINE_string("use_attention", None, "use attention mechanism: [None | self_attention | normal_attention]")
# Params for self attention (multi-head)
tf.compat.v1.flags.DEFINE_integer("attention_size", None, "attention size for multi-head attention mechanism")
tf.compat.v1.flags.DEFINE_integer("num_heads", 8, "number of heads")

# training parameters
tf.compat.v1.flags.DEFINE_float("lr", 0.001, "learning rate")
tf.compat.v1.flags.DEFINE_string("optimizer", "adam", "optimizer: [adagrad | sgd | rmsprop | adadelta | adam], default: adam")
tf.compat.v1.flags.DEFINE_boolean("use_lr_decay", True, "apply learning rate decay for each epoch")
tf.compat.v1.flags.DEFINE_float("lr_decay", 0.05, "learning rate decay factor")
tf.compat.v1.flags.DEFINE_float("minimal_lr", 1e-5, "minimal learning rate")
tf.compat.v1.flags.DEFINE_float("grad_clip", 5.0, "maximal gradient norm")
tf.compat.v1.flags.DEFINE_float("keep_prob", 0.5, "dropout keep probability for embedding while training")
tf.compat.v1.flags.DEFINE_integer("batch_size", 20, "batch size")
tf.compat.v1.flags.DEFINE_integer("epochs", 100, "train epochs")
tf.compat.v1.flags.DEFINE_integer("max_to_keep", 5, "maximum trained models to be saved")
tf.compat.v1.flags.DEFINE_integer("no_imprv_tolerance", 5, "no improvement tolerance")
tf.compat.v1.flags.DEFINE_string("checkpoint_path", "ckpt/conll2003_pos/", "path to save models checkpoints")
tf.compat.v1.flags.DEFINE_string("summary_path", "ckpt/conll2003_pos/summary/", "path to save summaries")
tf.compat.v1.flags.DEFINE_string("model_name", "pos_blstm_cnn_crf_model", "models name")

# convert parameters to dict
config = tf.compat.v1.flags.FLAGS.flag_values_dict()

# create dataset from raw data files
if not os.path.exists(config["save_path"]) or not os.listdir(config["save_path"]):
    process_data(config)
if not os.path.exists(config["pretrained_emb"]) and config["use_pretrained"]:
    process_data(config)

print("Load datasets...")
# used for training
train_set = batchnize_dataset(config["train_set"], config["batch_size"], shuffle=True)
# used for computing validate loss
valid_data = batchnize_dataset(config["dev_set"], batch_size=1000, shuffle=True)[0]
# used for computing validate accuracy, precision, recall and F1 scores
valid_set = batchnize_dataset(config["dev_set"], config["batch_size"], shuffle=False)
# used for computing test accuracy, precision, recall and F1 scores
test_set = batchnize_dataset(config["test_set"], config["batch_size"], shuffle=False)

print("Build models...")
model = SequenceLabelModel(config)
model.train(train_set, valid_data, valid_set, test_set)

print("Inference...")
sentences = ["EU rejects German call to boycott British lamb ."]
ground_truths = ["NNP VBZ     JJ     NN   TO VB      JJ      NN   ."]
for sentence, truth in zip(sentences, ground_truths):
    result = model.inference(sentence)
    print(result)
    print("Ground truth:\n{}\n".format(truth))
