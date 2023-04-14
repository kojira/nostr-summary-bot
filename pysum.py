from pysummarization.nlpbase.auto_abstractor import AutoAbstractor
from pysummarization.tokenizabledoc.mecab_tokenizer import MeCabTokenizer
from pysummarization.abstractabledoc.top_n_rank_abstractor import TopNRankAbstractor


def summarize(text):
  # Object of automatic summarization.
  auto_abstractor = AutoAbstractor()
  # Set tokenizer for Japanese.
  auto_abstractor.tokenizable_doc = MeCabTokenizer()
  # Set delimiter for making a list of sentence.
  auto_abstractor.delimiter_list = [".", "。", "\n"]
  # Object of abstracting and filtering document.
  abstractable_doc = TopNRankAbstractor()
  # Summarize document.

  result_dict = auto_abstractor.summarize(text, abstractable_doc)
  result_text = ""
  for sentence in result_dict["summarize_result"]:
    result_text += sentence
  print(result_text)
  print("--------------------------------")
  return result_text
