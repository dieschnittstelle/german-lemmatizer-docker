# source for tiger corpus: https://www.ims.uni-stuttgart.de/forschung/ressourcen-manuell-zu-bearbeiten/korpora/TIGERCorpus/download/start.html

# build
docker build -t dieschnittstelle/german_lemmatiser .

# stop&remove existing containers
docker stop flfddr_german_lemmatiser
docker rm flfddr_german_lemmatiser

# run
docker run -itd -p 7090:8082 --name flfddr_german_lemmatiser dieschnittstelle/german_lemmatiser


