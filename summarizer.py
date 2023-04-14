import time
from datetime import date, datetime, timedelta

from pynostr.filters import FiltersList, Filters
from pynostr.event import Event, EventKind
from pynostr.relay_manager import RelayManager
from pynostr.key import PrivateKey
import yaml
import gpt
from dotenv import load_dotenv
import os
import db
import re
import pysum
from tqdm import tqdm

from langdetect import detect

dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path)

BOT_SECRETKEY_JJ = os.environ.get("BOT_SECRETKEY_JJ")
BOT_SECRETKEY_JE = os.environ.get("BOT_SECRETKEY_JE")
BOT_SECRETKEY_EE = os.environ.get("BOT_SECRETKEY_EE")
BOT_SECRETKEY_EJ = os.environ.get("BOT_SECRETKEY_EJ")


with open("./config.yml", "r") as yml:
  config = yaml.safe_load(yml)


def connect_relay():
  relay_manager = RelayManager()
  add_all_relay(relay_manager, config["relay_servers"])
  today = datetime.now()
  since = today.timestamp()

  filters = FiltersList([
      Filters(kinds=[EventKind.TEXT_NOTE], since=since, limit=1),
  ])

  relay_manager.add_subscription_on_all_relays("summarizer-bot", filters)
  relay_manager.run_sync()

  return relay_manager


def add_all_relay(relay_manager, relay_servers):
  for relay_server in relay_servers:
    relay_manager.add_relay(relay_server)


def close_relay(relay_manager):
  relay_manager.close_all_relay_connections()


def reconnect_all_relay(relay_manager):
  print("reconnect_all_relay start")
  close_relay(relay_manager)
  time.sleep(2)
  relay_manager = connect_relay()
  time.sleep(2)
  print("reconnect_all_relay done")
  return relay_manager


def post(relay_manager, secretkey, text):
  byte_array = bytes.fromhex(secretkey)
  privateKey = PrivateKey(byte_array)
  event = Event(content=text)
  event.sign(privateKey.hex())
  relay_manager.publish_event(event)
  relay_manager.run_sync()


def get_events(_from, _to, target_lang):
  results = []
  events = db.getEvents(_from, _to, 1)
  all_contents = []
  hashtag_reg = r"#\w+"
  for event in events:
    hashtags = re.findall(hashtag_reg, event.content)
    if len(hashtags) >= 3:
      continue
    if "lnbc" in event.content \
            or "#まとめ除外" in event.content\
            or "日本語の投稿の要約を開始しますわ。" in event.content\
            or "英語投稿の要約ですわ。" in event.content\
            or "Cowdle" in event.content\
            or "Chatgpt的Promp" in event.content\
            or "Bitcoin price" in event.content\
            or "[BUY]" in event.content\
            or "[ LOTTERY ]" in event.content\
            or "Rolling 🎲🎲" in event.content\
            or "latest block found" in event.content\
            or "New OP_RETURN" in event.content\
            or "https://www.thinkingchain.app" in event.content\
            or "Spread the love by Zapping" in event.content\
            or "new block was found" in event.content\
            or "Next difficulty adjustment" in event.content\
            or "Robosats Orderbook" in event.content\
            or "Protect your nostr feed with paid relays" in event.content\
            or "guesses from all players." in event.content\
            or "#IntuitiveGame" in event.content\
            or "lightning-cli decode" in event.content\
            or "ULTIMUSPOOL" in event.content\
            or "LN Capacity" in event.content\
            or "#exceptsummary" in event.content\
            or "#時報" in event.content\
            or "5c10ed0678805156d39ef1ef6d46110fe1e7e590ae04986ccf48ba1299cb53e2" == event.pubkey\
            or "ad49832d5a2a8cf1d168278f62210ba17ae7619da708b1bc11d03a11b51906a4" == event.pubkey\
            or "139b1ed03764c10e796b902d36b55d182016f963fadd4548c998c21872f66b28" == event.pubkey\
            or "8ed237334555289b3f412a88f391b1a33e90f01a335fc31c410b4a2bcaa04c30" == event.pubkey\
            or "mostr" in event.tags:
      continue
    try:
      lang = detect(event.content)
    except:
      lang = ""

    if lang == target_lang:
      if event.content not in all_contents:
        results.append(event)
        all_contents.append(event.content)

  return results


def split_text(text, max_length=1000):
  import re
  # 「。\n」で分割する
  sentences = re.findall('[^。\n]*[。\n]', text)

  result = []
  current = ''
  for sentence in sentences:
    if len(current + sentence) > max_length:
      result.append(current.strip())
      current = ''
    current += sentence
  if current:
    result.append(current.strip())
  return result


def get_timeline(_from, _to, target_lang):
  events = get_events(_from, _to, target_lang)
  contents = "\n".join([event.content.replace("\n", " ") for event in events])
  contents = re.sub(r"#\[[0-9]+\]", "", contents)
  return contents


def get_pre_summary(text):
  pre_summary_all = ""
  contents_list = split_text(text, max_length=8000)
  for content in contents_list:
    pre_summary = pysum.summarize(content)
    print(pre_summary)
    print(len(pre_summary))
    pre_summary_all += f"{pre_summary}\n"

  return pre_summary_all


def get_summary(prompt, text):
  contents = split_text(text, max_length=3000)
  summary_all = ""
  for content in contents:
    summary = gpt.get_summary(prompt, content)
    summary_all += f"{summary}\n"

  summary_all = re.sub(r"\\$", "", summary_all)


def summarize_english(_from, _to):
  prompt_summarize_en = "You are a talented young journalist. Please read the following article, summarize it in English in 10 lines in a tone befitting a young lady. Begin each line with '・' and end each line with a newline character."
  timeline = get_timeline(_from, _to, "en")
  pre_summary = get_pre_summary(timeline)
  loop = True
  while loop:
    contents = split_text(pre_summary, max_length=4000)
    pre_summary = ""
    for content in tqdm(contents):
      summary = gpt.get_answer(prompt_summarize_en, content)
      print(summary)
      pre_summary += f"{summary}\n"
    if len(pre_summary) < 1400:
      break

  contents = split_text(pre_summary, max_length=4000)
  summarized_all = ""

  for content in tqdm(contents):
    summarized = gpt.get_answer(prompt_summarize_en, content)
    print(summarized)
    summarized_all += f"{summarized}\n"

  print(summarized_all)
  print("----------------------------------------")
  summarized_all = re.sub(r"\\$", "", summarized_all)

  return summarized_all, timeline.count("\n")


def summarize_japanese(_from, _to):
  # prompt_summarize_ja = "Please read the following article, summarize it in 日本語のまま in 20 lines in a tone befitting a young lady. Begin each line with '・' and end each line with a newline character."
  # prompt_summarize_ja = "次の文章を読んで要約し、日本語で20行にまとめてください。Begin each line with '・' and end each line with a newline character."
  prompt_summarize_ja = "あなたは優秀な新聞記者のお嬢様です。次の文章を読んで要約し、お嬢様のような口調で日本語で20行にまとめてください。行頭には必ず'・'を入れて行末には必ず改行を入れてください。"
  timeline = get_timeline(_from, _to, "ja")
  pre_summary = get_pre_summary(timeline)
  loop = True
  while loop:
    contents = split_text(pre_summary, max_length=4000)
    pre_summary = ""
    for content in tqdm(contents):
      summary = gpt.get_answer(prompt_summarize_ja, content)
      print(summary)
      pre_summary += f"{summary}\n"
    if len(pre_summary) < 1400:
      break

  contents = split_text(pre_summary, max_length=4000)
  summarized_all = ""

  for content in tqdm(contents):
    summarized = gpt.get_answer(prompt_summarize_ja, content)
    print(summarized)
    summarized_all += f"{summarized}\n"

  print(summarized_all)
  print("----------------------------------------")
  summarized_all = re.sub(r"\\$", "", summarized_all)

  return summarized_all, timeline.count("\n")


def translate_to_ja(text):
  prompt_translate_ja = "You are an excellent translator. Please translate the following English into Japanese."
  translated = gpt.get_answer(prompt_translate_ja, text)
  return translated


def translate_to_en(text):
  prompt_translate_en = "You are an excellent translator. Please translate the following Japanese into English."
  translated = gpt.get_answer(prompt_translate_en, text)
  return translated


def main():

  while True:
    now = datetime.utcnow()
    from_date = now - timedelta(hours=1)
    _from = from_date.replace(minute=0, second=0, microsecond=0)
    _to = now.replace(minute=0, second=0, microsecond=0)
    relay_manager = connect_relay()

    summarized_ja, count_ja = summarize_japanese(_from, _to)
    from_text_ja = (_from + timedelta(hours=9)).strftime("%Y-%m-%d %H:%M:%S")
    to_text_ja = (_to + timedelta(hours=9)).strftime("%Y-%m-%d %H:%M:%S")
    text = f"{from_text_ja}〜{to_text_ja}の日本語投稿{count_ja}件の要約ですわ。\n{summarized_ja}\n\n#summary4ja #exceptsummary"
    # print(text)
    # exit()
    post(relay_manager, BOT_SECRETKEY_JJ, text)

    summarized_ja_to_en = translate_to_en(summarized_ja)

    from_text_utc = _from.strftime("%Y-%m-%d %H:%M:%S")
    to_text_utc = _to.strftime("%Y-%m-%d %H:%M:%S")

    text = f"This is an English translation of the {count_ja} summaries of the Japanese timelines from {from_text_utc} to {to_text_utc} UTC.\n{summarized_ja_to_en}\n\n#summary4ja2en #exceptsummary"
    post(relay_manager, BOT_SECRETKEY_JE, text)

    summarized_en, count_en = summarize_english(_from, _to)
    text = f"This is a summary of {count_en} English timelines from {from_text_utc} to {to_text_utc} UTC.\n{summarized_en}\n\n#summary4en #exceptsummary"
    post(relay_manager, BOT_SECRETKEY_EE, text)

    summarized_en_to_ja = translate_to_ja(summarized_en)
    text = f"{from_text_ja}〜{to_text_ja}の英語タイムライン{count_en}件の要約ですわ。\n{summarized_en_to_ja}\n\n#summary4en2ja #exceptsummary"
    post(relay_manager, BOT_SECRETKEY_EJ, text)
    time.sleep(20)
    relay_manager.close_all_relay_connections()
    while True:
      now = datetime.now()
      print(now.minute)
      if now.minute == 0:
        break
      time.sleep(30)


if __name__ == "__main__":
  main()
