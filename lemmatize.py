import sys
from itertools import zip_longest
from pathlib import Path
from http.server import *
from socketserver import *
from subprocess import *
import urllib.parse
import json

import spacy
from germalemma import GermaLemma
from spacy_iwnlp import spaCyIWNLP

# setup IWNLP
nlp = spacy.load("de", disable=["parser", "ner"])
iwnlp = spaCyIWNLP(lemmatizer_path="IWNLP.Lemmatizer_20181001.json")
nlp.add_pipe(iwnlp)

# setup GermaLemma
lemmatizer = GermaLemma()


def escape_text(text):
    return text.replace("\n", "\\n")


def unescape_text(text):
    return text.replace("\\n", "\n")


def replace_with_lemma(token_text, iwnlp_lemmas, pos):
    # iwnlp_lemmas is list, this is single string
    other_canditate = None

    if pos == "NOUN":
        other_canditate = lemmatizer.find_lemma(token_text, "N")

    if pos == "VERB" or pos == "AUX":
        other_canditate = lemmatizer.find_lemma(token_text, "V")

    if pos == "ADJ":
        other_canditate = lemmatizer.find_lemma(token_text, "ADJ")

    if pos == "ADV":
        other_canditate = lemmatizer.find_lemma(token_text, "ADV")

    if iwnlp_lemmas is None:
        if other_canditate is None:
            # default return text
            return token_text
        else:
            # if there are no  iwnlp_lemmas from IWNLP, we take the one from Germ Lemma
            return other_canditate
    else:
        if other_canditate != token_text and other_canditate in iwnlp_lemmas:
            return other_canditate  # both found the same
        else:
            return iwnlp_lemmas[0]  # always first to be reproducible


def process_token(token_text, iwnlp_lemmas, pos, ws):
    # process and make some that some information about the case remains
    prc_tkn = replace_with_lemma(token_text, iwnlp_lemmas, pos)
    res_word = ""
    for x, y in zip_longest(list(prc_tkn), list(token_text), fillvalue=""):
        # keep orginal case if the characters are the same
        if x.lower() == y.lower():
            res_word += y
        else:
            res_word += x

    # remain upper case
    if token_text.isupper() and not res_word.isupper():
        res_word = res_word.upper()

    # remain title case
    if token_text.istitle() and not res_word.istitle():
        res_word = res_word.title()

    # prepend original whitespace
    return res_word + ws


def _lemma(doc, remove_stop):
    if remove_stop:
        lemmatized = [
            process_token(
                str(token), token._.iwnlp_lemmas, token.pos_, token.whitespace_
            )
            for token in doc
            if not token.is_stop
        ]
    else:
        # print("got doc: " + str(doc))

        lemmatized = [
            process_token(
                str(token), token._.iwnlp_lemmas, token.pos_, token.whitespace_
            )
            for token in doc
        ]
    return "".join(lemmatized)

def _addLemmaToTokens(doc, remove_stop):
    lemmatizedtokens = []
    for token in doc:
        if not remove_stop or not token.is_stop:
            tok = str(token)
            lemma = process_token(
                        str(token), token._.iwnlp_lemmas, token.pos_, token.whitespace_
                    )
#            token.text = tok-2.1.0
#            token.lemma = lemma
            lemmatizedtokens.append({"text": tok, "lemma": lemma})
    return lemmatizedtokens

def lemma(text, remove_stop):
    doc = nlp(text)
#    return _lemma(doc, remove_stop)
#    lemmatised = _addLemmaToTokens(doc, remove_stop)
    lemmatised = _addLemmaToTokens(doc, False)
    jsonstr = json.dumps(doc.to_json())

    print("doc as json: " + jsonstr)
    jsonised = json.loads(jsonstr)

    print("length of lemmatised: " + str(len(lemmatised)))
    print("length of jsonised: " + str(len(jsonised)))

    # now merge lemmatised into doc
    i = 0
    for token in doc:
        if True: #not remove_stop or not token.is_stop:
            jsonised["tokens"][i]["text"] = lemmatised[i]["text"]
            jsonised["tokens"][i]["lemma"] = lemmatised[i]["lemma"]
            i += 1

    return json.dumps(jsonised)


def process_file(path, per_line, escape, remove_stop):
    if per_line:
        with open(Path("/output/" + path.name), "w") as outfile:
            with open(path) as infile:
                # process docs with spacy.pipe for performance reasons
                lines = []
                for text in infile:
                    if escape:
                        text = text.strip()
                        text = unescape_text(text)
                    lines.append(text)
                docs = nlp.pipe(lines)
                results = []
                for d in docs:
                    results.append(_lemma(d, remove_stop))

                if escape:
                    results = [escape_text(txt) for txt in results]
                    results = "\n".join(results)
                else:
                    # no need to add newlines because there are still part of the spacy whitespace
                    results = "".join(results)
                outfile.write(results)

    else:
        text = path.read_text()
        Path("/output/" + path.name).write_text(lemma(text, remove_stop))

### server provision

PORT = 8082

class myHandler(BaseHTTPRequestHandler):

	#Handler for the GET requests
	def do_GET(self):
		# split the path
		segments = self.path.split("/");
		print(str(segments));

		output = ""

		# we will support the following calls:
		# /api/nlp/lemmatise/{POS}/{WORD}
		# /api/nlp/analye/{WORD_SEQUENCE}
		if len(segments) > 4:
		    if segments[3] == "lemmatise":
		        pos = segments[4]
		        token_text = segments[5]
		        output = json.dumps({"lemma": lemmatizer.find_lemma(token_text, pos)})
		    else:
		        input = urllib.parse.unquote(segments[4])
		        print("got input " + input)
		        output = lemma(input, remove_stop="--remove_stop" in sys.argv)

		self.send_response(200)
		self.send_header('Content-type','text/plain')
		self.end_headers()
		# Send the html message
		self.wfile.write(str.encode(output))
		return

def start_server():
    httpd = TCPServer(("", PORT), myHandler)
    print ("serving at port " + str(PORT))
    httpd.serve_forever()


# # https://stackoverflow.com/questions/46245844/pass-arguments-to-python-argparse-within-docker-container
if __name__ == "__main__":

    if len(sys.argv) > 1 and "--line" not in sys.argv:
        results = lemma(sys.argv[1], remove_stop="--remove_stop" in sys.argv)
        print(results)

    else:
        input_path = Path("/input")
        if input_path.exists() and input_path.is_dir():
            print("Saving lemmatized text to the output folder...")
            files = list(input_path.glob("**/*.txt"))

            for f in files:
                process_file(
                    f,
                    per_line="--line" in sys.argv,
                    escape="--escape" in sys.argv,
                    remove_stop="--remove_stop" in sys.argv,
                )

        else:
            start_server()

