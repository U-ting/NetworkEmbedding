#-----------------------------------------------------------------------------------------------#
#                                                                                               #
#   I M P O R T     L I B R A R I E S                                                           #
#                                                                                               #
#-----------------------------------------------------------------------------------------------# 

import os
import sys
import random
from io import open
from argparse import ArgumentParser, FileType, ArgumentDefaultsHelpFormatter
from collections import Counter, Mapping
import logging

import graph
from gensim.models import Word2Vec
from gensim.models.word2vec import Vocab

from six import text_type as unicode
from six import iteritems
from six import string_types
from six.moves import range

#-----------------------------------------------------------------------------------------------#
#                                                                                               #
#   DEEPWALK                                                                                    #
#                                                                                               #
#-----------------------------------------------------------------------------------------------# 


logger = logging.getLogger(__name__)
LOGFORMAT = "%(asctime).19s %(levelname)s %(filename)s: %(lineno)s %(message)s"

def main():
  parser = ArgumentParser("deepwalk",formatter_class=ArgumentDefaultsHelpFormatter,conflict_handler='resolve')
  parser.add_argument('--format', default='adjlist')
  parser.add_argument('--input', nargs='?', required=True)
  parser.add_argument('--output', required=True)
  parser.add_argument("-l", "--log", dest="log", default="INFO")
  parser.add_argument('--dic-network-name', default='network')
  parser.add_argument('--number-walks', default=10, type=int)
  parser.add_argument('--walk-length', default=40, type=int)
  parser.add_argument('--representation-size', default=64, type=int, help='Number of latent dimensions to learn for each node.')
  parser.add_argument('--model', default='Word2Vec')

  args = parser.parse_args()


  if args.format == "adjlist":
    G = graph.load_adjacencylist(args.input)
  elif args.format == "edgelist":
    G = graph.load_edgelist(args.input)
  elif args.format == "mat":
    G = graph.load_matfile(args.input, variable_name=args.dic_network_name)
  else:
    raise Exception("Unknown file format: '%s'.  Valid formats: 'adjlist', 'edgelist', 'mat'" % args.format)


  ## Info about the walks
  print("Number of nodes: {}".format(len(G.nodes())))

  # We have number_walks walks starting from each node
  total_walks = len(G.nodes()) * args.number_walks

  print("Total number of walks: {}".format(total_walks))

  data_size = total_walks * args.walk_length

  print("Data size (walks*length): {}".format(data_size))

  ## Create the random walks and store them in walks list
  print("Walking...")
  walks = graph.build_deepwalk_corpus(G, num_paths=args.number_walks, path_length=args.walk_length, alpha=0)

  ## Apply model to each walk = sentence
  # https://www.quora.com/Can-some-one-help-explain-DeepWalk-Online-Learning-of-Social-Representations-in-laymans-terms-and-provide-a-real-world-example-with-a-social-graph
  print("Training...")


  if args.model == 'Skipgram' :
    vertex_counts = count_words(walks) # dictionary of the times each vertex appear in walks
    model = skipgram.Skipgram(sentences=walks, vocabulary_counts=vertex_counts,size=args.representation_size,window=5, min_count=0, trim_rule=None, workers=1)
  if args.model == 'Word2Vec':
    model = Word2Vec(walks, size=args.representation_size, window=5, min_count=0, sg=1, hs=1, workers=1)
  else:
    raise Exception("Unknown model: '%s'.  Valid models: 'Word2Vec', 'Skipgram'" % args.model)

  model.wv.save_word2vec_format(args.output)


#-----------------------------------------------------------------------------------------------#
#                                                                                               #
#   SKIPGRAM MODEL                                                                              #
#   A subclass to allow more customization of the Word2Vec internals                            #
#                                                                                               #
#-----------------------------------------------------------------------------------------------# 
class Skipgram(Word2Vec):

    def __init__(self, vocabulary_counts=None, **kwargs):

        self.vocabulary_counts = None

        kwargs["min_count"] = kwargs.get("min_count", 0)
        kwargs["workers"] = kwargs.get("workers", cpu_count())
        kwargs["size"] = kwargs.get("size", 128)
        kwargs["sentences"] = kwargs.get("sentences", None)
        kwargs["window"] = kwargs.get("window", 10)
        kwargs["sg"] = 1
        kwargs["hs"] = 1

        if vocabulary_counts != None:
          self.vocabulary_counts = vocabulary_counts

        super(Skipgram, self).__init__(**kwargs)


## Helper function for using Skipgram. Returns dictionary of the times each vertex appear in walks
def count_words(walks):
  c = Counter()
  for words in walks:
    c.update(words)
  return c


#-----------------------------------------------------------------------------------------------#
#                                                                                               #
#   Start                                                                                       #
#                                                                                               #
#-----------------------------------------------------------------------------------------------# 
if __name__ == "__main__":
  main()