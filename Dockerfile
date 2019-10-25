FROM python:3.6

RUN apt-get update
RUN apt-get install unzip

# for caching, install pip packages first
ADD requirements.txt /app/
WORKDIR /app
RUN pip install -r requirements.txt

ADD lemmatize.py /app
WORKDIR /app

COPY tigercorpus-2.2.conll09.tar.gz /app/tigercorpus-2.2.conll09.tar.gz
#RUN wget http://www.ims.uni-stuttgart.de/forschung/ressourcen/korpora/TIGERCorpus/download/tigercorpus-2.2.conll09.tar.gz
RUN tar -xvzf tigercorpus-2.2.conll09.tar.gz && rm tigercorpus-2.2.conll09.tar.gz

COPY germalemma-a44431635dcc541620587605aac64f05e1b5f4f6.zip /app/a44431635dcc541620587605aac64f05e1b5f4f6.zip
#RUN wget https://github.com/WZBSocialScienceCenter/germalemma/archive/a44431635dcc541620587605aac64f05e1b5f4f6.zip
RUN unzip a44431635dcc541620587605aac64f05e1b5f4f6.zip && rm a44431635dcc541620587605aac64f05e1b5f4f6.zip && mv germalemma-a44431635dcc541620587605aac64f05e1b5f4f6/* .

COPY IWNLP.Lemmatizer_20181001.zip /app/IWNLP.Lemmatizer_20181001.zip
#RUN wget http://lager.cs.uni-duesseldorf.de/NLP/IWNLP/IWNLP.Lemmatizer_20181001.zip
RUN unzip IWNLP.Lemmatizer_20181001.zip && rm IWNLP.Lemmatizer_20181001.zip

# local fallback, but it doesn't work completely
#ADD de_core_news_sm-2.1.0.tar.gz/ /app
#RUN python -m spacy link de_core_news_sm-2.1.0 de
RUN python -m spacy download de_core_news_sm
RUN python -m spacy link de_core_news_sm de

RUN python germalemma.py tiger_release_aug07.corrected.16012013.conll09 && rm tiger_release_aug07.corrected.16012013.conll09

#ENTRYPOINT ["python", "lemmatize.py"]
CMD ["python", "lemmatize.py"]
